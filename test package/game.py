import pygame
import pytmx
import pyscroll
import pytmx.util_pygame
import random
import os
import time
from collections import defaultdict
from functools import lru_cache
from player import Player
from enemy import Enemy
from game_over import show_game_over
from victory_screen import show_victory_screen
from enum import Enum

class ResourceManager:
    _instance = None
    _sprites = {}
    _sounds = {}
    
    @classmethod
    @lru_cache(maxsize=32)
    def get_sprite(cls, name):
        """Load and cache sprite images with LRU caching for improved performance"""
        if name not in cls._sprites:
            try:
                cls._sprites[name] = pygame.image.load(f"{name}.png").convert_alpha()
            except pygame.error:
                print(f"Warning: Could not load {name}.png, using placeholder")
                # Create a placeholder sprite
                surface = pygame.Surface((32, 32), pygame.SRCALPHA)
                surface.fill((255, 0, 255, 128))  # Purple semi-transparent
                pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 1)
                cls._sprites[name] = surface
        return cls._sprites[name]
    
    @classmethod
    @lru_cache(maxsize=16)
    def get_sound(cls, name):
        """Load and cache sound effects"""
        if name not in cls._sounds:
            try:
                cls._sounds[name] = pygame.mixer.Sound(f"{name}.wav")
            except pygame.error:
                print(f"Warning: Could not load {name}.wav")
                cls._sounds[name] = None
        return cls._sounds[name]

class UI:
    def __init__(self):
        self._cached_fonts = {}
        self._cached_surfaces = {}
        self._text_surfaces = {}
    
    @lru_cache(maxsize=8)
    def get_font(self, size):
        """Get or create a font of specified size with caching"""
        if size not in self._cached_fonts:
            self._cached_fonts[size] = pygame.font.Font(None, size)
        return self._cached_fonts[size]
    
    def get_text_surface(self, text, size, color):
        """Get or create a text surface with caching for frequently used text"""
        key = (text, size, color)
        if key not in self._text_surfaces:
            font = self.get_font(size)
            self._text_surfaces[key] = font.render(text, True, color)
        return self._text_surfaces[key]

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    VICTORY = 5

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("RPG Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = "playing"  # Change from GameState.PLAYING to string for now
        
        # Initialisation des statistiques
        self.stats = {
            "level": 1,
            "exp": 0,
            "exp_to_level": 100,
            "health": 100,
            "max_health": 100,
            "attack": 10,
            "defense": 5,
            "enemies_defeated": 0  # Initialisation du compteur d'ennemis vaincus
        }
        
        # Load map
        self.using_placeholder_map = False
        try:
            # Try to load the map from the root directory first
            map_path = 'carte.tmx'
            if not os.path.exists(map_path):
                # If not found in root, try assets folder
                map_path = os.path.join('assets', 'carte.tmx')
                if not os.path.exists(map_path):
                    raise FileNotFoundError("carte.tmx not found in root or assets directory")
            
            print(f"Loading map from: {os.path.abspath(map_path)}")
            self.tmx_data = pytmx.util_pygame.load_pygame(map_path)
            
            # Set default properties if they don't exist
            if not hasattr(self.tmx_data, 'tilewidth'):
                self.tmx_data.tilewidth = 32
            if not hasattr(self.tmx_data, 'tileheight'):
                self.tmx_data.tileheight = 32
            if not hasattr(self.tmx_data, 'width'):
                self.tmx_data.width = 50
            if not hasattr(self.tmx_data, 'height'):
                self.tmx_data.height = 50
            
            # Ensure the map has the required layers
            if not hasattr(self.tmx_data, 'layers') or not self.tmx_data.layers:
                raise ValueError("Map has no layers")
                
            print(f"Successfully loaded map with {len(self.tmx_data.layers)} layers")
                
        except Exception as e:
            print(f"Error loading map: {str(e)}")
            print("Using placeholder map instead")
            self.using_placeholder_map = True
            self.tmx_data = self.create_placeholder_map()
        
        # Create a proper map data object
        class SimpleLayer:
            def __init__(self, data, name):
                self.data = data
                self.name = name
                self.visible = True
        
        if self.using_placeholder_map and not hasattr(self.tmx_data, 'layers'):
            # For placeholder, create a simple map layer
            background_layer = SimpleLayer(
                self.tmx_data.layers[0].data if hasattr(self.tmx_data, 'layers') else [0] * (50*50),
                'background'
            )
            collision_layer = SimpleLayer(
                self.tmx_data.layers[1].data if hasattr(self.tmx_data, 'layers') else [1] * (50*50),
                'collision'
            )
            
            self.tmx_data.layers = [background_layer, collision_layer]
            
            # Create a simple tileset if it doesn't exist
            if not hasattr(self.tmx_data, 'tilesets') or not self.tmx_data.tilesets:
                class SimpleTileset:
                    def __init__(self):
                        self.firstgid = 1
                        self.tilewidth = 32
                        self.tileheight = 32
                        self.margin = 0
                        self.spacing = 0
                        self.image = None
                
                self.tmx_data.tilesets = [SimpleTileset()]
        
        # Create map data and layer
        try:
            map_data = pyscroll.data.TiledMapData(self.tmx_data)
            map_layer = pyscroll.orthographic.BufferedRenderer(
                map_data, 
                self.screen.get_size(),
                alpha=True
            )
            map_layer.zoom = 2
            
            # Create sprite group with map layer
            self.all_sprites = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=2)
        except Exception as e:
            print(f"Warning: Could not create map renderer ({str(e)}), using simple background")
            # Fallback to simple background
            self.background = pygame.Surface(self.screen.get_size())
            self.background.fill((50, 120, 80))  # Dark green background
            self.all_sprites = pygame.sprite.LayeredUpdates()
        
        # Initialize game stats
        self.stats = {
            "level": 1,
            "exp": 0,
            "exp_to_level": 100,
            "health": 100,
            "max_health": 100,
            "attack": 10,
            "defense": 5,
            "enemies_defeated": 0
        }
    
        # Player setup - spawn at top-left corner with some offset
        spawn_x = 100  # 100 pixels from left
        spawn_y = 100  # 100 pixels from top
        self.player = Player(spawn_x, spawn_y)
        self.player_group = pygame.sprite.Group(self.player)
        
        # Add player to sprite group
        if hasattr(self, 'all_sprites'):
            try:
                self.all_sprites.add(self.player, layer=3)
            except:
                self.all_sprites.add(self.player)
        
        # Enemy group
        self.enemies = pygame.sprite.Group()
        
        # Load UI elements
        self.load_ui()
        
        # Game objects setup
        self.setup_collisions(self.tmx_data)
        self.spawn_enemies(5)  # Spawn 5 enemies
        
        # Game state
        self.game_over = False
        self.victory = False
        self.last_attack_time = 0
        self.attack_cooldown = 500  # milliseconds
        
        # Camera/viewport
        self.camera_x = 0
        self.camera_y = 0
        self.camera_width = self.screen.get_width()
        self.camera_height = self.screen.get_height()

    def load_ui(self):
        """Load UI elements like health bar"""
        try:
            self.health_ui = pygame.image.load('assets/HealthUI.png').convert_alpha()
            self.health_ui = pygame.transform.scale(self.health_ui, 
                                                 (self.health_ui.get_width() * 2, 
                                                  self.health_ui.get_height() * 2))
        except:
            print("Warning: Could not load health UI, using placeholder")
            self.health_ui = None
            
    def setup_collisions(self, tmx_data):
        """Setup collision rectangles from map data"""
        self.blocked_rects = []

        # Get collision rectangles from object layer if it exists
        try:
            for layer in self.tmx_data.layers:
                if hasattr(layer, 'name') and 'collision' in layer.name.lower():
                    # Debug print pour vérifier le type de la couche
                    print(f"Processing collision layer: {layer.name}, type: {type(layer)}")
                    
                    # Vérifier si la couche est un groupe d'objets (TiledObjectGroup)
                    if hasattr(layer, 'objects'):
                        objects = layer.objects
                    else:
                        # Si c'est une simple liste d'objets
                        objects = layer if isinstance(layer, list) else []
                        
                    # Traiter chaque objet dans la couche
                    objects_processed = 0
                    for obj in objects:
                        # Vérifier si l'objet a les attributs nécessaires
                        if hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'width') and hasattr(obj, 'height'):
                            rect = pygame.Rect(
                                obj.x, obj.y,
                                obj.width, obj.height
                            )
                            self.blocked_rects.append(rect)
                            objects_processed += 1
                        # Alternative: si l'objet est un tuple avec 4 valeurs (x, y, width, height)
                        elif isinstance(obj, tuple) and len(obj) >= 4:
                            rect = pygame.Rect(obj[0], obj[1], obj[2], obj[3])
                            self.blocked_rects.append(rect)
                            objects_processed += 1
                            
                    print(f"Loaded {objects_processed} collision objects from {layer.name}")
            
            # If no collision objects found, use tiles with specific properties or gid
            if not self.blocked_rects:
                collision_tiles = []
                for layer in tmx_data.layers:
                    if hasattr(layer, 'data'):
                        for x, y, gid in layer.iter_data():
                            # Check if this tile has collision property or is a wall tile
                            properties = tmx_data.get_tile_properties_by_gid(gid) if hasattr(tmx_data, 'get_tile_properties_by_gid') else None
                            
                            is_collision = False
                            if properties and 'collision' in properties and properties['collision']:
                                is_collision = True
                            elif gid > 1 and layer.name.lower() in ['walls', 'collision', 'obstacles']:
                                is_collision = True
                                
                            if is_collision:
                                rect = pygame.Rect(
                                    x * tmx_data.tilewidth,
                                    y * tmx_data.tileheight,
                                    tmx_data.tilewidth,
                                    tmx_data.tileheight
                                )
                                collision_tiles.append(rect)
                                
                self.blocked_rects.extend(collision_tiles)
                if collision_tiles:
                    print(f"Generated {len(collision_tiles)} collision rectangles from tiles")
                
            # For placeholder map, add walls around the edges
            if self.using_placeholder_map:
                wall_thickness = 32
                map_width = tmx_data.width * tmx_data.tilewidth
                map_height = tmx_data.height * tmx_data.tileheight
                
                # Walls around the edges of the map
                self.blocked_rects.extend([
                    pygame.Rect(0, 0, map_width, wall_thickness),  # Top wall
                    pygame.Rect(0, 0, wall_thickness, map_height),  # Left wall
                    pygame.Rect(0, map_height - wall_thickness, map_width, wall_thickness),  # Bottom wall
                    pygame.Rect(map_width - wall_thickness, 0, wall_thickness, map_height)  # Right wall
                ])
                
                print(f"Added placeholder walls around map edges")
        
        except Exception as e:
            print(f"Error setting up collisions: {e}")
            # Ensure we at least have a minimal set of collision blocks
            if not self.blocked_rects:
                self.blocked_rects = [
                    pygame.Rect(0, 0, 800, 32),  # Top
                    pygame.Rect(0, 0, 32, 600),  # Left
                    pygame.Rect(0, 568, 800, 32),  # Bottom
                    pygame.Rect(768, 0, 32, 600)   # Right
                ]
                print("Using fallback collision boundaries")
                
        # Make sure we have at least some collision rects
        if not self.blocked_rects:
            print("WARNING: No collision rects were found, creating basic boundaries")
            self.blocked_rects = [
                pygame.Rect(0, 0, 800, 32),    # Top
                pygame.Rect(0, 0, 32, 600),    # Left
                pygame.Rect(0, 568, 800, 32),  # Bottom
                pygame.Rect(768, 0, 32, 600)   # Right
            ]

    def is_valid_spawn_position(self, x, y, width, height):
        """Check if a position is valid for spawning (not colliding with walls)"""
        spawn_rect = pygame.Rect(x, y, width, height)
        for wall in self.blocked_rects:
            if spawn_rect.colliderect(wall):
                return False
        return True

    def find_valid_spawn_position(self):
        """Find a valid spawn position that doesn't collide with walls"""
        max_attempts = 100
        margin = 50  # Keep away from edges
        
        for _ in range(max_attempts):
            x = random.randint(margin, (self.tmx_data.width * self.tmx_data.tilewidth) - margin)
            y = random.randint(margin, (self.tmx_data.height * self.tmx_data.tileheight) - margin)
            
            if self.is_valid_spawn_position(x, y, 32, 32):
                return x, y
                
        # Fallback to default position if no valid position found
        return 100, 100

    def spawn_enemies(self, count):
        """Spawn enemies in valid positions"""
        attempts = 0
        spawned = 0
        
        while spawned < count and attempts < 100:
            x, y = self.find_valid_spawn_position()
            if self.is_valid_spawn_position(x, y, 32, 32):
                enemy = Enemy(x, y)
                self.enemies.add(enemy)
                self.all_sprites.add(enemy, layer=3)
                spawned += 1
            attempts += 1
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.player_attack()
                elif event.key == pygame.K_r and (self.game_state == "game_over" or self.game_state == "victory"):
                    self.__init__()  # Restart game
    
    def update(self, dt):
        """Update game state"""
        # Update player
        self.player.update(dt)
        
        # Vérifier si le joueur est mort
        if self.player.current_hearts <= 0 and self.game_state == "playing":
            self.game_state = "game_over"
            return

        # Si le jeu est en cours, mettre à jour le reste du jeu
        if self.game_state == "playing":
            # Process player movement
            self.handle_player_movement(dt)
            
            # Update enemies with strict collision handling
            for enemy in self.enemies:
                # Gérer les minuteurs
                enemy._handle_timers(dt)
                
                # IA simple - détecter le joueur et le poursuivre
                enemy._handle_ai_behavior(self.player, dt)
                
                # Gérer le mouvement avec vérification stricte des collisions
                self.handle_enemy_movement(enemy, dt)
            
            # Vérifier les collisions entre entités
            self.handle_collisions()

    def handle_player_movement(self, dt):
        """Handle player movement and collisions with walls - amélioration stricte"""
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        
        # Déterminer la direction du mouvement basée sur les touches pressées
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:
            dx -= self.player.speed * dt / 16.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.player.speed * dt / 16.0
        if keys[pygame.K_UP] or keys[pygame.K_z]:
            dy -= self.player.speed * dt / 16.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.player.speed * dt / 16.0
            
        # Normaliser le mouvement diagonal pour éviter une vitesse plus rapide
        if dx != 0 and dy != 0:
            dx *= 0.7071  # Approximation de 1/√2
            dy *= 0.7071

        # S'assurer que les déplacements sont des nombres entiers pour une meilleure détection de collision
        dx_int = int(dx)
        dy_int = int(dy)
        
        # Si le mouvement est trop petit pour être un entier, accumuler jusqu'à ce qu'il soit suffisant
        if dx != 0 and dx_int == 0:
            self.player.dx_accumulator = getattr(self.player, 'dx_accumulator', 0) + dx
            if abs(self.player.dx_accumulator) >= 1:
                dx_int = int(self.player.dx_accumulator)
                self.player.dx_accumulator -= dx_int
                
        if dy != 0 and dy_int == 0:
            self.player.dy_accumulator = getattr(self.player, 'dy_accumulator', 0) + dy
            if abs(self.player.dy_accumulator) >= 1:
                dy_int = int(self.player.dy_accumulator)
                self.player.dy_accumulator -= dy_int

        # Créer un rectangle temporaire pour tester les collisions
        test_rect = self.player.rect.copy()
        
        # Méthode de collision améliorée - traiter les mouvements séparément
        # Test du mouvement horizontal
        if dx_int != 0:
            test_rect.x += dx_int
            x_collision = False
            for wall in self.blocked_rects:
                if test_rect.colliderect(wall):
                    x_collision = True
                    # Ajustement précis - déplacer jusqu'au bord du mur
                    if dx_int > 0:  # Mouvement vers la droite
                        self.player.rect.right = wall.left
                    else:  # Mouvement vers la gauche
                        self.player.rect.left = wall.right
                    break
                    
            if not x_collision and dx_int != 0:
                self.player.move(dx_int, 0)

        # Test du mouvement vertical
        test_rect = self.player.rect.copy()  # Recommencer avec la position actualisée
        if dy_int != 0:
            test_rect.y += dy_int
            y_collision = False
            for wall in self.blocked_rects:
                if test_rect.colliderect(wall):
                    y_collision = True
                    # Ajustement précis - déplacer jusqu'au bord du mur
                    if dy_int > 0:  # Mouvement vers le bas
                        self.player.rect.bottom = wall.top
                    else:  # Mouvement vers le haut
                        self.player.rect.top = wall.bottom
                    break
                    
            if not y_collision and dy_int != 0:
                self.player.move(0, dy_int)
                
        # Mettre à jour la direction du joueur même si bloqué par un mur
        # cela permet de tourner le personnage face au mur
        if dx != 0 or dy != 0:
            self.player.update_direction(dx, dy)
    
    def player_attack(self):
        """Handle player attacking"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time < self.attack_cooldown:
            return
        
        self.last_attack_time = current_time
        
        # Check for enemies in attack range
        for enemy in list(self.enemies):  # Create a copy of the list
            dx = enemy.rect.centerx - self.player.rect.centerx
            dy = enemy.rect.centery - self.player.rect.centery
            distance = (dx**2 + dy**2)**0.5
            
            if distance < 100:  # Attack range
                enemy.take_damage(self.stats["attack"])
                if enemy.health <= 0:
                    self.enemies.remove(enemy)
                    self.all_sprites.remove(enemy)
                    self.stats["exp"] += 10
                    
                    # Incrémenter le compteur d'ennemis tués
                    if "enemies_defeated" not in self.stats:
                        self.stats["enemies_defeated"] = 0
                    self.stats["enemies_defeated"] += 1
                    print(f"Ennemi vaincu ! Total: {self.stats['enemies_defeated']}")
                    
                    # Check for level up
                    if self.stats["exp"] >= self.stats["exp_to_level"]:
                        self.level_up()
                    
                    # Check for victory condition
                    if not self.enemies:
                        self.game_state = "victory"
    
    def level_up(self):
        """Handle player level up"""
        self.stats["level"] += 1
        self.stats["exp"] = 0
        self.stats["exp_to_level"] = int(self.stats["exp_to_level"] * 1.5)
        self.stats["max_health"] += 20
        self.stats["health"] = self.stats["max_health"]
        self.stats["attack"] += 5
        self.stats["defense"] += 2
        print(f"Level up! Niveau {self.stats['level']} atteint.")
    
    def draw_ui(self):
        """Draw UI elements"""
        # Draw hearts
        heart_spacing = 2
        heart_x = 20
        heart_y = 20
        
        for i in range(self.player.max_hearts):
            if i < self.player.current_hearts:
                # Draw full heart (index 0)
                self.screen.blit(self.player.hearts[0], 
                               (heart_x + (self.player.heart_width + heart_spacing) * i, heart_y))
            else:
                # Draw empty heart (index 6 instead of 7)
                self.screen.blit(self.player.hearts[6], 
                               (heart_x + (self.player.heart_width + heart_spacing) * i, heart_y))

        # Draw stats
        font = pygame.font.Font(None, 24)
        stats_text = f"Level: {self.stats['level']}  |  ATK: {self.stats['attack']}  |  DEF: {self.stats['defense']}  |  EXP: {self.stats['exp']}/{self.stats['exp_to_level']}"
        text_surface = font.render(stats_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (20, 50))
        
        # Draw controls help
        controls_text = "WASD: Move  |  SPACE: Attack  |  ESC: Quit"
        controls_surface = font.render(controls_text, True, (200, 200, 200))
        self.screen.blit(controls_surface, (20, self.screen.get_height() - 40))
    
    def draw_game_over(self):
        """Draw game over screen using the game_over module"""
        # Afficher les statistiques du joueur et nombre d'ennemis vaincus
        if "enemies_defeated" not in self.stats:
            self.stats["enemies_defeated"] = 0
        
        # Créer un overlay semi-transparent
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Noir avec 70% d'opacité
        self.screen.blit(overlay, (0, 0))
        
        # Afficher le titre GAME OVER en rouge
        title_font = pygame.font.Font(None, 72)
        title = title_font.render("GAME OVER", True, (255, 0, 0))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 80))
        self.screen.blit(title, title_rect)
        
        # Afficher les statistiques du joueur
        text_font = pygame.font.Font(None, 36)
        stats_text = f"Niveau: {self.stats['level']} | Ennemis vaincus: {self.stats['enemies_defeated']}"
        stats_surf = text_font.render(stats_text, True, (255, 255, 255))
        stats_rect = stats_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        self.screen.blit(stats_surf, stats_rect)
        
        # Afficher les options de restart et quit
        restart_text = text_font.render("Appuyez sur R pour recommencer", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 60))
        self.screen.blit(restart_text, restart_rect)
        
        quit_text = text_font.render("Appuyez sur Q pour quitter", True, (255, 255, 255))
        quit_rect = quit_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 110))
        self.screen.blit(quit_text, quit_rect)
    
    def draw_victory(self):
        """Draw victory screen"""
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("VICTORY!", True, (0, 255, 0))
        text_rect = text.get_rect(center=(400, 250))
        self.screen.blit(text, text_rect)
        
        font = pygame.font.Font(None, 36)
        stats_text = f"Level {self.stats['level']} | Enemies Defeated: {self.stats.get('enemies_defeated', 0)}"
        stats_surface = font.render(stats_text, True, (255, 255, 255))
        stats_rect = stats_surface.get_rect(center=(400, 320))
        self.screen.blit(stats_surface, stats_rect)
        
        restart_text = font.render("Press R to play again", True, (200, 200, 255))
        restart_rect = restart_text.get_rect(center=(400, 380))
        self.screen.blit(restart_text, restart_rect)
    
    def create_placeholder_map(self):
        """Create a simple placeholder map"""
        # Create a simple map with walls around the edges
        map_data = {
            'tilewidth': 32,
            'tileheight': 32,
            'width': 50,
            'height': 50,
            'layers': [
                {
                    'name': 'background',
                    'data': [0] * (50*50),  # Empty background (grass)
                    'opacity': 1,
                    'visible': True,
                    'properties': {}
                },
                {
                    'name': 'collision',
                    'data': [],
                    'opacity': 1,
                    'visible': False,
                    'properties': {}
                }
            ],
            'tilesets': [
                {
                    'firstgid': 1,
                    'tilewidth': 32,
                    'tileheight': 32,
                    'margin': 0,
                    'spacing': 0,
                    'properties': {}
                }
            ],
            'tile_properties': {},
            'tilelayers': [],
            'objectgroups': []
        }
        
        # Initialize collision layer with all zeros
        collision_layer = [0] * (50 * 50)
        
        # Add walls around the edges
        for x in range(50):
            # Top and bottom walls
            collision_layer[x] = 1
            collision_layer[x + (49 * 50)] = 1
            
        for y in range(1, 49):
            # Left and right walls
            collision_layer[y * 50] = 1
            collision_layer[y * 50 + 49] = 1
            
            # Add some random obstacles
            for x in range(1, 49):
                if random.random() < 0.02:  # 2% chance of an obstacle
                    collision_layer[y * 50 + x] = 1
        
        map_data['layers'][1]['data'] = collision_layer
        
        # Add some properties needed by pyscroll
        map_data['background_color'] = (100, 100, 100, 255)
        map_data['render_order'] = 'right-down'
        
        # Create a simple class to mimic tmx data structure
        class SimpleTMX:
            def __init__(self, data):
                self.__dict__.update(data)
                self.tilewidth = data['tilewidth']
                self.tileheight = data['tileheight']
                self.width = data['width']
                self.height = data['height']
                self.background_color = data.get('background_color', (0, 0, 0, 0))
                self.render_order = data.get('render_order', 'right-down')
                
                # Set up layers
                self.layers = []
                for layer in data['layers']:
                    layer_obj = type('Layer', (), layer)
                    layer_obj.data = layer['data']
                    self.layers.append(layer_obj)
                
                # Set up tilesets
                self.tilesets = data['tilesets']
                self.tile_properties = data.get('tile_properties', {})
                
                # Methods expected by pyscroll
                def get_layer_by_name(name):
                    for layer in self.layers:
                        if hasattr(layer, 'name') and layer.name == name:
                            return layer
                    return None
                    
                self.get_layer_by_name = get_layer_by_name
                
                def get_tile_image_by_gid(gid):
                    # Return a simple surface for the tile
                    tile = pygame.Surface((32, 32), pygame.SRCALPHA)
                    if gid == 0:  # Grass
                        tile.fill((100, 200, 100, 255))
                    else:  # Wall/collision
                        tile.fill((139, 69, 19, 255))
                    return tile
                    
                self.get_tile_image_by_gid = get_tile_image_by_gid
        
        return SimpleTMX(map_data)
    
    def handle_collisions(self):
        """Gérer les collisions entre entités (joueur et ennemis)"""
        # Utiliser le partitionnement spatial pour une détection de collision efficace
        self.spatial_hash = defaultdict(list)
        cell_size = 64  # Taille de la cellule pour le partitionnement
        
        # Construire le hachage spatial pour une détection de collision efficace
        for sprite in self.all_sprites:
            if not hasattr(sprite, 'rect') or not sprite.rect:
                continue
                
            # Déterminer les cellules de la grille que le sprite occupe
            min_x = sprite.rect.left // cell_size
            max_x = sprite.rect.right // cell_size
            min_y = sprite.rect.top // cell_size
            max_y = sprite.rect.bottom // cell_size
            
            # Ajouter le sprite à toutes les cellules qu'il chevauche
            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    self.spatial_hash[(x, y)].append(sprite)
    
    def get_nearby_sprites(self, sprite, distance=64):
        """Get sprites near a given sprite using spatial partitioning"""
        if not hasattr(sprite, 'rect') or not sprite.rect:
            return []
            
        cell_size = 64
        center_x = sprite.rect.centerx // cell_size
        center_y = sprite.rect.centery // cell_size
        nearby = set()
        
        # Check surrounding cells
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                cell_key = (center_x + dx, center_y + dy)
                if cell_key in self.spatial_hash:
                    nearby.update(self.spatial_hash[cell_key])
        
        return [s for s in nearby if s != sprite]
        
    def handle_enemy_movement(self, enemy, dt):
        """Gérer le mouvement des ennemis avec vérification stricte des collisions"""
        # S'assurer que les déplacements sont des nombres entiers
        dx_int = int(enemy.dx)
        dy_int = int(enemy.dy)
        
        # Accumuler les petits mouvements
        enemy.dx_accumulator = getattr(enemy, 'dx_accumulator', 0) + (enemy.dx - dx_int)
        enemy.dy_accumulator = getattr(enemy, 'dy_accumulator', 0) + (enemy.dy - dy_int)
        
        if abs(enemy.dx_accumulator) >= 1:
            dx_acc = int(enemy.dx_accumulator)
            dx_int += dx_acc
            enemy.dx_accumulator -= dx_acc
            
        if abs(enemy.dy_accumulator) >= 1:
            dy_acc = int(enemy.dy_accumulator)
            dy_int += dy_acc
            enemy.dy_accumulator -= dy_acc
        
        # Gestion des collisions en X
        if dx_int != 0:
            test_rect = enemy.rect.copy()
            test_rect.x += dx_int
            collision_x = False
            
            # Vérifier les collisions avec les murs
            for wall in self.blocked_rects:
                if test_rect.colliderect(wall):
                    collision_x = True
                    # Rebondir dans la direction opposée
                    enemy.dx = -enemy.dx * 0.8
                    break
                    
            if not collision_x:
                enemy.rect.x += dx_int
                enemy.float_x = float(enemy.rect.x)
        
        # Gestion des collisions en Y
        if dy_int != 0:
            test_rect = enemy.rect.copy()
            test_rect.y += dy_int
            collision_y = False
            
            # Vérifier les collisions avec les murs
            for wall in self.blocked_rects:
                if test_rect.colliderect(wall):
                    collision_y = True
                    # Rebondir dans la direction opposée
                    enemy.dy = -enemy.dy * 0.8
                    break
                    
            if not collision_y:
                enemy.rect.y += dy_int
                enemy.float_y = float(enemy.rect.y)
    
    def run(self):
        """Main game loop with optimized rendering"""
        last_time = pygame.time.get_ticks()
        frame_count = 0
        fps_update_time = last_time
        fps_display = "FPS: 0"
        fps_surface = None
        
        # Pre-create UI font for FPS display
        fps_font = pygame.font.Font(None, 24)
        
        while self.running:
            # Calculate delta time with millisecond precision
            current_time = pygame.time.get_ticks()
            dt = current_time - last_time
            last_time = current_time
            
            # Cap delta time to avoid physics issues on lag spikes
            dt = min(dt, 100)  # Maximum 100ms (prevents physics glitches on lag spikes)
            
            # Handle events
            self.handle_events()
            
            # Clear screen
            self.screen.fill((0, 0, 0))
            
            # Update game state
            self.update(dt)
            
            # Update camera position to follow player with smoothing
            target_x = self.player.rect.centerx - self.camera_width // 2
            target_y = self.player.rect.centery - self.camera_height // 2
            self.camera_x = int(target_x)
            self.camera_y = int(target_y)
            
            # Draw everything efficiently
            if hasattr(self, 'background'):
                # Draw simple background if no map
                self.screen.blit(self.background, (0, 0))
                
                # Optimized grid drawing - only draw visible lines
                grid_color = (70, 100, 70)
                start_x = (self.camera_x // 32) * 32 - self.camera_x
                start_y = (self.camera_y // 32) * 32 - self.camera_y
                
                for x in range(int(start_x), self.camera_width + 32, 32):
                    pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.camera_height), 1)
                for y in range(int(start_y), self.camera_height + 32, 32):
                    pygame.draw.line(self.screen, grid_color, (0, y), (self.camera_width, y), 1)
                
                # Draw only visible sprites (culling optimization)
                for sprite in sorted(self.all_sprites.sprites(), key=lambda s: s.rect.centery):
                    sprite_x = sprite.rect.x - self.camera_x
                    sprite_y = sprite.rect.y - self.camera_y
                    
                    # Only draw if visible on screen (improves performance)
                    if (-sprite.rect.width <= sprite_x <= self.camera_width and
                        -sprite.rect.height <= sprite_y <= self.camera_height):
                        self.screen.blit(sprite.image, (sprite_x, sprite_y))
            else:
                # Use pyscroll renderer
                try:
                    self.all_sprites.center(self.player.rect.center)
                    self.all_sprites.draw(self.screen)
                except Exception as e:
                    # Fallback to optimized simple rendering
                    visible_area = pygame.Rect(
                        self.camera_x, self.camera_y, 
                        self.camera_width, self.camera_height
                    )
                    for sprite in sorted(self.all_sprites.sprites(), key=lambda s: s.rect.centery):
                        if visible_area.colliderect(sprite.rect):
                            self.screen.blit(sprite.image, 
                                (sprite.rect.x - self.camera_x, sprite.rect.y - self.camera_y))
            
            # Draw UI
            self.draw_ui()
            
            # Draw game over or victory screen if needed
            if self.game_state == "game_over":
                self.draw_game_over()
            elif self.game_state == "victory":
                self.draw_victory()
            
            # Update FPS counter every 500ms
            frame_count += 1
            if current_time - fps_update_time > 500:
                fps = int(frame_count * 1000 / (current_time - fps_update_time))
                fps_display = f"FPS: {fps}"
                fps_surface = fps_font.render(fps_display, True, (255, 255, 255))
                fps_update_time = current_time
                frame_count = 0
            
            # Draw FPS counter
            if fps_surface:
                self.screen.blit(fps_surface, (10, 10))
            
            # Update display
            pygame.display.flip()
            
            # Cap frame rate
            self.clock.tick(60)
        
        pygame.quit()