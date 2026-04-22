import pygame
import random

class VFXManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = VFXManager()
        return cls._instance

    def __init__(self):
        self.screen_width = 1200
        self.screen_height = 800
        self.vignette_surf = None
        self.flash_alpha = 0
        self.chromatic_aberration_timer = 0.0
        self.chromatic_intensity = 0.0
        self._setup_vignette()

    def _setup_vignette(self):
        """Tạo lớp viền tối cực nhẹ (Soft Vignette)"""
        self.vignette_surf = pygame.Surface((self.screen_width, self.screen_height))
        # Tăng độ sáng cơ bản (220 thay vì 0) để viền không bao giờ quá tối
        self.vignette_surf.fill((220, 220, 220)) 
        
        for r in range(self.screen_width, 0, -15):
            t = r / self.screen_width
            # val tiến gần tới 255 nhanh hơn ở tâm
            val = int(220 + (255 - 220) * (1.0 - t**2.0)) 
            if val > 255: val = 255
            
            color = (val, val, val)
            rect = pygame.Rect(0, 0, r * 3.5, r * 2.2)
            rect.center = (self.screen_width // 2, self.screen_height // 2)
            pygame.draw.ellipse(self.vignette_surf, color, rect)

    def trigger_flash(self, intensity=255):
        """Gây chớp màn hình trắng"""
        self.flash_alpha = intensity

    def trigger_chromatic(self, duration=0.15, intensity=4.0):
        """Gây hiệu ứng nhòe màu (Giảm cường độ và thời gian)"""
        self.chromatic_aberration_timer = duration
        self.chromatic_intensity = intensity

    def update(self, dt):
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 1500 * dt)
        
        if self.chromatic_aberration_timer > 0:
            self.chromatic_aberration_timer = max(0, self.chromatic_aberration_timer - dt)

    def apply_post_processing(self, screen):
        # 1. Chromatic Aberration - Giảm cường độ blit
        if self.chromatic_aberration_timer > 0:
            intensity = int(self.chromatic_intensity * (self.chromatic_aberration_timer / 0.15))
            if intensity >= 1:
                temp_screen = screen.copy()
                temp_screen.set_alpha(100) # Chỉ blit bóng mờ để tránh quá gay
                screen.blit(temp_screen, (intensity, 0))
                screen.blit(temp_screen, (-intensity, 0))

        # 2. Vignette
        screen.blit(self.vignette_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        # 3. Screen Flash
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((self.screen_width, self.screen_height))
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(int(self.flash_alpha))
            screen.blit(flash_surf, (0, 0))
