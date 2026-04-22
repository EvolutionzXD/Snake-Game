import pygame
import random

class CameraShake:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CameraShake()
        return cls._instance
        
    def __init__(self):
        self.trauma = 0.0
        
    def add_trauma(self, amount):
        self.trauma = min(max(self.trauma, amount), 1.0)
        
    def update(self, dt):
        if self.trauma > 0:
            self.trauma = max(self.trauma - dt, 0.0)
            
    def get_offset(self):
        if self.trauma > 0:
            amount = self.trauma ** 2 * 20.0 # Rung tối đa 20 pixel
            return pygame.math.Vector2(random.uniform(-amount, amount), random.uniform(-amount, amount))
        return pygame.math.Vector2(0, 0)

class DamageNumber:
    def __init__(self, pos, amount, color=(255, 255, 100), size=50):
        self.position = pygame.math.Vector2(pos)
        self.velocity = pygame.math.Vector2(random.uniform(-30, 30), random.uniform(-150, -80))
        self.amount = amount
        self.lifetime = 0.8
        self.max_lifetime = 0.8
        self.color = color
        self.font = pygame.font.SysFont("Impact", size)
        
    def update(self, dt):
        self.lifetime -= dt
        self.position += self.velocity * dt
        self.velocity.y += 300 * dt # Trọng lực
        return self.lifetime > 0
        
    def draw(self, screen, camera):
        if self.lifetime <= 0: return
        if self.amount < 1: return
        # Tính toán tỉ lệ scale (nhảy vọt lúc đầu rồi thu nhỏ)
        progress = self.lifetime / self.max_lifetime
        # Hiệu ứng pop-in: to ra ở 20% đầu tiên
        if progress > 0.8:
            scale = 1.0 + (1.0 - progress) * 5.0 # Pop to gấp đôi
        else:
            scale = progress * 1.25 # Nhỏ dần về 0
            
        alpha = int(progress * 255)
        text = self.font.render(str(int(self.amount)), True, self.color)
        
        # Scale surface
        if scale != 1.0:
            w, h = text.get_size()
            text = pygame.transform.scale(text, (int(w * scale), int(h * scale)))
            
        # Viền chữ
        text_outline = self.font.render(str(int(self.amount)), True, (0, 0, 0))
        if scale != 1.0:
            text_outline = pygame.transform.scale(text_outline, (int(w * scale), int(h * scale)))
            
        text_outline.set_alpha(alpha)
        text.set_alpha(alpha)
        
        pos = self.position - camera
        rect = text.get_rect(center=(pos.x, pos.y))
        
        screen.blit(text_outline, (rect.x - 2, rect.y - 2))
        screen.blit(text_outline, (rect.x + 2, rect.y + 2))
        screen.blit(text, rect)

class EffectManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EffectManager()
        return cls._instance
        
    def __init__(self):
        self.damage_numbers = []
        self.hitstop_timer = 0.0 # Thời gian khựng hình
        
    def add_damage_number(self, pos, amount, color=(255, 255, 10), size=30):
        self.damage_numbers.append(DamageNumber(pos, amount, color, size))
        
    def trigger_hitstop(self, duration):
        """Làm game dừng lại trong duration giây"""
        self.hitstop_timer = duration

    def is_hitstopping(self):
        return self.hitstop_timer > 0

    def update_and_draw(self, dt, screen, camera):
        # Update hitstop timer
        if self.hitstop_timer > 0:
            self.hitstop_timer = max(0, self.hitstop_timer - dt)
            # Khi đang hitstop, ta có thể không update các hiệu ứng khác hoặc vẫn draw
            # Thường thì chỉ dừng logic game, hiệu ứng vẫn nên hiện ra

        for dn in self.damage_numbers[:]:
            if not dn.update(dt):
                self.damage_numbers.remove(dn)
            else:
                dn.draw(screen, camera)
