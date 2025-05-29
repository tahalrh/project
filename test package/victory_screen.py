import pygame
import sys

def show_victory_screen(screen, level, enemies_defeated):
    """Display victory screen and wait for player to continue or quit"""
    # Create a semi-transparent overlay
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Black with 70% opacity
    
    # Create fonts
    title_font = pygame.font.Font(None, 72)
    text_font = pygame.font.Font(None, 36)
    stats_font = pygame.font.Font(None, 28)
    
    # Create text surfaces
    title = title_font.render("VICTORY!", True, (0, 255, 0))
    stats = stats_font.render(f"Level {level} Completed | Enemies Defeated: {enemies_defeated}", 
                             True, (255, 255, 255))
    continue_text = text_font.render("Press C to Continue", True, (200, 255, 200))
    quit_text = text_font.render("Press Q to Quit", True, (255, 200, 200))
    
    # Get rectangles for positioning
    title_rect = title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 80))
    stats_rect = stats.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    continue_rect = continue_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 80))
    quit_rect = quit_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 130))
    
    # Main victory loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:  # Continue
                    return True
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:  # Quit
                    pygame.quit()
                    sys.exit()
        
        # Draw everything
        screen.blit(overlay, (0, 0))
        screen.blit(title, title_rect)
        screen.blit(stats, stats_rect)
        screen.blit(continue_text, continue_rect)
        screen.blit(quit_text, quit_rect)
        
        pygame.display.flip()
    
    return False
