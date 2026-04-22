import pygame
import random
import math
from resources import ResourceManager
from config import GLOBAL_SCALE

_SCREEN_CENTER = pygame.math.Vector2(600, 400)
_SQUARE_SURF_CACHE = {}

class SquareParticle:
    __slots__ = ['pos', 'vel', 'size', 'color', 'alpha', 'lifetime', 'max_lifetime',
                 'gravity', 'rotation', 'rot_speed', '_surf', 'use_additive']

    def __init__(self, pos, vel, size=8, color=(255, 255, 255), alpha=255,
                 lifetime=0.6, gravity=200.0, rot_speed=None, use_additive=False):
        self.pos      = pygame.math.Vector2(pos)
        self.vel      = pygame.math.Vector2(vel)
        self.size     = size
        self.color    = color
        self.alpha    = float(alpha)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity  = gravity
        self.rotation = random.uniform(0, 360)
        self.rot_speed = rot_speed if rot_speed is not None else random.uniform(-180, 180)
        self.use_additive = use_additive
        self._surf    = None

    def _make_surf(self):
        s = max(1, int(self.size * GLOBAL_SCALE))
        key = (s, self.color)
        if key not in _SQUARE_SURF_CACHE:
            raw = pygame.Surface((s, s), pygame.SRCALPHA)
            raw.fill((*self.color, 255))
            _SQUARE_SURF_CACHE[key] = raw
        self._surf = _SQUARE_SURF_CACHE[key]

    def is_alive(self): return self.lifetime > 0

    def update(self, dt):
        self.lifetime -= dt
        self.pos      += self.vel * dt
        self.vel.y    += self.gravity * dt
        self.vel      *= 0.95
        self.rotation += self.rot_speed * dt

    def draw(self, screen, camera):
        if self.lifetime <= 0: return
        target = camera + _SCREEN_CENTER
        draw_pos = (self.pos - target) * GLOBAL_SCALE + _SCREEN_CENTER
        
        # Viewport Culling
        if draw_pos.x + 20 < 0 or draw_pos.x - 20 > screen.get_width() or draw_pos.y + 20 < 0 or draw_pos.y - 20 > screen.get_height():
            return
            
        ratio  = self.lifetime / self.max_lifetime
        alpha  = int(self.alpha * ratio)
        if self._surf is None: self._make_surf()
        
        self._surf.set_alpha(alpha)
        rect = self._surf.get_rect(center=(draw_pos.x, draw_pos.y))
        flags = pygame.BLEND_RGB_ADD if self.use_additive else 0
        screen.blit(self._surf, rect, special_flags=flags)

class TexturedParticle(SquareParticle):
    __slots__ = ['texture_name', '_orig_img']
    def __init__(self, texture_name, pos, vel, size=32, alpha=255, lifetime=0.6, gravity=0.0, rot_speed=None, use_additive=False):
        super().__init__(pos, vel, size, (255,255,255), alpha, lifetime, gravity, rot_speed, use_additive)
        self.texture_name = texture_name
        self._orig_img = None

    def _make_surf(self):
        img = ResourceManager.get_instance().get_texture(self.texture_name)
        if img:
            s = max(1, int(self.size * GLOBAL_SCALE))
            self._orig_img = pygame.transform.scale(img, (s, s))
            self._surf = self._orig_img
        else:
            # Fallback
            super()._make_surf()

    def draw(self, screen, camera):
        if self.lifetime <= 0: return
        target = camera + _SCREEN_CENTER
        draw_pos = (self.pos - target) * GLOBAL_SCALE + _SCREEN_CENTER
        
        # Viewport Culling
        if draw_pos.x + 40 < 0 or draw_pos.x - 40 > screen.get_width() or draw_pos.y + 40 < 0 or draw_pos.y - 40 > screen.get_height():
            return
            
        ratio  = self.lifetime / self.max_lifetime
        alpha  = int(self.alpha * ratio)
        if self._surf is None: self._make_surf()
        if self._orig_img:
            rotated = pygame.transform.rotate(self._orig_img, self.rotation)
            rotated.set_alpha(alpha)
            
            rect = rotated.get_rect(center=(draw_pos.x, draw_pos.y))
            flags = pygame.BLEND_RGB_ADD if self.use_additive else 0
            screen.blit(rotated, rect, special_flags=flags)
        else:
            super().draw(screen, camera)

class ParticleManager:
    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None: cls._instance = ParticleManager()
        return cls._instance

    def __init__(self):
        self._particles = []

    def spawn(self, pos, count=8, color=(255, 220, 80), alpha=255, size_range=(4, 12), 
              speed_range=(60, 300), lifetime=0.5, gravity=250.0, spread=360, texture_name=None, use_additive=False):
        for _ in range(count):
            angle = math.radians(random.uniform(0, spread))
            speed = random.uniform(*speed_range)
            vel = pygame.math.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
            size = random.randint(*size_range)
            lt = lifetime * random.uniform(0.6, 1.2)
            if texture_name:
                self._particles.append(TexturedParticle(texture_name, pos, vel, size, alpha, lt, gravity, use_additive=use_additive))
            else:
                self._particles.append(SquareParticle(pos, vel, size, color, alpha, lt, gravity, use_additive=use_additive))

    def spawn_directional(self, pos, direction_angle, count=6, color=(255, 255, 255), 
                          alpha=255, size_range=(3, 8), speed_range=(80, 250), 
                          spread_deg=60, lifetime=0.4, gravity=200.0, texture_name=None, use_additive=False):
        for _ in range(count):
            angle = direction_angle + random.uniform(-spread_deg / 2, spread_deg / 2)
            rad = math.radians(angle)
            speed = random.uniform(*speed_range)
            vel = pygame.math.Vector2(math.cos(rad) * speed, math.sin(rad) * speed)
            size = random.randint(*size_range)
            lt = lifetime * random.uniform(0.6, 1.2)
            if texture_name:
                self._particles.append(TexturedParticle(texture_name, pos, vel, size, alpha, lt, gravity, use_additive=use_additive))
            else:
                self._particles.append(SquareParticle(pos, vel, size, color, alpha, lt, gravity, use_additive=use_additive))

    def update(self, dt):
        self._particles[:] = [p for p in self._particles if p.is_alive()]
        for p in self._particles: p.update(dt)

    def draw(self, screen, camera):
        for p in self._particles: p.draw(screen, camera)

    def clear(self): self._particles.clear()
