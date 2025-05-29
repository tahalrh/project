import pygame
import random
import math
import os
from functools import lru_cache

class Enemy(pygame.sprite.Sprite):
    SPRITE_SIZE = 64
    DEFAULT_SPEED = 0.8
    DEFAULT_HEALTH = 30
    ATTACK_POWER = 5
    
    def __init__(self, x, y, enemy_type="slime_green"):
        super().__init__()
        self.sprite_width = 64
        self.sprite_height = 64
        
        # Add damage attribute
        self.damage = self.ATTACK_POWER
        
        # Animation state
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 150  # milliseconds per frame
        self.last_update = pygame.time.get_ticks()
        self.frames = []
    
        try:
            # Load sprite sheet
            self.sprite_sheet = pygame.image.load('Slime_Green.png').convert_alpha()
            
            # Calculate sprite sheet dimensions
            sheet_width = self.sprite_sheet.get_width()
            sheet_height = self.sprite_sheet.get_height()
            
            # Calculate individual sprite size (4x4 grid)
            self.sprite_width = sheet_width // 8
            self.sprite_height = sheet_height // 4
            
            # Extract only the first frame from the first row (down direction)
            frame = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
            frame.blit(self.sprite_sheet, (0, 0), 
                      (0, 0, self.sprite_width, self.sprite_height))
            self.frames = [frame]  # Only keep one frame
            
            # Set the image to our single frame
            self.image = self.frames[0]
            
        except pygame.error as e:
            print(f"Warning: Could not load Slime_Green.png ({e}), using placeholder")
            self.image = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
            pygame.draw.circle(
                self.image,
                (0, 200, 0),
                (self.sprite_width//2, self.sprite_height//2),
                self.sprite_width // 2 - 2
            )

        # Créer un rectangle de collision plus petit que le sprite
        self.rect = self.image.get_rect()
        self.rect.width = max(20, self.rect.width - 8)
        self.rect.height = max(20, self.rect.height - 8)
        
        # Ajuster la position pour centrer le rectangle de collision
        self.rect.x = x + (self.image.get_width() - self.rect.width) // 2
        self.rect.y = y + (self.image.get_height() - self.rect.height) // 2
        
        # Position flottante pour des mouvements plus fluides
        self.float_x = float(self.rect.x)
        self.float_y = float(self.rect.y)
        
        # Movement
        self.speed = 0.8
        self.float_x = float(x)
        self.float_y = float(y)
        self.direction_timer = 0
        self.direction_change_time = random.uniform(1.0, 3.0)
        self.dx = 0
        self.dy = 0
        
        # Combat stats
        self.health = 30
        self.max_health = 30
        self.attack_power = 5
        self.detection_radius = 150
        self.attack_radius = 40
        self.knockback_time = 0
        self.hit_cooldown = 0
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 200  # milliseconds
    
    def load_animation_frames(self):
        """Load all animation frames from the sprite sheet"""
        self.animation_frames = []
        
        # Assuming 4 directions (down, left, right, up) with 4 frames each
        for row in range(4):  # 4 directions
            frames = []
            for col in range(4):  # 4 frames per direction
                frame = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
                frame.blit(self.sprite_sheet, (0, 0), 
                          (col * self.sprite_width, row * self.sprite_height, 
                           self.sprite_width, self.sprite_height))
                frames.append(frame)
            self.animation_frames.append(frames)
    
    def update_animation(self, dt):
        """Update the current animation frame"""
        if not hasattr(self, 'animation_frames') or not self.animation_frames:
            return
            
        # Only animate if moving
        if self.dx != 0 or self.dy != 0:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % 4  # Assuming 4 frames per animation
        else:
            self.current_frame = 0  # Reset to first frame when not moving
            
        # Determine direction (0=down, 1=left, 2=right, 3=up)
        direction = 0  # Default to down
        if abs(self.dx) > abs(self.dy):
            direction = 1 if self.dx < 0 else 2
        elif self.dy != 0:
            direction = 3 if self.dy < 0 else 0
            
        # Update image based on direction and current frame
        if direction < len(self.animation_frames) and self.current_frame < len(self.animation_frames[direction]):
            self.image = self.animation_frames[direction][self.current_frame]
    
    def update(self, dt):
        """Update enemy state and animation"""
        # Update position
        self.float_x += self.dx * self.speed * dt * 60  # 60 is for frame rate normalization
        self.float_y += self.dy * self.speed * dt * 60
        
        # Update rect position
        self.rect.x = int(self.float_x)
        self.rect.y = int(self.float_y)
        
        # Update animation
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
        
        # Update direction based on movement
        if abs(self.dx) > abs(self.dy):
            row = 1 if self.dx < 0 else 2  # Left or Right
        else:
            row = 3 if self.dy < 0 else 0  # Up or Down
        
        # Calculate frame index based on row and current animation frame
        frame_index = row * 4 + (self.current_frame % 4)
        if frame_index < len(self.frames):
            self.image = self.frames[frame_index]
    
    def _load_sprites(self):
        """Load and setup sprites for the enemy"""
        self.image = self.get_image(0, 0, self.SPRITE_SIZE, self.SPRITE_SIZE)
        self.original_image = self.image
    
    def _setup_movement(self, x, y):
        """Initialize movement variables"""
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.float_x = float(x)
        self.float_y = float(y)
        self.speed = self.DEFAULT_SPEED
        self.direction_timer = 0
        self.direction_change_time = random.uniform(1.0, 3.0)
        self.dx = 0
        self.dy = 0
    
    def _setup_combat_stats(self):
        """Initialize combat statistics"""
        self.health = self.DEFAULT_HEALTH
        self.max_health = self.DEFAULT_HEALTH
        self.attack_power = self.ATTACK_POWER
        self.detection_radius = 150
        self.attack_radius = 40
        self.knockback_time = 0
        self.hit_cooldown = 0
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 200  # milliseconds
    
    def _handle_timers(self, dt):
        """Update and handle timers for the enemy"""
        if self.hit_cooldown > 0:
            self.hit_cooldown -= dt
            
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
                self.image.set_alpha(255)
    
        # Handle knockback
        if self.knockback_time > 0:
            self.knockback_time -= dt
            return True
        
        return False
    
    def _handle_ai_behavior(self, player, dt):
        """Handle enemy AI behavior based on player position"""
        # Calculate distance to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        
        # Change behavior based on distance to player
        if distance < self.attack_radius:
            if self.hit_cooldown <= 0:
                self.attack(player)
        elif distance < self.detection_radius:
            # Move towards player
            if distance > 0:
                self.dx = (dx / distance) * self.speed
                self.dy = (dy / distance) * self.speed
        else:
            self.dx = 0
            self.dy = 0
    
    def _handle_movement(self, blocked_rects, player=None, dt=0):
        """Handle enemy movement and collisions - optimized version"""
        # Random movement when idle (only if not chasing player)
        if not hasattr(self, 'chasing_player') or not self.chasing_player:
            self.direction_timer += dt / 1000.0
            if self.direction_timer >= self.direction_change_time:
                self.direction_timer = 0
                self.direction_change_time = random.uniform(1.0, 3.0)
                self.dx = random.uniform(-1, 1) * self.speed * 0.5
                self.dy = random.uniform(-1, 1) * self.speed * 0.5
        
        # Skip movement processing if not moving
        if abs(self.dx) < 0.01 and abs(self.dy) < 0.01:
            return
        
        # Move the enemy with optimized collision detection
        self.float_x += self.dx
        self.float_y += self.dy
        
        # Check for collisions with blocked tiles using more efficient collision checking
        new_rect = self.rect.copy()
        moved = False
        
        # Process horizontal movement first
        new_rect.x = int(self.float_x)
        
        if blocked_rects:
            # Use spatial optimizations if available
            if hasattr(self, 'nearby_blocks'):
                collision_found = any(new_rect.colliderect(r) for r in self.nearby_blocks)
            else:
                # Faster collision check - exit early when collision found
                collision_found = False
                for rect in blocked_rects:
                    if new_rect.colliderect(rect):
                        collision_found = True
                        break
            
            if not collision_found:
                self.rect.x = new_rect.x
                moved = True
            else:
                self.float_x = float(self.rect.x) 
                self.dx = -self.dx * 0.8  # Bounce with dampening
        else:
            self.rect.x = new_rect.x
            moved = True
        
        # Process vertical movement
        new_rect.x = self.rect.x
        new_rect.y = int(self.float_y)
        
        if blocked_rects:
            # Use same collision optimization as above
            if hasattr(self, 'nearby_blocks'):
                collision_found = any(new_rect.colliderect(r) for r in self.nearby_blocks)
            else:
                collision_found = False
                for rect in blocked_rects:
                    if new_rect.colliderect(rect):
                        collision_found = True
                        break
            
            if not collision_found:
                self.rect.y = new_rect.y
                moved = True
            else:
                self.float_y = float(self.rect.y)
                self.dy = -self.dy * 0.8  # Bounce with dampening
        else:
            self.rect.y = new_rect.y
            moved = True
    
    def take_damage(self, amount):
        """Handle taking damage"""
        if self.invincible:
            return 0
            
        damage = max(1, amount)
        self.health -= damage
        self.invincible = True
        self.invincible_timer = self.invincible_duration
        self.state = 'hurt'
        
        # Flash effect when hit
        self.image.set_alpha(128)
        
        return damage
    
    def attack(self, player):
        """Attack the player"""
        if self.hit_cooldown <= 0:
            player.take_damage(self.attack_power)
            self.hit_cooldown = 1.0  # 1 second cooldown between attacks
            
            # Apply knockback to self
            dx = self.rect.centerx - player.rect.centerx
            dy = self.rect.centery - player.rect.centery
            distance = max(1, math.sqrt(dx*dx + dy*dy))
            knockback = 5
            
            self.knockback_time = 100  # 100ms knockback duration
            self.float_x += (dx / distance) * knockback * 5
            self.float_y += (dy / distance) * knockback * 5
    
    def draw_health_bar(self, surface):
        """Draw health bar above the enemy - optimized with caching"""
        # Only draw health bar if enemy is damaged
        if self.health < self.max_health:
            # Use cached rects when health hasn't changed
            health_ratio = self.health / self.max_health
            
            # Cache health bar rects for reuse
            if (not hasattr(self, '_cached_health_ratio') or 
                self._cached_health_ratio != health_ratio or
                not hasattr(self, '_cached_health_rects')):
                
                # Update cache
                self._cached_health_ratio = health_ratio
                
                # Calculate health bar dimensions
                bar_width = 30
                bar_height = 4
                fill_width = int((self.health / self.max_health) * bar_width)
                
                # Create rectangles
                self._cached_health_rects = {
                    'outline': pygame.Rect(0, 0, bar_width, bar_height),
                    'fill': pygame.Rect(0, 0, fill_width, bar_height)
                }
            
            # Position health bars above the enemy
            pos_x = self.rect.centerx
            pos_y = self.rect.top - 5
            
            outline_rect = self._cached_health_rects['outline'].copy()
            fill_rect = self._cached_health_rects['fill'].copy()
            
            outline_rect.midbottom = (pos_x, pos_y)
            fill_rect.midbottom = (pos_x, pos_y)
            
            # Draw health bars
            pygame.draw.rect(surface, (255, 0, 0), outline_rect)
            pygame.draw.rect(surface, (0, 255, 0), fill_rect)
