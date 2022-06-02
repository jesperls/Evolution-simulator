import pygame
from robit import *
import random
import os

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
        self.everything = pygame.sprite.Group()
        self.config = config
        # self.spawn_pellets(100)
        # pygame.time.set_timer(SPAWN_PELLET, 1000)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == SPAWN_PELLET:
                    self.spawn_pellet()
            if len(self.pellets) < 150:
                self.spawn_pellets(100-len(self.pellets))
            if len(self.agents) < 10:
                genome = RobitGenome(1)
                genome.configure_new(self.config.genome_config)
                new_agent = RobotAgent(genome, self.config, random.randint(0, WORLD_SIZE[0]), random.randint(0, WORLD_SIZE[1]))
                self.agents.add(new_agent)
                self.everything.add(new_agent)
            self.update_agents()
            self.render()

    def close(self):
        pygame.quit()
    
    def render(self):
        self.screen.fill((0, 0, 0))
        self.draw_pellets()
        self.draw_agents()
        pygame.display.flip()
        # self.clock.tick(20)
    
    def draw_agents(self):
        for agent in self.agents:
            self.screen.blit(agent.image, agent.rect)
            for b in agent.bullets:
                self.screen.blit(b.image, b.rect)
            for r in agent.vision_rects:
                pygame.draw.rect(self.screen, (0, 255, 0), r, 1)
            
            pygame.draw.line(self.screen, (255, 0, 0), (int(agent.rect.center[0]-agent.width), int(agent.rect.center[1]-agent.height-4)), (int(agent.rect.center[0]+agent.width), int(agent.rect.center[1]-agent.height-4)), 1)
            pygame.draw.line(self.screen, (0, 255, 0), (int(agent.rect.center[0]-agent.width), int(agent.rect.center[1]-agent.height-4)), (int(agent.rect.center[0]+(agent.health/100)*agent.width*2-agent.width), int(agent.rect.center[1]-agent.height-4)), 1)
            if agent.stamina > 0:
                pygame.draw.line(self.screen, (200, 200, 0), (int(agent.rect.center[0]-agent.width), int(agent.rect.center[1]-agent.height)), (int(agent.rect.center[0]+(agent.stamina/100)*agent.width*2-agent.width), int(agent.rect.center[1]-agent.height)), 1)

    def draw_pellets(self):
        for pellet in self.pellets:
            self.screen.blit(pellet.image, pellet.rect)
    
    def spawn_pellets(self, amount):
        for i in range(amount):
            self.spawn_pellet()
    
    def spawn_pellet(self, size = 20):
        pellet = Pellet(random.randint(0, WORLD_SIZE[0]-20), random.randint(0, WORLD_SIZE[1]-20), size)
        self.pellets.add(pellet)
        self.everything.add(pellet)

    def update_agents(self):
        for agent in self.agents:
            self.update_agent(agent)

    def update_agent(self, agent):
        self.get_agent_action(agent)
        agent.update()

        if agent.health <= 0 or agent.idle_timer > 60:
            pygame.sprite.Sprite.kill(agent)
            return

        pellet = pygame.sprite.spritecollideany(agent, self.pellets)
        if pellet:
            agent.change_stamina(pellet.size*2)
            pygame.sprite.Sprite.kill(pellet)
        
        partner = agent.collide_agent(self.agents)
        if partner and agent.breeding_cooldown == 0 and partner.breeding_cooldown == 0:
            self.agents.add(agent.breed(partner))

    def get_agent_action(self, agent):
        if agent.type == "player":
            agent.get_action(pygame.key.get_pressed())
        else:
            agent.vision_rects = []
            vision = agent.vision(self.everything)
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