import pygame

def start_screen():
    pygame.init()
    screen_width, screen_height = 1140, 660
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("blue lock")

    background_img = pygame.image.load("intro.jpg").convert()
    background_img = pygame.transform.scale(background_img, (screen_width, screen_height))

    # Couleurs des boutons
    button_color = (102, 178, 255)
    button_hover = (0, 255, 0)
    quit_button_color = (255, 102, 102)  # Rouge pour le bouton Quit
    quit_button_hover = (255, 0, 0)      # Rouge plus vif pour le survol
    
    # Play button setup
    play_button_rect = pygame.Rect(screen_width//2 - 100, 480, 200, 60)
    
    # Quit button setup 
    quit_button_rect = pygame.Rect(screen_width//2 - 100, 560, 200, 60)
    
    # Texte des boutons
    font = pygame.font.SysFont(None, 60)
    play_text = font.render("PLAY", True, (255, 255, 255))
    play_text_rect = play_text.get_rect(center=play_button_rect.center)
    
    quit_text = font.render("QUIT", True, (255, 255, 255))
    quit_text_rect = quit_text.get_rect(center=quit_button_rect.center)

    clock = pygame.time.Clock()
    running = True
    play_clicked = False
    quit_clicked = False

    while running and not play_clicked and not quit_clicked:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                quit_clicked = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if play_button_rect.collidepoint(event.pos):
                    play_clicked = True
                elif quit_button_rect.collidepoint(event.pos):
                    quit_clicked = True
                    running = False

        screen.blit(background_img, (0, 0))

        # Dessiner le titre du jeu
        title_font = pygame.font.SysFont(None, 100)
        title_text = title_font.render("RPG ADVENTURE", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(screen_width//2, 200))
        screen.blit(title_text, title_rect)

        # Gestion des boutons et de leur survol
        mouse_pos = pygame.mouse.get_pos()
        
        # Bouton PLAY
        play_color = button_hover if play_button_rect.collidepoint(mouse_pos) else button_color
        pygame.draw.rect(screen, play_color, play_button_rect)
        screen.blit(play_text, play_text_rect)
        
        # Bouton QUIT
        quit_color = quit_button_hover if quit_button_rect.collidepoint(mouse_pos) else quit_button_color
        pygame.draw.rect(screen, quit_color, quit_button_rect)
        screen.blit(quit_text, quit_text_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.display.quit()
    if quit_clicked:
        return False  # Indique qu'il faut quitter le jeu
    return play_clicked  # True si le jeu doit démarrer