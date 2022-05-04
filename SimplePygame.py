import pygame
import yaml
import os
import sys
import random


class SimplePygame:

    class NoConfigFileException(Exception):
        pass

    # Class that enables simplified access to the config values
    class Config:
        def __init__(self, filename):
            try:
                ymlfile = open(filename, "r")
                self.config = yaml.safe_load(ymlfile)
                ymlfile.close()
            except FileNotFoundError:
                raise SimplePygame.NoConfigFileException

        def has_value(self, section, key):
            if (section in self.config):
                if (self.config[section] is not None and
                        key in self.config[section]):
                    return True
            return False

        def get_value(self, section, key):
            if (self.has_value(section, key)):
                return self.config[section][key]

            return None

    # Base class for our sprites (inherits from Pygame Sprite)
    # Uses adapted animated sprite code from:
    # https://www.simplifiedpython.net/pygame-sprite-animation-tutorial/
    class Sprite(pygame.sprite.Sprite):
        def __init__(self,
                     name,
                     x_size,
                     y_size,
                     x_start,
                     y_start,
                     max_frames_per_second,
                     movement_amount,
                     max_fps,
                     hit_behaviour):
            
            super().__init__()
            self.name = name
            self.x = x_start
            self.y = y_start
            self.movement_amount = movement_amount
            self.x_size = x_size
            self.y_size = y_size
            self.direction = 1
            self.hit_behaviour = hit_behaviour
            self.x_start = x_start
            self.y_start = y_start

            self.images = []

            # Load in all the images files for this sprite
            files = os.listdir(name)
            for f in files:
                if (f.endswith(".png")):
                    self.images.append(pygame.image.load(self.name+'/'+f))

            self.image_index = 0
            self.tick = 0

            # Enables control over how quickly the sprite animaes
            self.max_tick = max_fps/max_frames_per_second

            self.image = self.images[self.image_index]
            self.rect = pygame.Rect(x_start, y_start, x_size, y_size)

        # Enables sprite animation
        def update(self):
            self.tick += 1
            if (self.tick >= self.max_tick):
                self.tick = 0
                # when the update method is called, we will increment the index
                self.image_index += 1

                # if the index is larger than the total images
                if self.image_index >= len(self.images):
                    # we will make the index to 0 again
                    self.image_index = 0

                # finally we will update the image that will be displayed
                self.image = self.images[self.image_index]

        def draw(self, game_window):
            self.update()
            game_window.blit(self.image, self.rect)

        # Move the sprite following the config rules
        def move(self, max_x, max_y):
            if (self.movement_amount.startswith("random")):
                (a, b) = self.movement_amount.split(" ")
                amount_x = random.randint(-int(b), int(b))
                amount_y = random.randint(-int(b), int(b))

            elif (self.movement_amount.startswith("updown")):
                amount_x = 0
                (a, b) = self.movement_amount.split(" ")

                if (self.direction == 1 and
                        (self.y + int(b) + self.y_size > max_y)):
                    self.direction = -1
                elif (self.direction == -1 and
                        (self.y - int(b) < 0)):
                    self.direction = 1

                amount_y = (self.direction * int(b))
                
            elif (self.movement_amount.startswith("wave")):
                amount_x = 0
                (a, b) = self.movement_amount.split(" ")

                if (self.direction == 1 and
                        (self.y + int(b) + self.y_size > max_y)):
                    self.direction = -1
                elif (self.direction == -1 and
                        (self.y - int(b) < 0)):
                    self.direction = 1

                amount_y = (self.direction * int(b))
                amount_x = -int(b)

                # If we are going to go off the left side of the screen
                if (self.x + amount_x <=0):
                    # Change it by the -current x (so 0), plus width of screen
                    # minus x size of sprite - therefore move to right side of
                    # screen
                    amount_x = -self.x + max_x - self.x_size

            self.x += amount_x
            self.y += amount_y
            
            # Actually move the sprite
            self.rect.move_ip(amount_x, amount_y)

        def has_collided(self, check_against):
            if self.rect.colliderect(check_against.rect):
                return self.hit_behaviour
            return None
             
        def reset_position(self):
            self.x = self.x_start
            self.y = self.y_start
            self.rect = pygame.Rect(self.x_start, self.y_start, self.x_size, self.y_size)
            
    # Sprites that use user input to decide movement
    # Inherits from our Sprite base class
    class ControllableSprite(Sprite):
        def __init__(self,
                     name,
                     x_size,
                     y_size,
                     x_start,
                     y_start,
                     max_frames_per_second,
                     movement_amount,
                     max_fps,
                     hit_behaviour,
                     lives):
            
            super().__init__(name,
                             x_size,
                             y_size,
                             x_start,
                             y_start,
                             max_frames_per_second,
                             movement_amount,
                             max_fps,
                             hit_behaviour)
            self.lives = int(lives)

        # Enable movement based on keypresses
        # TODO: Respect config settings for which keysets to use
        def control(self, pressed_keys):
            if pressed_keys[pygame.K_LEFT]:
                self.x -= self.movement_amount
                self.rect.move_ip(-self.movement_amount, 0)
            if pressed_keys[pygame.K_RIGHT]:
                self.x += self.movement_amount
                self.rect.move_ip(self.movement_amount, 0)
            if pressed_keys[pygame.K_UP]:
                self.y -= self.movement_amount
                self.rect.move_ip(0, -self.movement_amount)
            if pressed_keys[pygame.K_DOWN]:
                self.y += self.movement_amount
                self.rect.move_ip(0, self.movement_amount)

        def reduce_life(self):
            self.lives -= 1

        def is_dead(self):
            return self.lives <= 0
        
    def __init__(self, autorun=False):
        self.enemies = []
        pygame.init()

    # Load the configuration and set up some variables for us to use
    def load_configuration(self, filename="simplepygame.yml"):
        self.config = SimplePygame.Config(filename)
        self.display = pygame.display
        self.clock = pygame.time.Clock()
        if (self.config.has_value("general", "max_fps")):
            self.max_fps = self.config.get_value("general", "max_fps")
        else:
            self.max_fps = 60

        # Create a window the requested size or full screen if no size set
        if (self.config.has_value("general", "screen_width") and
                self.config.has_value("general", "screen_height")):
            self.surface = pygame.display.set_mode(
                (self.config.get_value("general", "screen_width"),
                 self.config.get_value("general", "screen_height")))
        else:
            self.surface = pygame.display.set_mode()

        if (self.config.has_value("general", "title")):
            pygame.display.set_caption(
                self.config.get_value("general", "title"))

        self.screen_width = pygame.display.Info().current_w
        self.screen_height = pygame.display.Info().current_h

        # Set a background image if one is defined
        if (self.config.has_value("general", "background_image")):
            self.background = pygame.image.load(
                self.config.get_value("general", "background_image"))
        else:
            self.background = None

        self.should_score = self.config.get_value("general", "score")
        self.font = pygame.font.SysFont(None, 24)
        if (self.config.has_value("general", "start_score")):
            self.score = int(self.config.get_value("general", "start_score"))
        else:
            self.score = 0

    def update_score(self, delta):
        self.score += delta

    # Display the score
    # TODO: Respect more than just top-right
    def display_score(self):
        if (self.should_score is not None):
            score_img = self.font.render('Score: '+str(self.score), True, (255, 255, 255))
            if (self.should_score == "top-right"):
                x = self.screen_width-150
                y = 10
                
            self.surface.blit(score_img, (x, y))

    # Display the number of lives
    # TODO: Respect more than just top-left
    def display_lives(self):
      if (self.config.get_value("general", "lives") is not None):
            lives_img = self.font.render('Lives: '+str(self.player.lives), True, (255, 255, 255))
            if (self.config.get_value("general", "lives") == "top-left"):
                x = 20
                y = 10
                
            self.surface.blit(lives_img, (x, y))
        
    # Create all the sprites as per the config file            
    def setup_sprites(self):
        # Only try to create a player if it is in the config file
        if (self.config.has_value("player", "x_size")):
                self.player = SimplePygame.ControllableSprite(
                    "player",
                    self.config.get_value("player", "x_size"),
                    self.config.get_value("player", "y_size"),
                    self.config.get_value("player", "x_start"),
                    self.config.get_value("player", "y_start"),
                    self.config.get_value("player", "max_frames_per_second"),
                    self.config.get_value("player", "movement_amount"),
                    self.max_fps,
                    self.config.get_value("player", "hit"),
                    self.config.get_value("player", "lives"))

        # Only try to create enemies if they are in the config file
        if (self.config.has_value("general", "enemy_types")):
            # Go through each enemy type.  In the config file, they should
            # be in a section called enemyn where n is 1,2,3 etc.
            # Up to the number in General - enemy_types
            for n in range(1,
                        int(self.config.get_value("general", "enemy_types"))+1):
                # Each enemy type can have multiple enemies of
                # that type so create them
                if (self.config.has_value("enemy"+str(n), "number")):
                    for m in range(
                            int(self.config.get_value("enemy"+str(n), "number"))):
                        x_start = self.config.get_value("enemy"+str(n), "x_start")
                        if (x_start == "random"):
                            x_start = random.randint(0, self.screen_width)
                        y_start = self.config.get_value("enemy"+str(n), "y_start")
                        if (y_start == "random"):
                            y_start = random.randint(0, self.screen_height)

                        self.enemies.append(SimplePygame.Sprite(
                            "enemy"+str(n),
                            self.config.get_value("enemy"+str(n), "x_size"),
                            self.config.get_value("enemy"+str(n), "y_size"),
                            x_start,
                            y_start,
                            self.config.get_value("enemy"+str(n),
                                            "max_frames_per_second"),
                            self.config.get_value("enemy"+str(n),
                                            "movement_amount"),
                            self.max_fps,
                            self.config.get_value("enemy"+str(n), "hit")))

    # Performs the pygame main loop - get events, process movement, draw sprites
    def main_loop(self):
        while self.player.is_dead() == False:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            pressed_keys = pygame.key.get_pressed()
            if (pressed_keys is not None):
                self.player.control(pressed_keys)

            if (self.background is not None):
                self.surface.blit(self.background, (0, 0))
            else:
                self.surface.fill((255, 255, 255))
            self.update_score(1)
            self.display_score()
            self.display_lives()
            self.player.draw(self.surface)

            for e in self.enemies:
                e.move(self.screen_width, self.screen_height)
                col = e.has_collided(self.player)
                if (col is not None):
                    if (col == "die"):
                        self.player.lives = 0
                    elif (col == "reduce-life"):
                        self.player.reduce_life()
                        self.player.reset_position()
                        
                e.draw(self.surface)

            # Actually update the screen
            self.display.flip()
            self.clock.tick(self.max_fps)

        pygame.quit()
        sys.exit()
            
    # Convenience method to run the other methods in the correct order
    def go(self):
        simple.load_configuration()
        simple.setup_sprites()
        simple.main_loop()

simple = SimplePygame()
simple.go()
