import neat
import keyboard
import numpy as np
import math
from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    QUIT,
    K_SPACE,
)
import pygame
import numpy as np
import time


class RobitGenome(neat.DefaultGenome):
    def __init__(self, key):
        super().__init__(key)

    def configure_new(self, config):
        super().configure_new(config)

    def configure_crossover(self, genome1, genome2, config):
        super().configure_crossover(genome1, genome2, config)

    def mutate(self, config):
        super().mutate(config)

    def distance(self, other, config):
        dist = super().distance(other, config)
        return dist

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, rotation):
        super().__init__()
        self.rotation = rotation
        self.type = "bullet"
        self.image = pygame.image.load("Assets/Images/agent/bullet.png")
        self.image = pygame.transform.scale(self.image, (10, 10))
        self.image = pygame.transform.rotate(self.image, self.rotation*180/math.pi)
        self.rect = self.image.get_rect()
        self.rect.x = x-5
        self.rect.y = y-5
        self.speed = 10
        self.lifetime = 50
    
    def update(self):
        self.rect.x += round(self.speed * math.cos(self.rotation))
        self.rect.y -= round(self.speed * math.sin(self.rotation))
        self.lifetime -= 1

class Pellet(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        super().__init__()
        self.type = "pellet"
        # self.surf = pygame.Surface((10, 10))
        self.image = pygame.image.load("Assets/Images/Pellet/pellet.png")
        self.image = pygame.transform.scale(self.image, (20, 20))
        self.width, self.height = self.image.get_size()
        # self.surf.fill((255, 255, 0))
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = x
        self.rect.y = y
        self.size = size

class Agent(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # self.surf = pygame.Surface((10, 10))
        self.origin_image = pygame.image.load("Assets/Images/agent/Ship.png")
        self.origin_image = pygame.transform.scale(self.origin_image, (20, 15))
        self.image = self.origin_image
        self.rect = self.image.get_rect()
        self.width, self.height = self.image.get_size()
        self.mask = pygame.mask.from_surface(self.image)
        self.color = (0, 255, 0)
        self.rect.x = x
        self.rect.y = y
        self.rotation = 0
        self.speed = 3
        self.health = 100
        self.stamina = 100
        self.vision_range = 5
        self.cooldown = 0
        self.breeding_cooldown = 0
        self.idle_timer = 0
        self.bullets = []
        self.vision_rects = []
    
    def move_forward(self, speed):
        self.rect.x += round(speed * math.cos(self.rotation))
        self.rect.y -= round(speed * math.sin(self.rotation))
        self.change_stamina(-abs(speed)/30)
    
    def update_color(self):
        self.color = (int(0+(100-self.stamina)*2.55), int(self.stamina*2.55), 0)
    
    def shoot(self):
        if self.cooldown <= 0:
            self.bullets.append(Bullet(self.rect.center[0], self.rect.center[1], self.rotation))
            self.cooldown = 10
            self.stamina -= 5

    def rotate(self, angle):
        self.rotation += math.radians(angle)
        if self.rotation > math.pi*2:
            self.rotation -= math.pi*2
        if self.rotation < 0:
            self.rotation += math.pi*2
        self.image = pygame.transform.rotate(self.origin_image, self.rotation*180/math.pi)
        self.rot_rect = self.image.get_rect()
        self.rot_rect.center = self.rect.center
        self.rect = self.rot_rect
        self.change_stamina(-0.1)

    def change_stamina(self, amount):
        self.stamina += amount
        if self.stamina > 100:
            self.stamina = 100
        if self.stamina < 0:
            self.stamina = 0

    def change_health(self, amount):
        self.health += amount
        if self.health > 100:
            self.health = 100
    
    # def get_rotated(self):
    #     self.rot_image = pygame.transform.rotate(self.image, self.rotation*180/math.pi)
    #     self.rot_rect = self.rot_image.get_rect()
    #     self.rot_rect.center = self.rect.center
    #     return self.rot_image, self.rot_rect
    
    def update(self):
        for b in self.bullets:
            b.update()
            if b.lifetime <= 0:
                self.bullets.remove(b)
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.breeding_cooldown > 0:
            self.breeding_cooldown -= 1
        self.change_stamina(-0.01)
        if self.stamina <= 0: 
            self.health -= 1

        if self.rect.x > 1024 - self.rect.width:
            self.rect.x = 1024 - self.rect.width
        if self.rect.x < 0:
            self.rect.x = 0
        if self.rect.y > 1024 - self.rect.height:
            self.rect.y = 1024 - self.rect.height
        if self.rect.y < 0:
            self.rect.y = 0
    
    def vision(self, sprites):
        vision = []
        # self.vision_rects = []
        # start = time.time()
        scan_sprite = pygame.sprite.Sprite()
        scan_sprite.rect = pygame.Rect(0, 0, 20, 20)
        for i in np.arange(0, 360, 22.5):
            vision.append(self.get_ray(i, scan_sprite, sprites))
        # print(time.time() - start)
        return vision
    
    def get_ray(self, angle, scan_sprite, sprites):
        angle = math.radians(angle)
        origin = self.rect.center
        x = self.rect.center[0] - scan_sprite.rect.width/2
        y = self.rect.center[1] - scan_sprite.rect.height/2
        x_delta = round(scan_sprite.rect.width * math.cos(angle) * 1.5)
        y_delta = round(scan_sprite.rect.width * math.sin(angle) * 1.5)
        for _ in range(self.vision_range):
            x += x_delta
            y -= y_delta
            scan_sprite.rect.center = (x, y)
            sprite = pygame.sprite.spritecollideany(scan_sprite, sprites)
            if sprite != None and sprite != self:
                # self.vision_rects.append(pygame.Rect(x, y, scan_sprite.rect.width, scan_sprite.rect.height))

                if sprite.type == "robot":
                    return self.genome.distance(sprite.genome, self.config.genome_config)
                else:
                    return 1
        return 0

            # for s in sprites:
            #     loops += 1
            #     # if x < s.rect.x + s.rect.width and x > s.rect.x and y < s.rect.y + s.rect.height and y > s.rect.y and s != self:
            #     if s.rect.collidepoint(x, y) and s != self:
            #         self.vision_rects.append(pygame.Rect(x-2.5, y-2.5, 5, 5))
            #         if s.type == "robot":
            #             self.rect.center = origin
            #             return self.genome.distance(s.genome, self.config.genome_config)
            #         else:
            #             self.rect.center = origin
                        # return 1
    
    def collide(self, other):
        if pygame.sprite.collide_mask(self, other):
            return True
        return False

class RobotAgent(Agent):
    def __init__(self, genome, config, x, y):
        super().__init__(x, y)
        self.type = "robot"
        self.genome = genome
        self.genome.fitness = 0
        self.config = config
        self.net = neat.nn.FeedForwardNetwork.create(genome, config)

    def get_action(self, observation):
        output = self.net.activate(observation)
        idle = True
        # print(output)
        if output[0] > 30:
            self.move_forward(self.speed)
            idle = False
        elif output[1] > 30:
            self.move_forward(-self.speed)
            idle = False
        if output[2] > 30:
            self.rotate(5)
            idle = False
        if output[3] > 30:
            self.rotate(-5)
            idle = False
        if idle:
            self.idle_timer += 1
        else:
            self.idle_timer = 0
        # if output[4] > 0:
        #     self.shoot()

class PlayerAgent(Agent):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.type = "player"

    def get_action(self, keys):
        idle = True
        if keys[K_UP]:
            self.move_forward(self.speed)
            idle = False
        if keys[K_DOWN]:
            self.move_forward(-self.speed)
            idle = False
        if keys[K_LEFT]:
            self.rotate(5)
            idle = False
        if keys[K_RIGHT]:
            self.rotate(-5)
            idle = False
        if keys[K_SPACE]:
            self.shoot()
        if keys[K_ESCAPE]:
            self.health = 0
        if idle:
            self.idle_timer += 1
        else:
            self.idle_timer = 0