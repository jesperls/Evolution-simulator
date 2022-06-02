import pygame
from robit import *
import random
import os
import threading
import time

WORLD_SIZE = (1024, 1024)
SPAWN_PELLET = pygame.USEREVENT + 1


class World(object):
    def __init__(self, config):
        pygame.init()
        self.screen = pygame.display.set_mode(WORLD_SIZE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.SysFont("monospace", 15)
        self.agents = pygame.sprite.Group()
        self.pellets = pygame.sprite.Group()
        self.config = config
        self.spawn_pellets(100)
        pygame.time.set_timer(SPAWN_PELLET, 1000)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == SPAWN_PELLET:
                    self.spawn_pellet()
            self.update_agents()
            if len(self.agents) < 10:
                genome = RobitGenome(1)
                genome.configure_new(self.config.genome_config)
                self.agents.add(RobotAgent(genome, self.config, random.randint(0, WORLD_SIZE[0]), random.randint(0, WORLD_SIZE[1])))
            self.render()

    def close(self):
        pygame.quit()
    
    def render(self):
        self.screen.fill((0, 0, 0))
        self.draw_pellets()
        self.draw_agents()
        pygame.display.flip()
        if len(self.pellets) < 75:
            self.spawn_pellets(1)
        # self.clock.tick(20)
    
    def draw_agents(self):
        for agent in self.agents:
            self.screen.blit(agent.image, agent.rect)
            for b in agent.bullets:
                self.screen.blit(b.image, b.rect)
            for r in agent.vision_rects:
                pygame.draw.rect(self.screen, (255, 0, 0), r, 1)
            
            pygame.draw.line(self.screen, (255, 0, 0), (int(agent.rect.center[0]-agent.width), int(agent.rect.center[1]-agent.height-4)), (int(agent.rect.center[0]+agent.width), int(agent.rect.center[1]-agent.height-4)), 1)
            pygame.draw.line(self.screen, (200, 200, 0), (int(agent.rect.center[0]-agent.width), int(agent.rect.center[1]-agent.height)), (int(agent.rect.center[0]+(agent.stamina/100)*agent.width*2-agent.width), int(agent.rect.center[1]-agent.height)), 1)
            pygame.draw.line(self.screen, (0, 255, 0), (int(agent.rect.center[0]-agent.width), int(agent.rect.center[1]-agent.height-4)), (int(agent.rect.center[0]+(agent.health/100)*agent.width*2-agent.width), int(agent.rect.center[1]-agent.height-4)), 1)

    def draw_pellets(self):
        for pellet in self.pellets:
            self.screen.blit(pellet.image, pellet.rect)
    
    def spawn_pellets(self, amount):
        for i in range(amount):
            self.spawn_pellet()
    
    def spawn_pellet(self, size = 20):
        self.pellets.add(Pellet(random.randint(0, WORLD_SIZE[0]-20), random.randint(0, WORLD_SIZE[1]-20), size))

    def update_agents(self):
        threads = []
        for agent in self.agents:
            threads.append(threading.Thread(target=self.update_agent, args=(agent,)))
            threads[-1].start()
        
        for thread in threads:
            thread.join()

    def update_agent(self, agent): #TODO CONSIDER ADDING THREAD SAFETY
        self.get_agent_action(agent)
        agent.update()

        if agent.health <= 0 or agent.idle_timer > 60:
            pygame.sprite.Sprite.kill(agent)
            # self.agents.add(PlayerAgent(random.randint(0, WORLD_SIZE[0] - 20), random.randint(0, WORLD_SIZE[1] - 20)))

        for i in self.pellets:
            pellet = pygame.sprite.collide_mask(agent, i)
            if pellet:
                pygame.sprite.Sprite.kill(i)
                agent.change_stamina(i.size*2)
                # agent.change_health(5)
        
        for i in self.agents:
            if i != agent and agent.collide(i) and agent.type == "robot" and i.type == "robot" and agent.breeding_cooldown == 0 and i.breeding_cooldown == 0:
                agent.genome.fitness += 10
                i.breeding_cooldown = 500
                agent.breeding_cooldown = 500
                genetic_distance = agent.genome.distance(i.genome, self.config.genome_config) * 1.5
                agent.change_health(-genetic_distance)
                i.change_health(-genetic_distance)
                genome = RobitGenome(1)
                genome.configure_crossover(agent.genome, i.genome, self.config.genome_config)
                baby = RobotAgent(genome, self.config, agent.rect.center[0], agent.rect.center[1])
                baby.stamina = min((agent.stamina + i.stamina) / 2 + 20, 100)
                self.agents.add(baby)

                

    def get_agent_action(self, agent):
        if agent.type == "player":
            agent.get_action(pygame.key.get_pressed())
        else:
            agent.vision_rects = []
            vision = agent.vision(self.pellets)
            vision.extend(agent.vision(self.agents))
            vision.extend([agent.rotation, agent.stamina, agent.health, agent.breeding_cooldown])
            agent.get_action(vision)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                        neat.DefaultSpeciesSet, neat.DefaultStagnation,
                        config_path)
    world = World(config)

    world.agents.add(PlayerAgent(random.randint(0, WORLD_SIZE[0]), random.randint(0, WORLD_SIZE[1])))
    # for i in range(10):
    #     genome = RobitGenome(i)
    #     genome.configure_new(config.genome_config)
    #     world.agents.add(RobotAgent(genome, config, random.randint(0, WORLD_SIZE[0]), random.randint(0, WORLD_SIZE[1])))

    world.run()
    world.close()