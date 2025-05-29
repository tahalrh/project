import pygame
import os
from functools import lru_cache

class Player(pygame.sprite.Sprite):
    ANIMATION_SPEED = 0.2
    SPRITE_SIZE = 32
    MAX_HEARTS = 6
    HEALTH_PER_HEART = 17
    
    def __init__(self, x, y):
        super().__init__()
        self._load_sprites()
        self._setup_animation()
        self._setup_health()
        self._setup_movement(x, y)
        
    def _load_sprites(self):
        """Load player sprite sheet and create placeholder if it fails"""
        try:
            # Load and convert the sprite sheet once
            self.sprite_sheet = pygame.image.load('Player.png').convert_alpha()
            self.using_placeholder = False
        except pygame.error:
            # Create a placeholder with distinct visuals for each direction
            self.sprite_sheet = pygame.Surface((128, 128), pygame.SRCALPHA)
            
            # Create more visually distinct placeholders for different directions
            # Down (blue)
            for i in range(3):
                rect = pygame.Rect(i * 32, 0, 32, 32)
                pygame.draw.rect(self.sprite_sheet, (0, 0, 255), rect)
                pygame.draw.polygon(self.sprite_sheet, (200, 200, 255), 
                                 [(i*32 + 16, 25), (i*32 + 10, 15), (i*32 + 22, 15)])
            
            # Left (green)
            for i in range(3):
                rect = pygame.Rect(i * 32, 32, 32, 32)
                pygame.draw.rect(self.sprite_sheet, (0, 255, 0), rect)
                pygame.draw.polygon(self.sprite_sheet, (200, 255, 200), 
                                 [(i*32 + 10, 16), (i*32 + 20, 10), (i*32 + 20, 22)])
            
            # Up (red)
            for i in range(3):
                rect = pygame.Rect(i * 32, 64, 32, 32)
                pygame.draw.rect(self.sprite_sheet, (255, 0, 0), rect)
                pygame.draw.polygon(self.sprite_sheet, (255, 200, 200), 
                                 [(i*32 + 16, 10), (i*32 + 10, 20), (i*32 + 22, 20)])
                
            self.using_placeholder = True
            print("Warning: Could not load Player.png, using placeholder")
    
    def _setup_animation(self):
        """Setup player animations from the sprite sheet"""
        # Animation setup
        self.animations = {
            'down': [],
            'left': [],
            'right': [],
            'up': []
        }
        
        # Vérifier la taille totale de la spritesheet pour déterminer la structure
        sprite_sheet_height = self.sprite_sheet.get_height()
        sprite_sheet_width = self.sprite_sheet.get_width()
        
        # Si nous utilisons un placeholder ou si la hauteur indique un format différent
        # nous devons ajuster l'extraction des frames
        rows_in_sheet = sprite_sheet_height // self.SPRITE_SIZE
        cols_in_sheet = sprite_sheet_width // self.SPRITE_SIZE
        print(f"Detected {rows_in_sheet} rows and {cols_in_sheet} columns in player sprite sheet")
        
        # Déterminer les positions des animations selon la taille de la spritesheet
        # Dans une spritesheet typique pour RPG:
        # - Rangée 0: vers le bas
        # - Rangée 1: vers la gauche
        # - Rangée 2: vers la droite
        # - Rangée 3: vers le haut
        down_row = 0
        left_row = min(1, rows_in_sheet - 1) if rows_in_sheet > 1 else 0
        right_row = min(2, rows_in_sheet - 1) if rows_in_sheet > 2 else left_row
        up_row = min(3, rows_in_sheet - 1) if rows_in_sheet > 3 else 0
        
        print(f"Animation rows - down:{down_row}, left:{left_row}, right:{right_row}, up:{up_row}")
        
        # Charger les frames d'animation (3 frames par direction ou moins si disponible)
        frames_per_direction = min(3, cols_in_sheet)
        for i in range(frames_per_direction):
            self.animations['down'].append(self.get_image(i * self.SPRITE_SIZE, down_row * self.SPRITE_SIZE))
            self.animations['left'].append(self.get_image(i * self.SPRITE_SIZE, left_row * self.SPRITE_SIZE))
            self.animations['up'].append(self.get_image(i * self.SPRITE_SIZE, up_row * self.SPRITE_SIZE))
            
            # Si nous avons une rangée spécifique pour la droite, l'utiliser
            # Sinon, retourner les sprites de gauche
            if right_row != left_row and right_row < rows_in_sheet:
                self.animations['right'].append(self.get_image(i * self.SPRITE_SIZE, right_row * self.SPRITE_SIZE))
        
        # Si nous n'avons pas chargé d'animation pour la droite, retourner les animations gauches
        if not self.animations['right']:
            self.animations['right'] = [pygame.transform.flip(image, True, False) 
                                      for image in self.animations['left']]
        
        # Vérifier que chaque direction a au moins une frame d'animation
        # et créer des fallbacks si nécessaire
        for direction in ['down', 'left', 'right', 'up']:
            if not self.animations[direction]:
                print(f"Missing animation frames for direction: {direction}")
                if direction == 'up':
                    # Pour l'animation vers le haut, créer une version modifiée de l'animation vers le bas
                    for frame in self.animations['down']:
                        up_frame = frame.copy()
                        # Ajouter un indicateur visuel pour la direction vers le haut
                        if hasattr(self, 'using_placeholder') and self.using_placeholder:
                            pygame.draw.polygon(up_frame, (255, 0, 0), 
                                              [(self.SPRITE_SIZE // 2, 5), 
                                               (self.SPRITE_SIZE // 2 - 5, 15), 
                                               (self.SPRITE_SIZE // 2 + 5, 15)])
                        self.animations['up'].append(up_frame)
                        
                elif direction == 'right':
                    # Pour l'animation vers la droite, retourner les animations vers la gauche
                    self.animations['right'] = [pygame.transform.flip(image, True, False) 
                                              for image in self.animations['left']]
                elif direction == 'left':
                    # Pour l'animation vers la gauche, retourner les animations vers la droite
                    self.animations['left'] = [pygame.transform.flip(image, True, False) 
                                             for image in self.animations['right']]
        
        # Définir l'état initial
        self.direction = 'down'
        self.current_frame = 0
        self.animation_speed = 0.2  # Temps entre les frames en secondes
        self.animation_timer = 0
        self.image = self.animations[self.direction][0]
        self.rect = self.image.get_rect()
        self.speed = 1.5  # Vitesse réduite pour un meilleur contrôle
    
    def _setup_health(self):
        """Setup player health and hearts"""
        self.max_hearts = 6
        self.current_hearts = 6
        self.health = self.current_hearts * self.HEALTH_PER_HEART
        self.max_health = self.max_hearts * self.HEALTH_PER_HEART
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 1000  # milliseconds
        self.speed = 1.5  # Vitesse réduite pour un meilleur contrôle

        # Création de cœurs individuels comme images
        try:
            # Essayer de charger depuis différents emplacements possibles
            paths = ['HealthUI.png', 'assets/HealthUI.png', 'UI/HealthUI.png']
            image_loaded = False
            
            for path in paths:
                try:
                    self.hearts_sheet = pygame.image.load(path).convert_alpha()
                    print(f"Successfully loaded health UI from {path}")
                    image_loaded = True
                    break
                except pygame.error:
                    continue
            
            if not image_loaded:
                raise pygame.error("Could not find HealthUI.png")
                
            # Mesurer l'image chargée
            total_width = self.hearts_sheet.get_width()
            total_height = self.hearts_sheet.get_height()
            print(f"Health UI dimensions: {total_width}x{total_height}")
            
            # Approche simplifiée - nous allons générer directement les cœurs
            # comme ils sont supposés être
            self.hearts = []
            
            # Créer un cœur complet (rouge)
            full_heart = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.polygon(full_heart, (255, 0, 0), 
                             [(8, 4), (4, 0), (0, 4), (8, 16), (16, 4), (12, 0)])
            pygame.draw.polygon(full_heart, (200, 0, 0), 
                             [(8, 6), (5, 3), (2, 6), (8, 14), (14, 6), (11, 3)], 1)
            
            # Créer un cœur vide (contour)
            empty_heart = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.polygon(empty_heart, (100, 0, 0), 
                             [(8, 4), (4, 0), (0, 4), (8, 16), (16, 4), (12, 0)], 1)
            
            # Créer les états intermédiaires (remplissage partiel)
            partial_hearts = []
            for i in range(1, 6):  # 5 états intermédiaires
                heart = pygame.Surface((16, 16), pygame.SRCALPHA)
                fill_level = (6 - i) / 6
                color = (255, 0, 0, int(255 * fill_level))
                pygame.draw.polygon(heart, color, 
                                 [(8, 4), (4, 0), (0, 4), (8, 16), (16, 4), (12, 0)])
                pygame.draw.polygon(heart, (100, 0, 0), 
                                 [(8, 4), (4, 0), (0, 4), (8, 16), (16, 4), (12, 0)], 1)
                partial_hearts.append(heart)
            
            # Assembler tous les états dans l'ordre: plein, partiels, vide
            self.hearts = [full_heart] + partial_hearts + [empty_heart]
            self.heart_width = 16
            self.heart_height = 16
            
            print(f"Created {len(self.hearts)} heart states for health UI")
                
            # Debug info
            print(f"Heart dimensions: {self.heart_width}x{self.heart_height}")
                
        except Exception as e:
            print(f"Warning: Could not load health UI: {str(e)}, using placeholder hearts")
            self.heart_width = 16
            self.heart_height = 16
            self.hearts = []
            # Create 7 placeholder hearts with different fill levels
            for i in range(7):
                heart = pygame.Surface((16, 16), pygame.SRCALPHA)
                fill_level = (6 - i) / 6  # Full to empty
                color = (255, 0, 0, int(255 * fill_level))
                pygame.draw.polygon(heart, color, 
                                 [(8, 4), (4, 0), (0, 4), (8, 16), (16, 4), (12, 0)])
                self.hearts.append(heart)

    def _setup_movement(self, x, y):
        """Initialize player position and movement attributes"""
        self.rect.x = x
        self.rect.y = y
        self.speed = 1.5  # Slower speed for better control
    
    @lru_cache(maxsize=16)
    def get_image(self, x, y):
        """Extract a single frame from the sprite sheet with caching"""
        # Use LRU cache to avoid extracting the same frame multiple times
        image = pygame.Surface((self.SPRITE_SIZE, self.SPRITE_SIZE), pygame.SRCALPHA)
        
        # Make sure we don't try to access outside the sprite sheet
        if (x >= 0 and y >= 0 and 
            x + self.SPRITE_SIZE <= self.sprite_sheet.get_width() and
            y + self.SPRITE_SIZE <= self.sprite_sheet.get_height()):
            image.blit(self.sprite_sheet, (0, 0), (x, y, self.SPRITE_SIZE, self.SPRITE_SIZE))
        else:
            # Add visual indicator when accessing invalid sprite coordinates
            pygame.draw.rect(image, (255, 0, 255), image.get_rect(), 2)
            font = pygame.font.Font(None, 18)
            text = font.render(f"?{x},{y}", True, (255, 255, 255))
            image.blit(text, (2, 2))
            
        return image
    
    def update(self, dt):
        """Update player animation and state"""
        # Use delta time for smooth animation regardless of framerate
        self._update_invincibility(dt)
        
        # Only update animation when player is moving
        if hasattr(self, 'is_moving') and self.is_moving:
            self._update_animation(dt)
    
    def _update_invincibility(self, dt):
        """Update invincibility timer"""
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
    
    def _update_animation(self, dt):
        """Update player animation frames with framerate independence"""
        # Convert milliseconds to seconds for animation timing
        self.animation_timer += dt / 1000.0
        
        if self.animation_timer >= self.animation_speed:
            # Reset timer but keep fractional remainder for smoother animation
            self.animation_timer %= self.animation_speed
            
            # Update frame and get cached image from animations dictionary
            self.current_frame = (self.current_frame + 1) % len(self.animations[self.direction])
            self.image = self.animations[self.direction][self.current_frame]
            
            # Maintain alpha value for invincibility effect
            if self.invincible:
                self.image.set_alpha(128)
            else:
                self.image.set_alpha(255)
    
    def update_direction(self, dx, dy):
        """Update player direction based on movement input, even when blocked by walls
        La priorité est donnée au mouvement vertical pour correspondre au jeu original"""
        # Inverser la priorité pour donner priorité au mouvement vertical
        old_direction = getattr(self, 'direction', 'down')
        
        if dy < 0:  # Déplacement vers le haut en priorité
            self.direction = 'up'
        elif dy > 0:  # Déplacement vers le bas en priorité
            self.direction = 'down'
        elif dx > 0:  # Déplacement vers la droite si pas de mouvement vertical
            self.direction = 'right'
        elif dx < 0:  # Déplacement vers la gauche si pas de mouvement vertical
            self.direction = 'left'
            
        # Afficher un message de débogage si la direction change
        if old_direction != self.direction:
            print(f"Direction changed from {old_direction} to {self.direction}")
            
        # Vérifier que nous avons des animations pour cette direction
        if self.direction not in self.animations or not self.animations[self.direction]:
            print(f"Warning: Missing animation for direction '{self.direction}', using fallback")
            # Utiliser une direction alternative si l'animation manque
            if self.direction == 'up' and self.animations['down']:
                self.animations['up'] = []
                for frame in self.animations['down']:
                    up_frame = frame.copy()
                    # Marqueur visuel pour la direction haut
                    pygame.draw.line(up_frame, (255, 0, 0), (16, 8), (16, 24), 2)
                    pygame.draw.line(up_frame, (255, 0, 0), (8, 16), (24, 16), 2)
                    self.animations['up'].append(up_frame)
            
        # Mettre à jour l'image du joueur pour correspondre à la nouvelle direction
        if self.current_frame != 0 or not hasattr(self, 'image'):
            self.current_frame = 0
            # Récupérer l'animation pour la direction actuelle
            if self.direction in self.animations and self.animations[self.direction]:
                self.image = self.animations[self.direction][self.current_frame]
                
                # Maintenir la transparence si invincible
                if self.invincible:
                    self.image.set_alpha(128)
                else:
                    self.image.set_alpha(255)
    
    def move(self, dx, dy):
        """Move the player with animation - with collision support"""
        # Track if player is currently moving for animation optimization
        self.is_moving = (dx != 0 or dy != 0)
        
        if self.is_moving:
            # Update direction based on movement - only when actually moving
            if dx > 0:
                self.direction = 'right'
            elif dx < 0:
                self.direction = 'left'
            elif dy > 0:
                self.direction = 'down'
            elif dy < 0:
                self.direction = 'up'
            
            # Apply movement directly to the rect position
            # This is important for proper collision handling
            if dx != 0:
                self.rect.x += int(dx)
            if dy != 0:
                self.rect.y += int(dy)
                
            # Update animation
            self.animation_timer += 1/60.0  # Approximate frame time
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.animations[self.direction])
                self.image = self.animations[self.direction][self.current_frame]
                
                # Maintain transparency if player is invincible
                if self.invincible:
                    self.image.set_alpha(128)
        else:
            # Reset to standing frame when not moving
            if self.current_frame != 0:
                self.current_frame = 0
                self.image = self.animations[self.direction][self.current_frame]
                
                # Maintain transparency if invincible
                if self.invincible:
                    self.image.set_alpha(128)
    
    def draw_hearts(self, surface):
        """Draw the player's hearts/health"""
        hearts_spacing = 4
        start_x = 10
        start_y = 10
        
        # Make sure we have heart images before trying to render them
        if not hasattr(self, 'hearts') or not self.hearts or len(self.hearts) < 7:
            print("Warning: Missing heart images, skipping heart rendering")
            return
            
        # Agrandir pour une meilleure visibilité
        scale_factor = 2.0
        heart_width = self.heart_width
        heart_height = self.heart_height
        
        # Afficher les cœurs (scale_factor pour agrandir)
        for i in range(self.max_hearts):
            heart_x = start_x + (heart_width * scale_factor + hearts_spacing) * i
            heart_y = start_y
            
            if i < self.current_hearts:
                # Cœur plein (première ligne - index 0)
                heart_img = pygame.transform.scale(
                    self.hearts[0],
                    (int(heart_width * scale_factor), int(heart_height * scale_factor))
                )
            else:
                # Cœur vide (dernière ligne - index 6)
                heart_img = pygame.transform.scale(
                    self.hearts[6], 
                    (int(heart_width * scale_factor), int(heart_height * scale_factor))
                )
                
            surface.blit(heart_img, (heart_x, heart_y))
        
        # Afficher aussi les statistiques du joueur
        stats_x = start_x
        stats_y = start_y + heart_height * scale_factor + 5
        stats_font = pygame.font.Font(None, 20)
        stats_text = f"Level: {1} | ATK: {10} | DEF: {5} | EXP: {0}/100"
        stats_surface = stats_font.render(stats_text, True, (255, 255, 255))
        surface.blit(stats_surface, (stats_x, stats_y))
    
    def take_damage(self, amount):
        """Handle taking damage"""
        if self.invincible:
            return False
        
        self.invincible = True
        self.invincible_timer = self.invincible_duration
        
        # Convert damage to hearts (1 heart = ~17 health)
        heart_damage = max(1, amount // 17)
        self.current_hearts = max(0, self.current_hearts - heart_damage)
        self.health = self.current_hearts * 17
        
        # Visual feedback
        self.image.set_alpha(128)
        
        return True
    
    def heal(self, amount):
        """Heal the player with hearts system"""
        heart_heal = max(1, amount // 17)
        self.current_hearts = min(self.max_hearts, self.current_hearts + heart_heal)
        self.health = self.current_hearts * 17
    
    def reset_alpha(self):
        """Reset sprite alpha after invincibility"""
        self.image.set_alpha(255)
        attack_size = 40
    def get_attack_rect(self):
        """Get the attack hitbox based on player direction"""
        attack_distance = 50  # Attack range in pixels
        attack_size = 40
        if self.direction == 'up':
            return pygame.Rect(
                self.rect.centerx - attack_size//2,
                self.rect.top - attack_distance,
                attack_size,
                attack_distance
            )
        elif self.direction == 'down':
            return pygame.Rect(
                self.rect.centerx - attack_size//2,
                self.rect.bottom,
                attack_size,
                attack_distance
            )
        elif self.direction == 'left':
            return pygame.Rect(
                self.rect.left - attack_distance,
                self.rect.centery - attack_size//2,
                attack_distance,
                attack_size
            )
        else:  # right
            return pygame.Rect(
                self.rect.right,
                self.rect.centery - attack_size//2,
                attack_distance,
                attack_size
            )