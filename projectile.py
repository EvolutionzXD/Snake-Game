import pygame
import math
import random
from entity import Node

class ProjectileManager:
    @classmethod
    def Spawn(cls, pos, target_pos, config_func=None, speed=None, knockback_override=None, 
              stun_override=None, lifetime_override=None, damage_override=None, 
              inherited_velocity=None, alpha_override=None):
        from config import GetProjectileConfig
        if config_func is None:
            config_func = GetProjectileConfig
            
        proj = Node(pos)
        config = config_func()
        proj.apply_config(config)
        
        final_speed = speed if speed is not None else 1200.0
        
        if knockback_override is not None: proj.knockback = knockback_override
        if stun_override is not None:      proj.stun_on_hit = stun_override
        if damage_override is not None:    proj.damage = damage_override
        if lifetime_override is not None:  proj.lifetime = lifetime_override
        if alpha_override is not None:     proj.alpha = alpha_override
        
        direction = pygame.math.Vector2(target_pos) - pygame.math.Vector2(pos)
        if direction.length_squared() > 0:
            proj.velocity = direction.normalize() * final_speed
            if inherited_velocity is not None:
                proj.velocity += inherited_velocity
            
            proj.angle = math.degrees(math.atan2(proj.velocity.y, proj.velocity.x))
        
        if config.MaxFrame > 0:
            proj.frame = random.uniform(0, config.MaxFrame + 0.99)
            
        proj.invincibility = 0
        return proj
