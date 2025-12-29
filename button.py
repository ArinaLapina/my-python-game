import pygame

import sys
import time

FPS_CLOCK = pygame.time.Clock()
MAX_FPS = 60



class ImageButton:
    def __init__(self, x, y, width, height, text, image_path, hover_image_path=None, sound_path=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

        # Load the normal and hover images
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (width, height))
        self.hover_image = self.image
        if hover_image_path:
            self.hover_image = pygame.image.load(hover_image_path)
            self.hover_image = pygame.transform.scale(self.hover_image, (width, height))

        # Define the button rectangle
        self.rect = self.image.get_rect(topleft=(x, y))

        # Load sound if provided
        self.sound = None
        if sound_path:
            self.sound = pygame.mixer.Sound(sound_path)

        self.is_hovered = False

    def set_pos(self, x, y = None):
        self.x = x
        self.rect = self.image.get_rect(topleft=(self.x, self.y))


    def draw(self, screen):
        current_image = self.hover_image if self.is_hovered else self.image
        screen.blit(current_image, self.rect.topleft)

        # Draw the text on the button if provided
        if self.text:
            font = pygame.font.Font(None, 36)
            text_surface = font.render(self.text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            if self.sound:
                self.sound.play()
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, button=self))



def fade(screen):
    fade_duration = 0.05  # Time for the fade (seconds)
    start_time = time.time()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Get screen size
        screen_width, screen_height = screen.get_size()

        # Work out how much time has passed
        elapsed_time = time.time() - start_time
        fade_alpha = min(255, int((elapsed_time / fade_duration) * 255))

        # Make a black surface for fading
        fade_surface = pygame.Surface((screen_width, screen_height))
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(fade_alpha)

        # Clear screen and apply fade
        screen.fill((0, 0, 0))
        screen.blit(fade_surface, (0, 0))

        pygame.display.flip()
        FPS_CLOCK.tick(60)  # Limit frame rate

        # Stop when fade is done
        if fade_alpha >= 255:
            running = False




