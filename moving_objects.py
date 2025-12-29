import pygame
from game_objects import GameObject

from constants import Directions
from constants import Points




# Функции для перевода координат
def pixel_to_cell(pos, size=24):
    return pos[0] // size, pos[1] // size

def cell_to_pixel(pos, size=24):
    return pos[0] * size, pos[1] * size

# Класс для движущихся объектов
class MovingObject(GameObject):
    def __init__(self, game, x, y, size, color=(255, 0, 0), is_round=False):
        super().__init__(game, x, y, size, color, is_round)
        self.dir = Directions.NONE
        self.buffered_dir = Directions.NONE
        self.last_valid_dir = Directions.NONE
        self.path = []
        self.target = None
        self.sprite = pygame.image.load('images/ghost.png')
        self.move_delay = 1
        self.move_count = 0

    def get_target(self):
        return None if not self.path else self.path.pop(0)

    def set_dir(self, direction):
        self.dir = direction
        self.buffered_dir = direction

    def hits_wall(self, pos):
        collision_rect = pygame.Rect(pos[0], pos[1], self.size, self.size)
        for wall in self.game.get_walls():
            if collision_rect.colliderect(wall.get_rect()):
                return True
        return False

    def check_move(self, direction):
        if direction == Directions.NORTH:
            next_pos = (self.x, self.y - 1)
        elif direction == Directions.SOUTH:
            next_pos = (self.x, self.y + 1)
        elif direction == Directions.WEST:
            next_pos = (self.x - 1, self.y)
        elif direction == Directions.EAST:
            next_pos = (self.x + 1, self.y)
        else:
            next_pos = (0, 0)
        return self.hits_wall(next_pos), next_pos

    def move(self, direction):
        if self.move_count < self.move_delay:
            self.move_count += 1
            return
        self.move_count = 0

        if direction == Directions.NORTH:
            self.set_pos(self.x, self.y - 1)
        elif direction == Directions.SOUTH:
            self.set_pos(self.x, self.y + 1)
        elif direction == Directions.WEST:
            self.set_pos(self.x - 1, self.y)
        elif direction == Directions.EAST:
            self.set_pos(self.x + 1, self.y)

    def update(self):
        self.reach_target()
        self.move(self.dir)

    def reach_target(self):
        pass

    def render(self):
        self.sprite = pygame.transform.scale(self.sprite, (24, 24))
        self.screen.blit(self.sprite, self.get_rect())
        

class Player(MovingObject):
    def __init__(self, game, x, y, size):
        super().__init__(game, x, y, size, (255, 255, 0), False)
        self.prev_pos = (0, 0)
        self.open = pygame.image.load("images/pacman1.png")
        self.closed = pygame.image.load("images/pacman2.png")
        self.sprite = self.open
        self.mouth_open = True
        self.animation_timer = 0
        self.animation_delay = 10  # Задержка между сменами кадров анимации
        self.move_delay = 0  # Уменьшили задержку для увеличения скорости
        self.move_count = 0

    def update(self):
        if self.x < 0:
            self.x = self.game.width
        if self.x > self.game.width:
            self.x = 0
        self.prev_pos = self.get_pos()
        if self.check_move(self.buffered_dir)[0]:
            self.move(self.dir)
        else:
            self.move(self.buffered_dir)
            self.dir = self.buffered_dir
        if self.hits_wall((self.x, self.y)):
            self.set_pos(*self.prev_pos)
        self.collect_dots()
        self.handle_spooks()

        # Анимация рта
        self.animation_timer += 1
        if self.animation_timer >= self.animation_delay:
            self.animation_timer = 0
            self.mouth_open = not self.mouth_open

    def move(self, direction):
        if self.move_count < self.move_delay:
            self.move_count += 1
            return
        self.move_count = 0

        collision = self.check_move(direction)
        if not collision[0]:
            self.last_valid_dir = self.dir
            self.set_pos(*collision[1])
        else:
            self.dir = self.last_valid_dir                
                        

    def collect_dots(self):
        collision_rect = pygame.Rect(self.x, self.y, self.size, self.size)
        dots = self.game.get_dots()
        energizers = self.game.get_energizers()
        objects = self.game.get_objects()

        for dot in dots:
            if collision_rect.colliderect(dot.get_rect()) and dot in objects:
                objects.remove(dot)
                self.game.increase_score(Points.DOT)
                dots.remove(dot)
                break

        if not dots:
            self.game.set_victory()

        for energizer in energizers:
            if collision_rect.colliderect(energizer.get_rect()) and energizer in objects:
                objects.remove(energizer)
                self.game.increase_score(Points.ENERGIZER)
                self.game.set_power(True)
                
    def handle_spooks(self):
        collision_rect = pygame.Rect(self.x, self.y, self.size, self.size)
        spooks = self.game.get_spooks()
        objects = self.game.get_objects()
        for spook in spooks:
            if collision_rect.colliderect(spook.get_rect()) and spook in objects:
                if self.game.is_power_active():
                    objects.remove(spook)
                    self.game.increase_score(Points.SPOOK)
                else:
                    if not self.game.get_victory():
                        self.game.lose_life()           
                
    
    def render(self):
        self.sprite = self.open if self.mouth_open else self.closed
        self.sprite = pygame.transform.rotate(self.sprite, self.dir)
        super().render()


class Spook(MovingObject):
    def __init__(self, game, x, y, size, controller, sprite="images/ghost_fright.png"):
        super().__init__(game, x, y, size)
        self.controller = controller
        self.normal = pygame.image.load(sprite)
        self.fright = pygame.image.load("images/ghost_fright.png")
        self.speed = 0.5
        self.target = None
        self.path = []

    def set_path(self, path):
        self.path = path
        self.target = self.path.pop(0) if self.path else None

    def reach_target(self):
        if self.target is None or (self.x, self.y) == self.target:
            self.update_target()

        if self.target:
            self.move_towards_target()

    def set_frightened(self, frightened):
        self.frightened = frightened
        if self.frightened:
            self.speed = 0.4
        else:
            self.speed = 0.5

    def update_target(self):
        if self.game.get_mode() == "CHASE" and not self.game.is_power_active():
            self.request_path_to_player()
        else:
            self.controller.request_random_path(self)

    def request_path_to_player(self):
        player_pos = pixel_to_cell(self.game.get_player_pos())
        current_pos = pixel_to_cell(self.get_pos())
        path = self.controller.pathfinder.find_path(current_pos[1], current_pos[0], player_pos[1], player_pos[0])
        if path:
            self.set_path([cell_to_pixel(loc) for loc in path])

    def move_towards_target(self):
        if self.target:
            target_x, target_y = self.target
            dx = target_x - self.x
            dy = target_y - self.y

            if dx != 0:
                self.x += self.speed if dx > 0 else -self.speed
            if dy != 0:
                self.y += self.speed if dy > 0 else -self.speed

            if abs(self.x - target_x) < self.speed and abs(self.y - target_y) < self.speed:
                self.x, self.y = target_x, target_y
                self.target = self.path.pop(0) if self.path else None

    def move(self, direction):
        pass

    def render(self):
        self.sprite = self.fright if self.game.is_power_active() else self.normal
        super().render()

    

   