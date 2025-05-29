import pygame
import sys

def show_game_over(screen):
    """Display game over screen and wait for player to restart or quit"""
    # Create a semi-transparent overlay
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Black with 70% opacity
    
    # Create fonts
    title_font = pygame.font.Font(None, 72)
    text_font = pygame.font.Font(None, 36)
    
    # Create text surfaces
    title = title_font.render("GAME OVER", True, (255, 0, 0))
    restart_text = text_font.render("Press R to Restart", True, (255, 255, 255))
    quit_text = text_font.render("Press Q to Quit", True, (255, 255, 255))
    
    # Get rectangles for positioning
    title_rect = title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 50))
    restart_rect = restart_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 50))
    quit_rect = quit_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 100))
    
    # Main game over loop
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Restart
                    return True
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:  # Quit
                    pygame.quit()
                    sys.exit()
        
        # Draw everything
        screen.blit(overlay, (0, 0))
        screen.blit(title, title_rect)
        screen.blit(restart_text, restart_rect)
        screen.blit(quit_text, quit_rect)
        
        pygame.display.flip()
    
    return False
