import pygame
import math
import random
from entity import Node
from config import GetSnakeHeadConfig, GetSnakeBodyConfig
from particle import ParticleManager

class Snake:
    def __init__(self, startPos, config):
        self.config = config
        self.MaxVelocity = getattr(config, 'velocity', 350.0)
        self.BodyLength = getattr(config, 'length', 15.0)
        self.nodes = [Node(startPos) for _ in range(getattr(config, 'size', 10))]
        
        # Scaling logic constant
        self.scale_logic = getattr(config, 'scale_logic', 4.0)
        
        if self.nodes:
            head_cfg = getattr(config, 'headConfig', None)
            if head_cfg: self.nodes[0].apply_config(head_cfg)
            self.nodes[0].scaleMultiplier = getattr(config, 'headSize', 0.5)
            
        for i in range(1, len(self.nodes)):
            shrinkRatio = getattr(config, 'headSize', 0.5) - 0.1 - (i / len(self.nodes)) * 0.1
            self.nodes[i].position = pygame.math.Vector2(startPos) 
            body_cfg = getattr(config, 'bodyConfig', None)
            if body_cfg: self.nodes[i].apply_config(body_cfg)
            self.nodes[i].scaleMultiplier = shrinkRatio

        if self.nodes:
            head_node = self.nodes[0]
            for i, node in enumerate(self.nodes):
                node.snake_head = head_node
                node.snake_depth = i

    def GetPosition(self):
        return self.nodes[0].position if self.nodes else pygame.math.Vector2(0,0)

    def GetHead(self):
        return self.nodes[0] if self.nodes else None

    def attract(self, target_node, Smoothing):
        if not self.nodes or not target_node: return
        offset = target_node.position - self.nodes[0].position
        if offset.length_squared() > 0:
            TargetSpeed = offset.normalize() * (self.MaxVelocity if Smoothing >= 0 else -self.MaxVelocity)
            self.nodes[0].direction = self.nodes[0].direction.lerp(TargetSpeed, abs(Smoothing))

    def process(self, dt):
        if not self.nodes: return
        
        # Allow for a custom behavior override if defined in config
        update_func = getattr(self.config, 'custom_update', None)
        if update_func:
            update_func(self, dt)
            return

        self._handle_death_propagation(dt)
        self._update_movement(dt)
        self._update_body_trailing(dt)
        self._emit_particles(dt)

    def _handle_death_propagation(self, dt):
        num_nodes = len(self.nodes)
        death_damage = getattr(self.config, 'death_damage', 400.0)
        for i in range(num_nodes - 1):
            curr_node = self.nodes[i]
            next_node = self.nodes[i+1]
            if curr_node and curr_node.Hp <= 0:
                if next_node:
                    next_node.Hp -= death_damage * dt

    def _update_movement(self, dt):
        head = self.nodes[0]
        move_vec = head.direction + head.velocity
        if move_vec.length_squared() > 0.01:
            head.angle = math.degrees(math.atan2(move_vec.y, move_vec.x))

    def _update_body_trailing(self, dt):
        push_force = getattr(self.config, 'push_force', 50.0)
        lerp_factor = getattr(self.config, 'lerp_factor', 0.5)
        
        for i in range(1, len(self.nodes)):
            curr, prev = self.nodes[i], self.nodes[i-1]
            desired_dist = self.BodyLength * self.scale_logic * curr.scaleMultiplier
            offset = curr.position - prev.position
            dist = offset.length()
            
            if dist > desired_dist:
                target_pos = prev.position + (offset / dist) * desired_dist
                curr.position = curr.position.lerp(target_pos, lerp_factor)
                
                if dist > 0.1:
                    curr.angle = math.degrees(math.atan2(-offset.y, -offset.x))
            
            if dist < desired_dist * 0.8 and dist > 0:
                push_dir = offset / dist
                curr.velocity += push_dir * push_force * dt

    def _emit_particles(self, dt):
        head = self.nodes[0]
        speed_sq = head.direction.length_squared()
        if speed_sq > 5000:
            pm = ParticleManager.get_instance()
            
            head_particle_chance = getattr(self.config, 'head_particle_chance', 0.4)
            if random.random() < head_particle_chance:
                pm.spawn(
                    pos         = head.position,
                    count       = 1,
                    color       = getattr(self.config, 'head_particle_color', (40, 160, 60)),
                    alpha       = getattr(self.config, 'particle_alpha', 120),
                    size_range  = getattr(self.config, 'particle_size_range', (2, 5)),
                    speed_range = (10, 50),
                    lifetime    = 0.3,
                    gravity     = 80.0,
                )
                
            if len(self.nodes) > 2:
                body_particle_chance = getattr(self.config, 'body_particle_chance', 0.2)
                if random.random() < body_particle_chance:
                    rand_node = self.nodes[random.randint(1, len(self.nodes) - 1)]
                    pm.spawn(
                        pos         = rand_node.position,
                        count       = 1,
                        color       = getattr(self.config, 'body_particle_color', (30, 130, 50)),
                        alpha       = getattr(self.config, 'particle_alpha', 120) - 40,
                        size_range  = (2, 4),
                        speed_range = (5, 30),
                        lifetime    = 0.2,
                        gravity     = 60.0,
                    )

    def draw_shadow(self, screen, camera):
        if not self.nodes: return
        for i in range(len(self.nodes) - 1, -1, -1):
            self.nodes[i].draw_shadow(screen, camera)

    def draw_outline(self, screen, camera):
        if not self.nodes: return
        for i in range(len(self.nodes) - 1, -1, -1):
            self.nodes[i].draw_outline(screen, camera)

    def draw_sprite(self, screen, camera):
        if not self.nodes: return
        for i in range(len(self.nodes) - 1, -1, -1):
            self.nodes[i].draw_sprite(screen, camera)
