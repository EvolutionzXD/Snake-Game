import pygame
from settings import SettingsManager
from resources import ResourceManager

class ToggleButton:
    def __init__(self, category, key, label, pos):
        self.category = category
        self.key = key
        self.label = label
        self.pos = pygame.math.Vector2(pos)
        self.rect = pygame.Rect(pos[0], pos[1], 60, 30)
        self.font = ResourceManager.get_instance().get_font("GrapeSoda", 30)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                SettingsManager.get_instance().toggle(self.category, self.key)
                return True
        return False
        
    def draw(self, screen):
        is_on = SettingsManager.get_instance().get(self.category, self.key)
        
        # Vẽ label
        text_surf = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(text_surf, (self.pos.x - text_surf.get_width() - 20, self.pos.y))
        
        # Vẽ nút gạt
        color = (50, 255, 50) if is_on else (100, 100, 100)
        pygame.draw.rect(screen, color, self.rect, border_radius=15)
        
        # Vẽ núm gạt
        circle_x = self.rect.right - 15 if is_on else self.rect.left + 15
        pygame.draw.circle(screen, (255, 255, 255), (circle_x, self.rect.centery), 12)

class Slider:
    def __init__(self, category, key, label, pos, width=200):
        self.category = category
        self.key = key
        self.label = label
        self.pos = pygame.math.Vector2(pos)
        self.width = width
        self.rect = pygame.Rect(pos[0], pos[1], width, 20)
        self.font = ResourceManager.get_instance().get_font("GrapeSoda", 30)
        self.is_dragging = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
                self._update_value(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            self._update_value(event.pos[0])
            return True
        return False
        
    def _update_value(self, mouse_x):
        ratio = (mouse_x - self.rect.left) / self.width
        ratio = max(0.0, min(1.0, ratio))
        SettingsManager.get_instance().set(self.category, self.key, ratio)
        
    def draw(self, screen):
        val = SettingsManager.get_instance().get(self.category, self.key)
        
        # Vẽ label
        text_surf = self.font.render(f"{self.label}: {int(val*100)}%", True, (255, 255, 255))
        screen.blit(text_surf, (self.pos.x - 200, self.pos.y - 5))
        
        # Vẽ thanh trượt nền
        pygame.draw.rect(screen, (100, 100, 100), self.rect, border_radius=10)
        
        # Vẽ thanh phần trăm
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, int(self.width * val), self.rect.height)
        if fill_rect.width > 0:
            pygame.draw.rect(screen, (50, 150, 255), fill_rect, border_radius=10)
            
        # Vẽ núm
        pygame.draw.circle(screen, (255, 255, 255), (self.rect.x + fill_rect.width, self.rect.centery), 12)

class SettingsScreen:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.font_title = ResourceManager.get_instance().get_font("GrapeSoda", 60)
        self.font_cat = ResourceManager.get_instance().get_font("GrapeSoda", 40)
        
        # Khung hộp chính
        box_w, box_h = 700, 600
        box_x = (screen_w - box_w) // 2
        box_y = (screen_h - box_h) // 2 - 20 # Nhích lên một chút để chừa chỗ cho nút Back
        self.box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        
        center_x = box_x + box_w // 2 + 100
        start_y = box_y + 110
        spacing = 45
        
        self.components = [
            ToggleButton("video", "show_fps", "Show FPS", (center_x, start_y)),
            ToggleButton("video", "show_hitbox", "Show Hitbox", (center_x, start_y + spacing)),
            ToggleButton("video", "show_grid", "Show AI Grid", (center_x, start_y + spacing * 2)),
            ToggleButton("video", "screen_shake", "Screen Shake", (center_x, start_y + spacing * 3)),
            ToggleButton("video", "particles", "Particles", (center_x, start_y + spacing * 4)),
            
            ToggleButton("gameplay", "show_damage_numbers", "Damage Numbers", (center_x, start_y + spacing * 6)),
            ToggleButton("gameplay", "auto_collect_exp", "Auto Collect EXP", (center_x, start_y + spacing * 7)),
            
            Slider("audio", "master_volume", "Master Volume", (center_x, start_y + spacing * 9)),
            # Slider("audio", "sfx_volume", "SFX Volume", (center_x, start_y + spacing * 10)),
            # Slider("audio", "bgm_volume", "BGM Volume", (center_x, start_y + spacing * 11))
        ]
        
        # Nút Back nằm ngoài khung
        from screens import MenuButton
        self.back_btn = MenuButton("BACK", (screen_w // 2, self.box_rect.bottom + 50))
        
    def handle_event(self, event):
        for comp in self.components:
            if comp.handle_event(event):
                return None
                
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_btn.is_hovered:
                return "back"
        return None
        
    def update(self, mouse_pos, dt):
        self.back_btn.update(mouse_pos, dt)
        
    def draw(self, screen):
        # 1. Nền tối mờ toàn màn hình
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, 200))
        screen.blit(overlay, (0, 0))
        
        # 2. Khung hộp tròn góc (Rounded Box)
        pygame.draw.rect(screen, (30, 30, 35), self.box_rect, border_radius=20)
        pygame.draw.rect(screen, (60, 60, 70), self.box_rect, width=4, border_radius=20) # Viền xám sáng
        
        # Tiêu đề
        title = self.font_title.render("SETTINGS", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(self.screen_w // 2, self.box_rect.top + 40)))
        
        # Phân loại
        c_vid = self.font_cat.render("VIDEO", True, (150, 150, 150))
        c_game = self.font_cat.render("GAMEPLAY", True, (150, 150, 150))
        c_aud = self.font_cat.render("AUDIO", True, (150, 150, 150))
        
        cat_x = self.box_rect.left + 50
        spacing = 45
        start_y = self.box_rect.top + 110
        
        screen.blit(c_vid, (cat_x, start_y + spacing * 1 - 20))
        screen.blit(c_game, (cat_x, start_y + spacing * 6 - 20))
        screen.blit(c_aud, (cat_x, start_y + spacing * 9 - 20))
        
        # Vẽ các nút cài đặt
        for comp in self.components:
            comp.draw(screen)
            
        # 3. Vẽ nút Back ở ngoài
        self.back_btn.draw(screen)
