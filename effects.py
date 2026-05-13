import pygame
import random
from config import GLOBAL_SCALE

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
        """Thêm độ rung chấn cho màn hình (0.0 – 1.0), bị giới hạn tối đa là 1.0."""
        from settings import SettingsManager
        if not SettingsManager.get_instance().get("video", "screen_shake"):
            return
        self.trauma = min(max(self.trauma, amount), 1.0)
        
    def update(self, dt):
        """Giảm dần độ rung chấn theo thời gian."""
        if self.trauma > 0:
            self.trauma = max(self.trauma - dt, 0.0)
            
    def get_offset(self):
        """Trả về Vector2 offset ngẫu nhiên tứ lệ với trauma^2 để camera rung có cảm giác tự nhiên."""
        if self.trauma > 0:
            amount = self.trauma ** 2 * 20.0 # Rung tối đa 20 pixel
            return pygame.math.Vector2(random.uniform(-amount, amount), random.uniform(-amount, amount))
        return pygame.math.Vector2(0, 0)

class DamageNumber:
    def __init__(self, pos, amount, color=(255, 255, 100), size=50):
        from resources import ResourceManager
        self.position = pygame.math.Vector2(pos)
        self.velocity = pygame.math.Vector2(random.uniform(-30, 30), random.uniform(-150, -80))
        self.amount = amount
        self.lifetime = 0.8
        self.max_lifetime = 0.8
        self.color = color
        self.font = ResourceManager.get_instance().get_font("GrapeSoda", size)
        
    def update(self, dt):
        """Cập nhật vật lý số sát thương (truyền động lượng, trọng lực). Trả về False nếu đã hết thời gian tồn tại."""
        self.lifetime -= dt
        self.position += self.velocity * dt
        self.velocity.y += 300 * dt # Trọng lực
        return self.lifetime > 0
        
    def draw(self, screen, camera):
        """Vẽ số sát thương lên màn hình với hiệu ứng pop-in, mờ dần và viền chữ."""
        if self.lifetime <= 0: return
        if self.amount < 1: return
        # Tính toán tỉ lệ scale (nhảy vọt lúc đầu rồi thu nhỏ)
        progress = self.lifetime / self.max_lifetime
        # Hiệu ứng pop-in
        if progress > 0.8:
            scale = 1.0 + (1.0 - progress) * 5.0 
        else:
            scale = progress * 1.25 
            
        final_scale = scale * GLOBAL_SCALE
        alpha = int(progress * 255)
        text = self.font.render(str(int(self.amount)), True, self.color)
        
        # Scale surface
        w, h = text.get_size()
        text = pygame.transform.scale(text, (int(w * final_scale), int(h * final_scale)))
            
        # Viền chữ
        text_outline = self.font.render(str(int(self.amount)), True, (0, 0, 0))
        text_outline = pygame.transform.scale(text_outline, (int(w * final_scale), int(h * final_scale)))
            
        text_outline.set_alpha(alpha)
        text.set_alpha(alpha)
        
        center = pygame.math.Vector2(600, 400)
        target = camera + center
        pos = (self.position - target) * GLOBAL_SCALE + center
        
        rect = text.get_rect(center=(pos.x, pos.y))
        
        off = 2 * GLOBAL_SCALE
        screen.blit(text_outline, (rect.x - off, rect.y - off))
        screen.blit(text_outline, (rect.x + off, rect.y + off))
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
        """Sinh một số sát thương bay lên tại vị trí `pos` (chỉ hiển thị nếu cài đặt bật)."""
        from settings import SettingsManager
        if not SettingsManager.get_instance().get("gameplay", "show_damage_numbers"):
            return
        self.damage_numbers.append(DamageNumber(pos, amount, color, size))
        
    def trigger_hitstop(self, duration):
        """Làm game dừng lại trong duration giây"""
        self.hitstop_timer = duration

    def is_hitstopping(self):
        """Trả về True nếu hiện đang trong trạng thái khựng hình (hitstop_timer > 0)."""
        return self.hitstop_timer > 0

    def update_and_draw(self, dt, screen, camera):
        """Cập nhật bộ đếm HitStop và vẽ các số sát thương đang bay lên màn hình."""
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
