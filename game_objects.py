import pygame


# Основной класс для объектов
class GameObject:
    def __init__(self, game, x, y, size, color=(255, 0, 0), is_round=False):
        self.size = size
        self.game = game
        self.screen = game.screen
        self.x = x
        self.y = y
        self.color = color
        self.is_round = is_round

    def render(self):
        if self.is_round:
            pygame.draw.circle(self.screen, self.color, (self.x, self.y), self.size)
        else:
            pygame.draw.rect(self.screen, self.color, pygame.Rect(self.x, self.y, self.size, self.size), border_radius=1)

    def update(self):
        pass

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def set_pos(self, x, y):
        self.x = x
        self.y = y

    def get_pos(self):
        return self.x, self.y

# Класс для стен
class Wall(GameObject):
    def __init__(self, game, x, y, size, color=(85, 85, 255)):
        super().__init__(game, x * size, y * size, size, color)

class Dot(GameObject):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, 3, (200, 255, 0), True)


class Energizer(GameObject):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, 6, (125, 249, 255), True)

