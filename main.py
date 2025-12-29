import pygame
import sys
import random
import numpy as np
import tcod
from constants import CELL_SIZE, Directions, Points
from game_objects import Wall, Dot, Energizer
from moving_objects import Player, Spook
from button import ImageButton, fade



pygame.init()

# Screen parameters
WIDTH, HEIGHT = 960, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Menu")
main_background = pygame.image.load("background.jpg")

#Music
pygame.mixer.music.load("music1.mp3")
pygame.mixer.music.play(-1)

def pixel_to_cell(pos, size=24):
    return pos[0] // size, pos[1] // size

def cell_to_pixel(pos, size=24):
    return pos[0] * size, pos[1] * size


class GameManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption('Pacman')
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.victory = False
        self.paused = False
        self.objects = []
        self.dots = []
        self.spooks = []
        self.energizers = []
        self.walls = []  #
        self.score = 0
        self.lives = 3
        self.player = None
        self.power_active = False
        self.mode = "SCATTER"
        self.mode_phases = [(7, 20), (7, 20), (5, 20), (5, 999999)]
        self.phase = 0
        self.mode_event = pygame.USEREVENT + 1
        self.power_end_event = pygame.USEREVENT + 2
        self.animation_event = pygame.USEREVENT + 3

    def increase_score(self, points):
        self.score += points

    def start(self, fps):
        win_sound = pygame.mixer.Sound("win.mp3")
        fail_sound = pygame.mixer.Sound("fail.mp3")
        self.change_mode()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
        pygame.time.set_timer(self.animation_event, 200)
        while self.is_running:
            if not self.paused:
                for obj in self.objects:
                    obj.update()
                    obj.render()
                self.display_text(f"Score: {self.score}", (30, 675))
                self.display_text(f"Lives: {self.lives}", (550, 675))
                if not self.player:
                    print("YOU FAIL!")
                    fail_sound.play()
                    fail(self.score)
                if self.victory:
                    print("YOU WIN!")
                    win_sound.play()
                    win(self.score)
            else:
                self.render_pause_menu()
            pygame.display.flip()
            self.clock.tick(fps)
            self.screen.fill((0, 0, 0))
            self.process_events()
        print("Game ended")
        

    

    def change_mode(self):
        scatter, chase = self.mode_phases[self.phase]
        self.mode = "SCATTER" if self.mode == "CHASE" else "CHASE"
        self.phase += 1 if self.mode == "SCATTER" else 0
        pygame.time.set_timer(self.mode_event, (scatter if self.mode == "SCATTER" else chase) * 1000)

    def activate_power(self):
        pygame.time.set_timer(self.power_end_event, 2000)

    def add_object(self, obj):
        self.objects.append(obj)

    def add_dot(self, dot):
        self.objects.append(dot)
        self.dots.append(dot)

    def add_spook(self, spook):
        self.objects.append(spook)
        self.spooks.append(spook)

    def add_energizer(self, energizer):
        self.objects.append(energizer)
        self.energizers.append(energizer)


    def set_power(self, active):
        self.power_active = active
        self.set_mode("SCATTER")
        self.activate_power()
 

    def set_victory(self):
        self.victory = True

    def get_victory(self):
        return self.victory


    def get_player_pos(self):
        return self.player.get_pos() if self.player else (0, 0)

    def set_mode(self, mode):
        self.mode = mode

    def get_mode(self):
        return self.mode

    def end_game(self):
        if self.player in self.objects:
            self.objects.remove(self.player)
        self.player = None

    def lose_life(self):
        self.lives -= 1
        self.player.set_pos(24, 24)
        self.player.set_dir(Directions.NONE)
        if self.lives == 0:
            self.end_game()


    def display_text(self, text, pos=(24, 0), size=30):
        font = pygame.font.SysFont('Arial', size)
        text_surface = font.render(text, False, (255, 255, 255))
        self.screen.blit(text_surface, pos)

    def is_power_active(self):
        return self.power_active

    def add_wall(self, wall):
        self.add_object(wall)
        self.walls.append(wall)

    def get_walls(self):
        return self.walls

    def get_dots(self):
        return self.dots

    def get_spooks(self):
        return self.spooks

    def get_energizers(self):
        return self.energizers

    def get_objects(self):
        return self.objects

    def set_player(self, player):
        self.add_object(player)
        self.player = player

    def process_events(self):
        click_sound = pygame.mixer.Sound("click.mp3")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Pause on Esc key
                    self.paused = not self.paused  # Toggle pause state
            elif event.type == pygame.MOUSEBUTTONDOWN and self.paused:
                mouse_pos = pygame.mouse.get_pos()
                resume_button, restart_button, quit_button = self.render_pause_menu()

                if resume_button.collidepoint(mouse_pos):
                    click_sound.play()
                    self.paused = False  # Resume the game
                elif restart_button.collidepoint(mouse_pos):
                    click_sound.play()
                    self.restart_game()  # Restart the game
                elif quit_button.collidepoint(mouse_pos):
                    click_sound.play()
                    self.is_running = False  # Quit the game
                    main_menu()
            elif event.type == self.power_end_event:
                self.power_active = False
                for spook in self.spooks:
                    spook.set_frightened(False)
        keys = pygame.key.get_pressed()
        if self.player:
            if keys[pygame.K_UP]:
                self.player.set_dir(Directions.NORTH)
            elif keys[pygame.K_LEFT]:
                self.player.set_dir(Directions.WEST)
            elif keys[pygame.K_DOWN]:
                self.player.set_dir(Directions.SOUTH)
            elif keys[pygame.K_RIGHT]:
                self.player.set_dir(Directions.EAST)

        if not self.paused:  # Only process movement keys if the game is not paused
            keys = pygame.key.get_pressed()
            if self.player:
                if keys[pygame.K_UP]:
                    self.player.set_dir(Directions.NORTH)
                elif keys[pygame.K_LEFT]:
                    self.player.set_dir(Directions.WEST)
                elif keys[pygame.K_DOWN]:
                    self.player.set_dir(Directions.SOUTH)
                elif keys[pygame.K_RIGHT]:
                    self.player.set_dir(Directions.EAST)



    def render_pause_menu(self):
        

        # Draw a semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Black with 50% opacity
        self.screen.blit(overlay, (0, 0))

        # Draw the pause menu title
        font = pygame.font.SysFont("Chiller", 72)
        text_surface = font.render("Paused", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.width / 2, self.height / 2 - 100))
        self.screen.blit(text_surface, text_rect)

        
        resume_button = pygame.Rect(self.width / 2 - 100, self.height / 2, 200, 50)
        restart_button = pygame.Rect(self.width / 2 - 100, self.height / 2 + 70, 200, 50)
        quit_button = pygame.Rect(self.width / 2 - 100, self.height / 2 + 140, 200, 50)

       
        mouse_pos = pygame.mouse.get_pos()
        for btn in [resume_button, restart_button, quit_button]:
            if btn.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (150, 150, 255), btn)  # Hover color
            else:
                pygame.draw.rect(self.screen, (85, 85, 255), btn)  # Normal color

        # Draw button labels
        font = pygame.font.SysFont("Arial", 36)
        self.screen.blit(font.render("Resume", True, (255, 255, 255)), (resume_button.x + 50, resume_button.y))
        self.screen.blit(font.render("Restart", True, (255, 255, 255)), (restart_button.x + 50, restart_button.y))
        self.screen.blit(font.render("Quit", True, (255, 255, 255)), (quit_button.x + 70, quit_button.y))


        return resume_button, restart_button, quit_button
    

    def restart_game(self):
        # Reset game state
        self.objects = []
        self.dots = []
        self.spooks = []
        self.energizers = []
        self.walls = []
        self.score = 0
        self.lives = 3
        self.paused = False
        self.victory = False
        self.power_active = False

        # Reinitialize the game
        controller = MazeController()
        game_size = controller.size
        self.screen = pygame.display.set_mode((game_size[0] * CELL_SIZE, game_size[1] * CELL_SIZE))

        
        for y, row in enumerate(controller.grid):
            for x, col in enumerate(row):
                if col == 0:
                    self.add_wall(Wall(self, x, y, CELL_SIZE))

        for dot_pos in controller.dot_positions:
            screen_pos = cell_to_pixel(dot_pos, CELL_SIZE)
            self.add_dot(Dot(self, screen_pos[0] + CELL_SIZE // 2, screen_pos[1] + CELL_SIZE // 2))

        for energizer_pos in controller.energizer_positions:
            screen_pos = cell_to_pixel(energizer_pos, CELL_SIZE)
            self.add_energizer(Energizer(self, screen_pos[0] + CELL_SIZE // 2, screen_pos[1] + CELL_SIZE // 2))

        for i, spook_spawn in enumerate(controller.spook_spawns):
            screen_pos = cell_to_pixel(spook_spawn, CELL_SIZE)
            spook = Spook(self, screen_pos[0], screen_pos[1], CELL_SIZE, controller, controller.spook_sprites[i % len(controller.spook_sprites)])
            self.add_spook(spook)

        # Recreate the player
        self.player = Player(self, CELL_SIZE, CELL_SIZE, CELL_SIZE)
        self.set_player(self.player)





class Pathfinder:
    def __init__(self, grid):
        self.pathfinder = tcod.path.AStar(cost=np.array(grid, dtype=np.bool_).tolist(), diagonal=0)

    def find_path(self, from_x, from_y, to_x, to_y):
        path = self.pathfinder.get_path(from_x, from_y, to_x, to_y)
        return [(y, x) for x, y in path]


# Класс для управления лабиринтом
class MazeController:
    def __init__(self):
        self.layout = [
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "X     O      XX       O  S X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X X    X            X    X X",
            "X X XX X XXXXXXXXXX X XX X X",
            "X X XX X XXXXXXXXXX X XX X X",
            "X X XX X     XX     X XX X X",
            "X       XXXX XX XXXX       X",
            "XXXXXXX XXXX XX XXXX XXXXXXX",
            "    O                       ",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "X S    XX    XX    XX    S X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X O    XX          XX   O  X",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "X  S O       XX       O    X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X   XX     X    X     XX   X",
            "XXX XX X            X XX XXX",
            "XXX XX X XXXX  XXXX X XX XXX",
            "X   S    X        X     S  X",
            "X XXXXXX X        X XXXXXX X",
            "X        X    S   X        X",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]
        self.grid = []
        self.dot_positions = []
        self.energizer_positions = []
        self.walkable_positions = []
        self.spook_spawns = []
        self.spook_sprites = [ "images/spook_pink.png","images/spook_red.png","images/spook_yellow.png","images/spook_orange.png","images/spook_green.png","images/spook_purple.png","images/spook_blue.png",]
        self.size = (0, 0)
        self.convert_layout()
        self.pathfinder = Pathfinder(self.grid)
        

    def request_random_path(self, spook):
        target = random.choice(self.walkable_positions)
        current_pos = pixel_to_cell(spook.get_pos())
        path = self.pathfinder.find_path(current_pos[1], current_pos[0], target[1], target[0])
        spook.set_path([cell_to_pixel(loc) for loc in path])

    def convert_layout(self):
        for x, row in enumerate(self.layout):
            self.size = (len(row), x + 1)
            binary_row = []
            for y, col in enumerate(row):
                if col == "S":
                    self.spook_spawns.append((y, x))
                if col == "X":
                    binary_row.append(0)
                else:
                    binary_row.append(1)
                    self.dot_positions.append((y, x))
                    self.walkable_positions.append((y, x))
                    if col == "O":
                        self.energizer_positions.append((y, x))
            self.grid.append(binary_row)
        


def start_pacman_game():

    pygame.init()
    controller = MazeController()
    game_size = controller.size
    game = GameManager(game_size[0] * CELL_SIZE, game_size[1] * CELL_SIZE)

    # Добавление стен
    for y, row in enumerate(controller.grid):
        for x, col in enumerate(row):
            if col == 0:
                game.add_wall(Wall(game, x, y, CELL_SIZE))
    

    for dot_pos in controller.dot_positions:
        screen_pos = cell_to_pixel(dot_pos, CELL_SIZE)
        game.add_dot(Dot(game, screen_pos[0] + CELL_SIZE // 2, screen_pos[1] + CELL_SIZE // 2))

    for energizer_pos in controller.energizer_positions:
        screen_pos = cell_to_pixel(energizer_pos, CELL_SIZE)
        game.add_energizer(Energizer(game, screen_pos[0] + CELL_SIZE // 2, screen_pos[1] + CELL_SIZE // 2))

    for i, spook_spawn in enumerate(controller.spook_spawns):
        screen_pos = cell_to_pixel(spook_spawn, CELL_SIZE)
        spook = Spook(game, screen_pos[0], screen_pos[1], CELL_SIZE, controller, controller.spook_sprites[i % len(controller.spook_sprites)])
        game.add_spook(spook)

    # Create player
    player = Player(game, CELL_SIZE, CELL_SIZE, CELL_SIZE)
    game.set_player(player)

    # Запуск игры
    game.start(60)


def save_score(new_score):
    current_score = load_score()
    total_score = current_score + new_score
    with open("score.txt", "w") as file:
        file.write(str(total_score))


def load_score():
    try:
        with open("score.txt", "r") as file:
            return int(file.read())
    except FileNotFoundError:
        return 0



def win(score):
    save_score(score)
    WIDTH, HEIGHT = 960, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    exit_button = ImageButton((WIDTH / 2) - (252 / 2), 420, 252, 74, "Exit", "green_button2.jpg", "green_button2_hover.jpg", "click.mp3")

    running = True
    while running:
        screen.fill((0, 0, 0))  # Clear screen
        screen.blit(main_background, (0, 0))  # Draw background

        # Draw the menu title
        font = pygame.font.SysFont("Chiller", 150)
        text_surface = font.render("YOU WIN", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WIDTH / 2, 150))
        screen.blit(text_surface, text_rect)


        # Display the score
        score_font = pygame.font.SysFont("Chiller", 50)
        score_surface = score_font.render(f"Final Score: {score}", True, (255, 255, 255))
        score_rect = score_surface.get_rect(center=(WIDTH / 2, 250))
        screen.blit(score_surface, score_rect)

        


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.USEREVENT and event.button == exit_button:
                running = False
                fade(screen)
                main_menu()


            # Handle button events
            for btn in [exit_button]:
                btn.handle_event(event)

        # Update and draw all buttons
        for btn in [ exit_button]:
            btn.check_hover(pygame.mouse.get_pos())
            btn.draw(screen)


        # Update the display
        pygame.display.flip()

def fail(score):
    save_score(score)
    WIDTH, HEIGHT = 960, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    exit_button = ImageButton((WIDTH / 2) - (252 / 2), 420, 252, 74, "Exit", "green_button2.jpg", "green_button2_hover.jpg", "click.mp3")


    running = True
    while running:
        screen.fill((0, 0, 0))  # Clear screen
        screen.blit(main_background, (0, 0))  # Draw background

        # Draw the menu title
        font = pygame.font.SysFont("Chiller", 100)
        text_surface = font.render("Game Over", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WIDTH / 2, 130))
        screen.blit(text_surface, text_rect)

        # Display the score
        score_font = pygame.font.SysFont("Chiller", 50)
        score_surface = score_font.render(f"Final Score: {score}", True, (255, 255, 255))
        score_rect = score_surface.get_rect(center=(WIDTH / 2, 250))
        screen.blit(score_surface, score_rect)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.USEREVENT and event.button == exit_button:
                print("Button 'Start' was clicked")
                fade(screen)
                main_menu()



            # Handle button events
            for btn in [exit_button]:
                btn.handle_event(event)

        # Update and draw all buttons
        for btn in [exit_button]:
            btn.check_hover(pygame.mouse.get_pos())
            btn.draw(screen)


        # Update the display
        pygame.display.flip()

def startup():
    play_button = ImageButton(300, 320, 350, 100, "Play", "green_button2.jpg", "green_button2_hover.jpg", "click.mp3")
    
    running = True
    while running:
        screen.fill((0, 0, 0))  # Clear screen
        screen.blit(main_background, (0,0))  # Draw background

        # Draw the menu title
        font = pygame.font.SysFont("Chiller", 150)
        text_surface = font.render("START GAME", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WIDTH / 2, 200))
        screen.blit(text_surface, text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()


            if event.type == pygame.USEREVENT and event.button == play_button:
                print("Button 'Start' was clicked")
                fade(screen)
                main_menu()
                

            # Handle button events
            for btn in [play_button]:
                btn.handle_event(event)

        # Update and draw all buttons
        for btn in [play_button]:
            btn.check_hover(pygame.mouse.get_pos())
            btn.draw(screen)


        # Update the display
        pygame.display.flip()



def main_menu():
    WIDTH, HEIGHT = 960, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    start_button = ImageButton((WIDTH / 2) - (252 / 2), 220, 252, 74, "New Game", "green_button2.jpg", "green_button2_hover.jpg","click.mp3")
    about_button = ImageButton((WIDTH / 2) - (252 / 2), 320, 252, 74, "About", "green_button2.jpg", "green_button2_hover.jpg", "click.mp3")
    exit_button = ImageButton((WIDTH / 2) - (252 / 2), 420, 252, 74, "Exit", "green_button2.jpg", "green_button2_hover.jpg", "click.mp3")

    running = True
    while running:
        screen.fill((0, 0, 0))  # Clear screen
        screen.blit(main_background, (0, 0))  # Draw background

        # Draw the menu title
        font = pygame.font.SysFont("Chiller", 100)
        text_surface = font.render("Danger Zone", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WIDTH / 2, 130))
        screen.blit(text_surface, text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.USEREVENT and event.button == start_button:
                print("Button 'New Game' was clicked") 
                fade(screen)
                new_game()   

            if event.type == pygame.USEREVENT and event.button == about_button:
                print("Button 'About' was clicked")
                fade(screen)
                about_menu()


                for btn in [start_button, about_button, exit_button]:
                    btn.set_pos(WIDTH/2 -(252/2))

            if event.type == pygame.USEREVENT and event.button == exit_button:
                running = False
                print("Button 'Exit' was clicked")
                pygame.quit()
                sys.exit()

            # Handle button events
            for btn in [start_button, about_button, exit_button]:
                btn.handle_event(event)

        # Update and draw all buttons
        for btn in [start_button, about_button, exit_button]:
            btn.check_hover(pygame.mouse.get_pos())
            btn.draw(screen)


        # Update the display
        pygame.display.flip()

def about_menu():
    WIDTH, HEIGHT = 960, 600
    saved_score = load_score()
    back_button = ImageButton((WIDTH / 2) - (252 / 2), 460, 252, 74, "Back", "green_button2.jpg", "green_button2_hover.jpg", "click.mp3")

    running = True
    while running:
        screen.fill((0, 0, 0))  # Clear screen
        screen.blit(main_background, (0, 0))  # Draw background

        # Draw the settings title
        font = pygame.font.SysFont("Chiller", 72)
        text_surface = font.render("ABOUT", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WIDTH / 2, 100))
        screen.blit(text_surface, text_rect)

        score_font = pygame.font.SysFont("Chiller", 50)
        score_surface = score_font.render(f"Final Score: {saved_score}", True, (255, 255, 255))
        score_rect = score_surface.get_rect(center=(WIDTH / 2, 250))
        screen.blit(score_surface, score_rect)
     

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            if event.type == pygame.USEREVENT:
                if event.button == back_button:
                    fade(screen) 
                    running = False
                    print("Button 'Back' was clicked")

                  
            # Handle button events
            for btn in [back_button]:
                btn.handle_event(event)
                

        # Update and draw all buttons
        for btn in [ back_button]:
            btn.check_hover(pygame.mouse.get_pos())
            btn.draw(screen)


        # Update the display
        pygame.display.flip()


def new_game():
    WIDTH, HEIGHT = 960, 600
    start_button = ImageButton((WIDTH / 2) - (252 / 2), 320, 252, 74, "Start", "green_button2.jpg", "green_button2_hover.jpg", "click.mp3")
    back_button = ImageButton((WIDTH / 2) - (252 / 2), 420, 252, 74, "Back", "green_button2.jpg", "green_button2_hover.jpg", "click.mp3")
    running = True
    while running:
        screen.fill((0, 0, 0))
        screen.blit(main_background, (0,0))

        font = pygame.font.SysFont("Chiller", 100)
        text_surface = font.render("Welcome to the game", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WIDTH/2, 200))
        screen.blit(text_surface, text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            if event.type == pygame.USEREVENT and event.button == start_button:
                print("Button 'Start' was clicked")
                fade(screen)
                start_pacman_game()


            if event.type == pygame.USEREVENT and event.button == back_button:
                fade(screen)
                running = False
                print("Button 'Back' was clicked")

                

            for btn in [start_button, back_button]:
                btn.handle_event(event)
        

        for btn in [start_button, back_button]:
            btn.check_hover(pygame.mouse.get_pos())
            btn.draw(screen)


        pygame.display.flip()


if __name__ == "__main__":
    
    startup()
