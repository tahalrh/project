import pygame
import os

def create_placeholders():
    # Create assets directory if it doesn't exist
    os.makedirs('assets', exist_ok=True)
    
    # Initialize Pygame
    pygame.init()
    
    # Create player sprite sheet (4 directions, 4 frames each)
    player_sheet = pygame.Surface((128, 128), pygame.SRCALPHA)
    
    # Colors
    blue = (0, 0, 255, 255)
    light_blue = (100, 100, 255, 255)
    dark_blue = (0, 0, 150, 255)
    
    # Draw player frames (simple colored rectangles for now)
    for direction in range(4):
        for frame in range(4):
            x = frame * 32
            y = direction * 32
            
            # Draw base
            pygame.draw.rect(player_sheet, blue, (x, y, 32, 32))
            pygame.draw.rect(player_sheet, (0, 0, 0, 255), (x, y, 32, 32), 1)
            
            # Add some simple features to distinguish directions
            if direction == 0:  # Down
                pygame.draw.rect(player_sheet, dark_blue, (x+12, y+8, 8, 8))  # Eyes
                pygame.draw.rect(player_sheet, dark_blue, (x+12, y+16, 8, 4))  # Mouth
            elif direction == 1:  # Left
                pygame.draw.rect(player_sheet, dark_blue, (x+8, y+12, 8, 8))  # Eyes
                pygame.draw.rect(player_sheet, dark_blue, (x+16, y+12, 4, 8))  # Mouth
            elif direction == 2:  # Right
                pygame.draw.rect(player_sheet, dark_blue, (x+16, y+12, 8, 8))  # Eyes
                pygame.draw.rect(player_sheet, dark_blue, (x+12, y+12, 4, 8))  # Mouth
            else:  # Up
                pygame.draw.rect(player_sheet, dark_blue, (x+12, y+16, 8, 8))  # Eyes
                pygame.draw.rect(player_sheet, dark_blue, (x+12, y+12, 8, 4))  # Mouth
    
    # Save player sprite sheet
    pygame.image.save(player_sheet, 'Player.png')
    
    # Create enemy sprite (green slime)
    slime_sheet = pygame.Surface((128, 128), pygame.SRCALPHA)
    green = (0, 200, 0, 255)
    dark_green = (0, 100, 0, 255)
    light_green = (100, 255, 100, 255)
    
    # Draw slime frames (simple animation)
    for frame in range(4):
        x = frame * 32
        y = 0
        
        # Draw blob shape (squished circle)
        height = 24 - frame * 2  # Vary height for animation
        pygame.draw.ellipse(slime_sheet, green, (x+4, y+16-height//2, 24, height+8))
        pygame.draw.ellipse(slime_sheet, dark_green, (x+4, y+16-height//2, 24, height+8), 1)
        
        # Add eyes
        eye_y = y + 12 - frame  # Eyes move up and down
        pygame.draw.circle(slime_sheet, (255, 255, 255), (x+10, eye_y), 4)
        pygame.draw.circle(slime_sheet, (255, 255, 255), (x+22, eye_y), 4)
        pygame.draw.circle(slime_sheet, (0, 0, 0), (x+10, eye_y), 2)
        pygame.draw.circle(slime_sheet, (0, 0, 0), (x+22, eye_y), 2)
    
    # Save enemy sprite sheet
    pygame.image.save(slime_sheet, 'Slime_Green.png')
    
    # Create a simple tileset for the map
    tileset = pygame.Surface((32, 32), pygame.SRCALPHA)
    # Grass tile (index 0)
    pygame.draw.rect(tileset, (100, 200, 100), (0, 0, 32, 32))
    # Dirt tile (index 1, for collision)
    pygame.draw.rect(tileset, (139, 69, 19), (0, 0, 32, 32))
    # Save tileset
    pygame.image.save(tileset, 'assets/tileset.png')
    
    print("Placeholder assets created successfully!")

if __name__ == '__main__':
    create_placeholders()
