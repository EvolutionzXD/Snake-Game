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

class TextPopup:
    def __init__(self, text, pos, color, is_large=False):
        from resources import ResourceManager
        self.text = text
        self.position = pygame.math.Vector2(pos)
        self.color = color
        self.lifetime = 1.5
        self.max_lifetime = 1.5
        self.font = ResourceManager.get_instance().get_font("GrapeSoda", 100 if is_large else 45)
        self.vel = pygame.math.Vector2(0, -250) # Chữ bay nhanh lên trên
        
    def update(self, dt):
        self.lifetime -= dt
        self.position += self.vel * dt
        self.vel.y *= 0.95 # Giảm tốc dần
        return self.lifetime > 0
        
    def draw(self, screen, camera):
        alpha = int((self.lifetime / self.max_lifetime) * 255)
        text_surf = self.font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        
        center = pygame.math.Vector2(600, 400)
        target = camera + center
        pos = (self.position - target) * GLOBAL_SCALE + center
        rect = text_surf.get_rect(center=(pos.x, pos.y))
        
        # Vẽ bóng đổ cho chữ
        shadow = self.font.render(self.text, True, (0, 0, 0))
        shadow.set_alpha(alpha)
        screen.blit(shadow, (rect.x + 3, rect.y + 3))
        screen.blit(text_surf, rect)

class EffectManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EffectManager()
        return cls._instance
    def __init__(self):
        self.damage_numbers = []
        self.text_popups = [] # Danh sách thông báo chữ
        self.jackpot_aura_particles = [] # Danh sách hạt lửa jackpot
        self.hitstop_timer = 0.0 # Thời gian khựng hình
        self.time_stop_timer = 0.0 # Thời gian dừng thời gian
        
    def add_damage_number(self, pos, amount, color=(255, 255, 10), size=30):
        """Sinh một số sát thương bay lên tại vị trí `pos` (chỉ hiển thị nếu cài đặt bật)."""
        from settings import SettingsManager
        if not SettingsManager.get_instance().get("gameplay", "show_damage_numbers"):
            return
        self.damage_numbers.append(DamageNumber(pos, amount, color, size))
        
    def trigger_hitstop(self, duration):
        """Làm game dừng lại trong duration giây"""
        self.hitstop_timer = duration

    def trigger_time_stop(self, duration):
        """Kích hoạt hiệu ứng dừng thời gian (ZA WARUDO)"""
        self.time_stop_timer = duration

    def trigger_text_popup(self, text, pos, color=(255, 255, 255), is_large=False):
        """Hiện thông báo chữ (ví dụ 2 OF 3) trên màn hình."""
        self.text_popups.append(TextPopup(text, pos, color, is_large))

    def is_hitstopping(self):
        """Trả về True nếu hiện đang trong trạng thái khựng hình (hitstop_timer > 0)."""
        return self.hitstop_timer > 0

    def update_and_draw(self, dt, screen, camera):
        """Cập nhật bộ đếm HitStop, TimeStop và vẽ các hiệu ứng lên màn hình."""
        # Update timers
        if self.hitstop_timer > 0:
            self.hitstop_timer = max(0, self.hitstop_timer - dt)
            
        if self.time_stop_timer > 0:
            self.time_stop_timer = max(0, self.time_stop_timer - dt)
            # Hiệu ứng đóng băng không gian (Màu xám xanh mờ)
            overlay = pygame.Surface(screen.get_size())
            overlay.set_alpha(120) # Độ trong suốt
            overlay.fill((50, 50, 70)) 
            screen.blit(overlay, (0, 0))

        # --- VẼ RAINBOW VIGNETTE (JACKPOT) ---
        from weapon import WeaponManager
        from arsenal import TarotCardWeapon
        manager = WeaponManager.get_instance()
        tarot = manager.weapons.get("TarotCard")
        is_jackpot = tarot and getattr(tarot, "jackpot_timer", 0) > 0
        
        if is_jackpot:
            self._draw_rainbow_vignette(screen)
            self._update_and_draw_jackpot_aura(screen, dt)

        for dn in self.damage_numbers[:]:
            if not dn.update(dt):
                self.damage_numbers.remove(dn)
            else:
                dn.draw(screen, camera)
                
        for tp in self.text_popups[:]:
            if not tp.update(dt):
                self.text_popups.remove(tp)
            else:
                tp.draw(screen, camera)

    def _draw_rainbow_vignette(self, screen):
        import time, math
        t = time.time() * 4.0
        w, h = screen.get_size()
        
        # TỐI ƯU: Chỉ tạo 1 Surface duy nhất cho toàn bộ viền thay vì tạo trong vòng lặp
        vignette_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Vẽ dải mờ dần từ rìa vào (25 pixel)
        for i in range(25):
            alpha = int(120 * (1.0 - i/25)) # Càng vào trong càng mờ
            r = int(127 + 127 * math.sin(t + i*0.1))
            g = int(127 + 127 * math.sin(t + i*0.1 + 2))
            b = int(127 + 127 * math.sin(t + i*0.1 + 4))
            
            pygame.draw.rect(vignette_surf, (r, g, b, alpha), (i, i, w - i*2, h - i*2), 2)
            
        screen.blit(vignette_surf, (0, 0))

    def _update_and_draw_jackpot_aura(self, screen, dt):
        import random, math, time
        w, h = screen.get_size()
        t = time.time()
        
        # Sinh hạt lửa mới dọc đáy màn hình
        if len(self.jackpot_aura_particles) < 100: # Giới hạn số lượng hạt để mượt
            for _ in range(random.randint(1, 3)):
                self.jackpot_aura_particles.append({
                    'pos': [random.uniform(0, w), h + 30],
                    'vel': [random.uniform(-30, 30), random.uniform(-100, -300)],
                    'size': random.uniform(30, 70), # Hình tròn to
                    'life': 1.0,
                    'offset': random.uniform(0, 10)
                })
            
        for p in self.jackpot_aura_particles[:]:
            p['pos'][0] += p['vel'][0] * dt
            p['pos'][1] += p['vel'][1] * dt
            p['life'] -= dt * 0.7 
            
            if p['life'] <= 0 or p['pos'][1] < h - 300:
                self.jackpot_aura_particles.remove(p)
                continue
                
            # Màu sắc RGB đồng bộ
            alpha = int(p['life'] * 150)
            color_time = t * 4.0
            r = int(127 + 127 * math.sin(color_time))
            g = int(127 + 127 * math.sin(color_time + 2))
            b = int(127 + 127 * math.sin(color_time + 4))
            
            # VẼ Y HỆT AURA TRÊN GUI (2 lớp hình tròn đặc)
            current_size = p['size'] * p['life']
            # Lớp hào quang (To và mờ hơn)
            pygame.draw.circle(screen, (r, g, b, alpha // 2), (int(p['pos'][0]), int(p['pos'][1])), int(current_size * 1.5))
            # Lớp lõi (Đặc hơn)
            pygame.draw.circle(screen, (r, g, b, alpha), (int(p['pos'][0]), int(p['pos'][1])), int(current_size))
