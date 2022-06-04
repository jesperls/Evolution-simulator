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
        self.lifetime = 10
    
    def update(self):
        self.rect.x += round(self.speed * math.cos(self.rotation))
        self.rect.y -= round(self.speed * math.sin(self.rotation))
        self.lifetime -= 1

class Pellet(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        super().__init__()
        self.type = "pellet"
        self.image = pygame.image.load("Assets/Images/Pellet/pellet2.png")
        self.image = pygame.transform.scale(self.image, (20, 20))
        self.width, self.height = self.image.get_size()
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = x
        self.rect.y = y
        self.size = size

class Agent(pygame.sprite.Sprite):
    def __init__(self, x, y, everything, global_bullets):
        super().__init__()
        self.origin_image = pygame.image.load("Assets/Images/agent/Ship.png")
        self.origin_image = pygame.transform.scale(self.origin_image, (20, 15))
        self.everything = everything
        self.global_bullets = global_bullets
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
        self.vision_range = 10
        self.cooldown = 0
        self.breeding_cooldown = 0
        self.idle_timer = 0
        self.bullets = []
        self.vision_rects = []
        self.memory = [0 for _ in range(10)]
    
    def move_forward(self, speed):
        self.rect.x += round(speed * math.cos(self.rotation))
        self.rect.y -= round(speed * math.sin(self.rotation))
        self.change_stamina(-abs(speed)/60)
    
    def update_color(self):
        self.color = (int(0+(100-self.stamina)*2.55), int(self.stamina*2.55), 0)
    
    def shoot(self):
        self.stamina -= 10
        if self.cooldown <= 0:
            bullet = Bullet(self.rect.center[0], self.rect.center[1], self.rotation)
            self.bullets.append(bullet)
            self.everything.add(bullet)
            self.global_bullets.add(bullet)
            self.cooldown = 50

    def rotate(self, angle):
        self.rotation += math.radians(angle)
        if self.rotation > math.pi*2:
            self.rotation -= math.pi*2
        if self.rotation < 0:
            self.rotation += math.pi*2
        self.update_mask()
        self.change_stamina(-0.03)
    
    def update_mask(self):
        self.image = pygame.transform.rotate(self.origin_image, self.rotation*180/math.pi)
        self.rot_rect = self.image.get_rect()
        self.rot_rect.center = self.rect.center
        self.rect = self.rot_rect

    def change_stamina(self, amount):
        self.stamina += amount
        if self.stamina > 100:
            self.stamina = 100
        if self.stamina < 0:
            self.stamina = 0
            self.change_health(amount)

    def change_health(self, amount):
        self.health += amount
        if self.health > 100:
            self.health = 100
    
    def update(self):
        for b in self.bullets:
            b.update()
            if b.lifetime <= 0:
                self.bullets.remove(b)
                pygame.sprite.Sprite.kill(b)

        if self.cooldown > 0:
            self.cooldown -= 1
        if self.breeding_cooldown > 0:
            self.breeding_cooldown -= 1
        if self.stamina <= 0: 
            self.health -= 0.5

        self.change_stamina(-0.01)
        self.got_shot()

        if self.rect.x > 1024 - self.rect.width:
            self.rect.x = 1024 - self.rect.width
        if self.rect.x < 0:
            self.rect.x = 0
        if self.rect.y > 1024 - self.rect.height:
            self.rect.y = 1024 - self.rect.height
        if self.rect.y < 0:
            self.rect.y = 0
        
        if self.type == "robot":
            self.genome.fitness += 0.01

    def vision(self, sprites):
        # vision = []
        walls = []
        agents = []
        pellets = []
        bullets = []
        scan_sprite = pygame.sprite.Sprite()
        scan_sprite.rect = pygame.Rect(0, 0, 10, 10)
        for i in np.arange(0, 360, 22.5):
            hit = self.get_ray(i, scan_sprite, sprites)
            if hit == 0:
                walls.append(0)
                agents.append(0)
                pellets.append(0)
                bullets.append(0)
            elif hit == 1:
                walls.append(1)
                agents.append(0)
                pellets.append(0)
                bullets.append(0)
            elif hit == 2:
                walls.append(0)
                agents.append(0)
                pellets.append(1)
                bullets.append(0)
            elif hit == 3:
                walls.append(0)
                agents.append(0)
                pellets.append(0)
                bullets.append(1)
            elif hit > 3:
                walls.append(hit)
                agents.append(0)
                pellets.append(0)
                bullets.append(0)
            
            # vision.append(self.get_ray(i, scan_sprite, sprites))
        return walls + agents + bullets + pellets
    
    def get_ray(self, angle, scan_sprite, sprites):
        angle = math.radians(angle) + self.rotation
        x = self.rect.center[0] - scan_sprite.rect.width/2
        y = self.rect.center[1] - scan_sprite.rect.height/2
        x_delta = round(scan_sprite.rect.width * math.cos(angle) * 1.5)
        y_delta = round(scan_sprite.rect.width * math.sin(angle) * 1.5)
        for _ in range(self.vision_range):
            x += x_delta
            y -= y_delta
            scan_sprite.rect.center = (x, y)
            sprite = pygame.sprite.spritecollideany(scan_sprite, sprites)
            # self.vision_rects.append(pygame.Rect(x, y, scan_sprite.rect.width, scan_sprite.rect.height))
            if sprite != None and sprite != self:
                # self.vision_rects.append(pygame.Rect(x, y, scan_sprite.rect.width, scan_sprite.rect.height))
                if sprite.type == "robot":
                    return self.genome.distance(sprite.genome, self.config.genome_config) + 10
                elif sprite.type == "bullet":
                    return 3
                else:
                    return 2
            if scan_sprite.rect.x < 0 or scan_sprite.rect.x + scan_sprite.rect.width > 1024 or scan_sprite.rect.y < 0 or scan_sprite.rect.y + scan_sprite.rect.height > 1024:
                # self.vision_rects.append(pygame.Rect(x, y, scan_sprite.rect.width, scan_sprite.rect.height))
                return 1
        return 0
    
    def collide(self, other):
        if pygame.sprite.collide_mask(self, other):
            return True
        return False
    
    def got_shot(self):
        bullet = pygame.sprite.spritecollideany(self, self.global_bullets)
        if bullet != None and bullet not in self.bullets:
            self.change_health(-50)
            return True
        return False
    
    def collide_agent(self, others):
        other = pygame.sprite.spritecollideany(self, others)
        if other and other != self and self.type == "robot" and other.type == "robot":
            return other
        return False

    def breed(self, partner):
        self.genome.fitness += 10
        partner.breeding_cooldown = 1000
        self.breeding_cooldown = 1000
        genetic_distance = self.genome.distance(partner.genome, self.config.genome_config)
        self.change_health(-genetic_distance * 1.5)
        partner.change_health(-genetic_distance * 1.5)
        genome = RobitGenome(1)
        genome.configure_crossover(self.genome, partner.genome, self.config.genome_config)
        baby = RobotAgent(genome, self.config, self.rect.center[0], self.rect.center[1], self.everything, self.global_bullets)
        baby.stamina = min((self.stamina + partner.stamina) / 2, 100)
        return baby
    
    def kill(self):
        for b in self.bullets:
            pygame.sprite.Sprite.kill(b)
        pygame.sprite.Sprite.kill(self)

class RobotAgent(Agent):
    def __init__(self, genome, config, x, y, everything, global_bullets):
        super().__init__(x, y, everything, global_bullets)
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
        # elif output[1] > 30:
        #     self.move_forward(-self.speed)
        #     idle = False
        if output[1] > 30:
            self.rotate(5)
            idle = False
        if output[2] > 30:
            self.rotate(-5)
            idle = False
        if output[3] > 30:
            self.shoot()
            idle = False
        self.memory = output[4:14]

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