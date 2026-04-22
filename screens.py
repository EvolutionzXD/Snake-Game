import pygame
import math

class MenuButton:
    def __init__(self, text, pos, size=(300, 60)):
        self.text = text
        self.pos = pygame.math.Vector2(pos)
        self.size = size
        # Rect dùng để va chạm chuột
        self.rect = pygame.Rect(pos[0] - size[0]//2, pos[1] - size[1]//2, size[0], size[1])
        self.is_hovered = False
        self.scale = 1.0
        self.font = pygame.font.SysFont("Impact", 40)
        
    def update(self, mouse_pos, dt):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        target_scale = 1.1 if self.is_hovered else 1.0
        # Lerp scale
        self.scale += (target_scale - self.scale) * 12.0 * dt
        
    def draw(self, screen):
        color = (50, 255, 50) if self.is_hovered else (200, 200, 200)
        
        # Hiệu ứng phát sáng nhẹ khi hover
        if self.is_hovered:
            glow_rect = self.rect.inflate(15, 15)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (50, 255, 50, 40), (0, 0, glow_rect.width, glow_rect.height), border_radius=15)
            screen.blit(glow_surf, glow_rect)

        # Vẽ viền nút với độ dày thay đổi theo scale
        border_thickness = int(3 * self.scale)
        pygame.draw.rect(screen, color, self.rect, border_thickness, border_radius=12)
        
        # Render chữ
        text_surf = self.font.render(self.text, True, color)
        if self.scale != 1.0:
            w, h = text_surf.get_size()
            text_surf = pygame.transform.smoothscale(text_surf, (int(w * self.scale), int(h * self.scale)))
            
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

class MainMenu:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        try:
            self.title_font = pygame.font.SysFont("Impact", 110)
            self.sub_font = pygame.font.SysFont("Arial", 24, bold=True)
        except:
            self.title_font = pygame.font.Font(None, 110)
            self.sub_font = pygame.font.Font(None, 24)
            
        self.buttons = [
            MenuButton("START GAME", (screen_w // 2, screen_h // 2 + 20)),
            MenuButton("OPTIONS", (screen_w // 2, screen_h // 2 + 100)),
            MenuButton("QUIT", (screen_w // 2, screen_h // 2 + 180))
        ]
        self.timer = 0.0

    def draw(self, screen, dt):
        self.timer += dt
        mouse_pos = pygame.mouse.get_pos()
        
        # Vẽ background tối giản nhưng xịn
        screen.fill((15, 15, 20)) 
        
        # 1. Vẽ Title hiệu ứng Wave
        for i in range(3): # Vẽ layer chồng lên nhau tạo độ dày
            offset = math.sin(self.timer * 2 + i*0.2) * 10
            color = (30 + i*20, 100 + i*40, 30 + i*20)
            title_surf = self.title_font.render("PY-SNAKE", True, color)
            title_rect = title_surf.get_rect(center=(self.screen_w // 2, 220 + offset))
            screen.blit(title_surf, title_rect)

        # 2. Vẽ Sub-title
        sub_text = self.sub_font.render("ULTIMATE EVOLUTION", True, (150, 150, 150))
        sub_rect = sub_text.get_rect(center=(self.screen_w // 2, 290 + math.sin(self.timer * 2) * 5))
        screen.blit(sub_text, sub_rect)
        
        # 3. Update & Draw Buttons
        for btn in self.buttons:
            btn.update(mouse_pos, dt)
            btn.draw(screen)
            
        # 4. Vẽ footer nhỏ
        footer = pygame.font.SysFont("Arial", 14).render("v1.0 - Created with Antigravity", True, (60, 60, 60))
        screen.blit(footer, (20, self.screen_h - 30))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for btn in self.buttons:
                    if btn.is_hovered:
                        return btn.text.lower().replace(" ", "_")
        return None
