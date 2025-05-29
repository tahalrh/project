import pygame
import sys
from game import Game
from start_screen import start_screen

def main():
    pygame.init()
    try:
        # Afficher l'écran de démarrage
        start_game = start_screen()
        
        # Si l'utilisateur a cliqué sur PLAY, lancer le jeu
        # Si l'utilisateur a cliqué sur QUIT, quitter le jeu
        if start_game:
            game = Game()
            game.run()
        else:
            print("Game exited from start screen")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    main()