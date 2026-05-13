import pygame
import math

class MenuButton:
    def __init__(self, text, pos, size=(300, 60)):
        from resources import ResourceManager
        self.text = text
        self.pos = pygame.math.Vector2(pos)
        self.size = size
        # Rect dùng để va chạm chuột
        self.rect = pygame.Rect(pos[0] - size[0]//2, pos[1] - size[1]//2, size[0], size[1])
        self.is_hovered = False
        self.scale = 1.0
        self.font = ResourceManager.get_instance().get_font("GrapeSoda", 50)
        self.normal_color = (200, 200, 200)
        self.hover_color = (50, 255, 50)
        
    def update(self, mouse_pos, dt):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        target_scale = 1.1 if self.is_hovered else 1.0
        # Lerp scale
        self.scale += (target_scale - self.scale) * 12.0 * dt
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.normal_color
        
        # Hiệu ứng phát sáng nhẹ khi hover
        if self.is_hovered:
            glow_rect = self.rect.inflate(15, 15)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            rgba_color = (self.hover_color[0], self.hover_color[1], self.hover_color[2], 40)
            pygame.draw.rect(glow_surf, rgba_color, (0, 0, glow_rect.width, glow_rect.height), border_radius=15)
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
        from resources import ResourceManager
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        self.title_font = ResourceManager.get_instance().get_font("GrapeSoda", 140)
        self.sub_font = ResourceManager.get_instance().get_font("VCRosdNEUE", 30)
            
        self.buttons = [
            MenuButton("START GAME", (screen_w // 2, screen_h // 2 + 20)),
            MenuButton("OPTIONS", (screen_w // 2, screen_h // 2 + 100)),
            MenuButton("QUIT", (screen_w // 2, screen_h // 2 + 180))
        ]
        self.timer = 0.0
        
        # State cho Level Select ngay trên MainMenu
        self.is_level_select_mode = False
        self.selected_wave = 1
        self.max_unlocked_wave = 1
        
        self.level_font = ResourceManager.get_instance().get_font("GrapeSoda", 50)
        self.arrow_font = ResourceManager.get_instance().get_font("GrapeSoda", 50)
        
        self.left_arrow_rect = pygame.Rect(screen_w // 2 + 40, screen_h // 2 - 10, 40, 60)
        self.right_arrow_rect = pygame.Rect(screen_w // 2 + 220, screen_h // 2 - 10, 40, 60)
        
        self.left_hover = False
        self.right_hover = False

    def update_max_wave(self, max_wave):
        self.max_unlocked_wave = max_wave
        if self.selected_wave > self.max_unlocked_wave:
            self.selected_wave = self.max_unlocked_wave

    def draw(self, screen, dt):
        self.timer += dt
        mouse_pos = pygame.mouse.get_pos()
        
        # Vẽ background tối giản nhưng xịn
        screen.fill((15, 15, 20)) 
        
        # 1. Vẽ Title hiệu ứng Wave
        for i in range(3): # Vẽ layer chồng lên nhau tạo độ dày
            offset = math.sin(self.timer * 2 + i*0.2) * 10
            color = (30 + i*20, 100 + i*40, 30 + i*20)
            title_surf = self.title_font.render("SNAKE GAME", True, color)
            title_rect = title_surf.get_rect(center=(self.screen_w // 2, 220 + offset))
            screen.blit(title_surf, title_rect)

        # 2. Vẽ Sub-title
        sub_text = self.sub_font.render("EVOLVED", True, (150, 150, 150))
        sub_rect = sub_text.get_rect(center=(self.screen_w // 2, 290 + math.sin(self.timer * 2) * 5))
        screen.blit(sub_text, sub_rect)
        
        # 3. Update & Draw Buttons
        for btn in self.buttons:
            # Di chuyển mượt mà nút START GAME sang trái khi vào mode chọn màn
            if btn.text in ["START GAME", "START", "START?"] and self.is_level_select_mode:
                btn.text = "START?"
                target_x = self.screen_w // 2 - 150
                btn.normal_color = (150, 255, 150) # Hơi xanh hơn
                btn.hover_color = (0, 255, 0)
            elif btn.text in ["START GAME", "START", "START?"] and not self.is_level_select_mode:
                btn.text = "START GAME"
                target_x = self.screen_w // 2
                btn.normal_color = (200, 200, 200)
                btn.hover_color = (50, 255, 50)
            else:
                target_x = self.screen_w // 2
                
            # Lerp position x
            btn.pos.x += (target_x - btn.pos.x) * 10.0 * dt
            btn.rect.centerx = int(btn.pos.x)
            
            btn.update(mouse_pos, dt)
            btn.draw(screen)
            
        # 3.5 Vẽ giao diện chọn màn nếu ở mode chọn màn
        if self.is_level_select_mode:
            # Fade in alpha theo vị trí của nút START
            alpha_ratio = min(1.0, max(0.0, (self.screen_w // 2 - self.buttons[0].pos.x) / 150.0))
            if alpha_ratio > 0.1:
                self.left_hover = self.left_arrow_rect.collidepoint(mouse_pos)
                self.right_hover = self.right_arrow_rect.collidepoint(mouse_pos)
                
                # Render chữ wave
                level_text = f"WAVE {self.selected_wave}"
                level_surf = self.level_font.render(level_text, True, (255, 255, 255))
                level_surf.set_alpha(int(255 * alpha_ratio))
                screen.blit(level_surf, level_surf.get_rect(center=(self.screen_w // 2 + 150, self.screen_h // 2 + 20)))
                
                # Render mũi tên
                if self.selected_wave > 1:
                    color = (50, 255, 50) if self.left_hover else (150, 150, 150)
                    left_surf = self.arrow_font.render("<", True, color)
                    left_surf.set_alpha(int(255 * alpha_ratio))
                    screen.blit(left_surf, left_surf.get_rect(center=self.left_arrow_rect.center))
                    
                if self.selected_wave < self.max_unlocked_wave:
                    color = (50, 255, 50) if self.right_hover else (150, 150, 150)
                    right_surf = self.arrow_font.render(">", True, color)
                    right_surf.set_alpha(int(255 * alpha_ratio))
                    screen.blit(right_surf, right_surf.get_rect(center=self.right_arrow_rect.center))
            
        # 4. Vẽ footer nhỏ
        from resources import ResourceManager
        footer_font = ResourceManager.get_instance().get_font("VCRosdNEUE", 16)
        footer = footer_font.render("v1.0 - Created with Antigravity", True, (60, 60, 60))
        screen.blit(footer, (20, self.screen_h - 30))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.is_level_select_mode:
                    if self.left_hover and self.selected_wave > 1:
                        self.selected_wave -= 1
                        return "wave_changed"
                    elif self.right_hover and self.selected_wave < self.max_unlocked_wave:
                        self.selected_wave += 1
                        return "wave_changed"
                
                for btn in self.buttons:
                    if btn.is_hovered:
                        if btn.text == "START GAME":
                            self.is_level_select_mode = True
                            return "enter_level_select"
                        return btn.text.lower().replace(" ", "_")
        return None

class SaveSelectMenu:
    def __init__(self, screen_w, screen_h):
        from resources import ResourceManager
        from save_system import SaveSystem
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.title_font = ResourceManager.get_instance().get_font("GrapeSoda", 100)
        self.info_font = ResourceManager.get_instance().get_font("VCRosdNEUE", 30)
        
        # Dời nút sang trái một chút để chừa chỗ cho Info text
        offset_x = -150
        self.buttons = [
            MenuButton("SAVE 1", (screen_w // 2 + offset_x, screen_h // 2 - 20)),
            MenuButton("SAVE 2", (screen_w // 2 + offset_x, screen_h // 2 + 60)),
            MenuButton("SAVE 3", (screen_w // 2 + offset_x, screen_h // 2 + 140))
        ]
        
        self.summaries = [
            SaveSystem.get_instance().get_save_summary(1),
            SaveSystem.get_instance().get_save_summary(2),
            SaveSystem.get_instance().get_save_summary(3)
        ]
        
        # Nút xóa (chỉ hiện cho slot đã có save)
        self.del_buttons = [
            MenuButton("X", (screen_w // 2 + 400, screen_h // 2 - 20), size=(60, 60)),
            MenuButton("X", (screen_w // 2 + 400, screen_h // 2 + 60), size=(60, 60)),
            MenuButton("X", (screen_w // 2 + 400, screen_h // 2 + 140), size=(60, 60))
        ]
        
        # Cho font chữ trong nút X nhỏ đi
        for btn in self.del_buttons:
            btn.font = ResourceManager.get_instance().get_font("GrapeSoda", 40)
            
        self.timer = 0.0
        
        # Naming mode
        self.is_naming = False
        self.naming_slot = -1
        self.input_text = ""
        
    def reload_summaries(self):
        from save_system import SaveSystem
        self.summaries = [
            SaveSystem.get_instance().get_save_summary(1),
            SaveSystem.get_instance().get_save_summary(2),
            SaveSystem.get_instance().get_save_summary(3)
        ]

    def draw(self, screen, dt):
        self.timer += dt
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((15, 15, 20))
        
        offset = math.sin(self.timer * 2) * 5
        title_surf = self.title_font.render("SELECT SAVE SLOT", True, (255, 200, 50))
        title_rect = title_surf.get_rect(center=(self.screen_w // 2, 200 + offset))
        screen.blit(title_surf, title_rect)
        
        for i, btn in enumerate(self.buttons):
            btn.update(mouse_pos, dt)
            btn.draw(screen)
            
            summary = self.summaries[i]
            if summary["is_empty"]:
                text = "Empty Slot"
                color = (100, 100, 100)
            else:
                text = f"{summary['username']} | Lvl {summary['level']} | Wave {summary['wave']}"
                color = (200, 255, 200)
                
                # Cập nhật và vẽ nút xóa
                self.del_buttons[i].update(mouse_pos, dt)
                self.del_buttons[i].draw(screen)
                
            info_surf = self.info_font.render(text, True, color)
            screen.blit(info_surf, (btn.rect.right + 20, btn.rect.centery - info_surf.get_height() // 2))

        # Hiển thị UI Naming
        if self.is_naming:
            # Làm mờ nền
            overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            prompt_surf = self.title_font.render("ENTER USERNAME", True, (100, 200, 255))
            screen.blit(prompt_surf, prompt_surf.get_rect(center=(self.screen_w // 2, self.screen_h // 2 - 60)))
            
            # Hiển thị chuỗi đang nhập, nhấp nháy con trỏ
            display_text = self.input_text
            if (self.timer * 2) % 1.0 > 0.5:
                display_text += "_"
                
            input_surf = self.title_font.render(display_text, True, (255, 255, 255))
            screen.blit(input_surf, input_surf.get_rect(center=(self.screen_w // 2, self.screen_h // 2 + 20)))
            
            hint_surf = self.info_font.render("Press ENTER to confirm, ESC to cancel", True, (150, 150, 150))
            screen.blit(hint_surf, hint_surf.get_rect(center=(self.screen_w // 2, self.screen_h // 2 + 100)))

    def handle_event(self, event):
        if self.is_naming:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if len(self.input_text.strip()) > 0:
                        # Chọn tên xong -> Khởi tạo save mặc định rồi vào game
                        from save_system import SaveSystem
                        name = self.input_text.strip()
                        # Lưu 1 file rỗng với tên này (Exp 0, Lvl 1, Wave 1)
                        SaveSystem.get_instance().set_current_slot(self.naming_slot)
                        SaveSystem.get_instance().save_game(name, 0, 1, 1, 0.0, 0.0, 1.0)
                        
                        self.is_naming = False
                        return f"save_{self.naming_slot}"
                elif event.key == pygame.K_ESCAPE:
                    self.is_naming = False
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    if len(self.input_text) < 12 and event.unicode.isprintable():
                        self.input_text += event.unicode
            return None
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Kiểm tra nút X
                for i, d_btn in enumerate(self.del_buttons):
                    if not self.summaries[i]["is_empty"] and d_btn.is_hovered:
                        from save_system import SaveSystem
                        SaveSystem.get_instance().delete_save(i + 1)
                        self.reload_summaries()
                        return None
                        
                for i, btn in enumerate(self.buttons):
                    if btn.is_hovered:
                        if self.summaries[i]["is_empty"]:
                            self.is_naming = True
                            self.naming_slot = i + 1
                            self.input_text = ""
                            return None
                        else:
                            return f"save_{i + 1}"
        return None

class LevelSelectMenu:
    def __init__(self, screen_w, screen_h):
        from resources import ResourceManager
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.title_font = ResourceManager.get_instance().get_font("GrapeSoda", 100)
        self.level_font = ResourceManager.get_instance().get_font("GrapeSoda", 80)
        self.arrow_font = ResourceManager.get_instance().get_font("GrapeSoda", 80)
        
        self.buttons = [
            MenuButton("PLAY", (screen_w // 2, screen_h // 2 + 120)),
            MenuButton("BACK", (screen_w // 2, screen_h // 2 + 200))
        ]
        
        self.selected_wave = 1
        self.max_unlocked_wave = 1
        self.timer = 0.0
        
        # Rects cho mũi tên
        self.left_arrow_rect = pygame.Rect(screen_w // 2 - 150, screen_h // 2 - 40, 60, 60)
        self.right_arrow_rect = pygame.Rect(screen_w // 2 + 90, screen_h // 2 - 40, 60, 60)
        
        self.left_hover = False
        self.right_hover = False

    def update_max_wave(self, max_wave):
        self.max_unlocked_wave = max_wave
        if self.selected_wave > self.max_unlocked_wave:
            self.selected_wave = self.max_unlocked_wave

    def draw(self, screen, dt):
        self.timer += dt
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((15, 15, 20))
        
        offset = math.sin(self.timer * 2) * 5
        title_surf = self.title_font.render("SELECT LEVEL", True, (100, 200, 255))
        title_rect = title_surf.get_rect(center=(self.screen_w // 2, 200 + offset))
        screen.blit(title_surf, title_rect)
        
        # Cập nhật hover mũi tên
        self.left_hover = self.left_arrow_rect.collidepoint(mouse_pos)
        self.right_hover = self.right_arrow_rect.collidepoint(mouse_pos)
        
        # Vẽ số Level
        level_text = f"WAVE {self.selected_wave}"
        level_surf = self.level_font.render(level_text, True, (255, 255, 255))
        screen.blit(level_surf, level_surf.get_rect(center=(self.screen_w // 2, self.screen_h // 2 - 10)))
        
        # Vẽ mũi tên trái (ẩn nếu đang ở wave 1)
        if self.selected_wave > 1:
            color = (50, 255, 50) if self.left_hover else (150, 150, 150)
            left_surf = self.arrow_font.render("<", True, color)
            screen.blit(left_surf, left_surf.get_rect(center=self.left_arrow_rect.center))
            
        # Vẽ mũi tên phải (ẩn nếu đang ở max unlocked wave)
        if self.selected_wave < self.max_unlocked_wave:
            color = (50, 255, 50) if self.right_hover else (150, 150, 150)
            right_surf = self.arrow_font.render(">", True, color)
            screen.blit(right_surf, right_surf.get_rect(center=self.right_arrow_rect.center))

        for btn in self.buttons:
            btn.update(mouse_pos, dt)
            btn.draw(screen)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Click mũi tên
                if self.left_hover and self.selected_wave > 1:
                    self.selected_wave -= 1
                elif self.right_hover and self.selected_wave < self.max_unlocked_wave:
                    self.selected_wave += 1
                
                # Click nút
                for btn in self.buttons:
                    if btn.is_hovered:
                        return btn.text.lower().replace(" ", "_")
        return None

class PauseMenu:
    def __init__(self, screen_w, screen_h):
        from resources import ResourceManager
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        self.title_font = ResourceManager.get_instance().get_font("GrapeSoda", 100)
        self.warn_font = ResourceManager.get_instance().get_font("VCRosdNEUE", 30)
        
        center_x = screen_w // 2
        center_y = screen_h // 2
        self.buttons = [
            MenuButton("RESUME", (center_x, center_y - 20)),
            MenuButton("OPTIONS", (center_x, center_y + 60)),
            MenuButton("MAIN MENU", (center_x, center_y + 140))
        ]
        
        self.confirming_quit = False
        self.confirm_buttons = [
            MenuButton("YES", (center_x - 100, center_y + 100), size=(180, 60)),
            MenuButton("NO", (center_x + 100, center_y + 100), size=(180, 60))
        ]
        
    def draw(self, screen, dt):
        mouse_pos = pygame.mouse.get_pos()
        
        if self.confirming_quit:
            # Vẽ hộp thoại cảnh báo
            box_rect = pygame.Rect(self.screen_w//2 - 250, self.screen_h//2 - 150, 500, 300)
            pygame.draw.rect(screen, (30, 30, 35), box_rect, border_radius=20)
            pygame.draw.rect(screen, (255, 100, 100), box_rect, width=4, border_radius=20)
            
            title_surf = self.title_font.render("WARNING!", True, (255, 100, 100))
            screen.blit(title_surf, title_surf.get_rect(center=(self.screen_w // 2, self.screen_h // 2 - 80)))
            
            warn_surf = self.warn_font.render("All progress will be lost. Are you sure?", True, (200, 200, 200))
            screen.blit(warn_surf, warn_surf.get_rect(center=(self.screen_w // 2, self.screen_h // 2)))
            
            for btn in self.confirm_buttons:
                btn.update(mouse_pos, dt)
                btn.draw(screen)
        else:
            title_surf = self.title_font.render("PAUSED", True, (255, 255, 255))
            title_rect = title_surf.get_rect(center=(self.screen_w // 2, 200))
            screen.blit(title_surf, title_rect)
            
            for btn in self.buttons:
                btn.update(mouse_pos, dt)
                btn.draw(screen)
            
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.confirming_quit:
                    for btn in self.confirm_buttons:
                        if btn.is_hovered:
                            if btn.text == "YES":
                                self.confirming_quit = False
                                return "confirm_quit"
                            elif btn.text == "NO":
                                self.confirming_quit = False
                                return None
                else:
                    for btn in self.buttons:
                        if btn.is_hovered:
                            action = btn.text.lower().replace(" ", "_")
                            if action == "main_menu":
                                self.confirming_quit = True
                                return None
                            return action
        return None

class GameOverMenu:
    def __init__(self, screen_w, screen_h):
        from resources import ResourceManager
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        self.title_font = ResourceManager.get_instance().get_font("GrapeSoda", 140)
        self.score_font = ResourceManager.get_instance().get_font("VCRosdNEUE", 40)
        
        center_x = screen_w // 2
        center_y = screen_h // 2
        self.buttons = [
            MenuButton("TRY AGAIN", (center_x, center_y + 60)),
            MenuButton("MAIN MENU", (center_x, center_y + 140))
        ]
        
    def draw(self, screen, dt, score, level):
        mouse_pos = pygame.mouse.get_pos()
        
        # Nền đỏ mờ
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((50, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        title_surf = self.title_font.render("GAME OVER", True, (255, 50, 50))
        title_rect = title_surf.get_rect(center=(self.screen_w // 2, 200))
        screen.blit(title_surf, title_rect)
        
        score_surf = self.score_font.render(f"Level: {level}   |   Kills: {score}", True, (255, 255, 255))
        score_rect = score_surf.get_rect(center=(self.screen_w // 2, 300))
        screen.blit(score_surf, score_rect)
        
        for btn in self.buttons:
            btn.update(mouse_pos, dt)
            btn.draw(screen)
            
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for btn in self.buttons:
                    if btn.is_hovered:
                        return btn.text.lower().replace(" ", "_")
        return None

class LevelUpMenu:
    def __init__(self, screen_w, screen_h):
        from resources import ResourceManager
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.title_font = ResourceManager.get_instance().get_font("GrapeSoda", 80)
        self.stat_font = ResourceManager.get_instance().get_font("VCRosdNEUE", 30)
        self.upgrade_font = ResourceManager.get_instance().get_font("GrapeSoda", 40)
        self.upgrades = []
        self.hovered_idx = -1
        self.hovered_reset = False
        
    def setup_cards(self, upgrades):
        # Lưu lại danh sách nâng cấp cố định
        self.upgrades = upgrades
            
    def draw(self, screen, dt):
        from apple import AppleManager
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_idx = -1
        self.hovered_reset = False
        
        # Overlay
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        # Panel
        panel_w, panel_h = 750, 550
        panel_rect = pygame.Rect((self.screen_w - panel_w)//2, (self.screen_h - panel_h)//2 + 40, panel_w, panel_h)
        pygame.draw.rect(screen, (30, 30, 40), panel_rect, border_radius=20)
        pygame.draw.rect(screen, (70, 70, 90), panel_rect, width=4, border_radius=20)
        
        # Title
        title_surf = self.title_font.render("STATUS & UPGRADES", True, (255, 255, 50))
        title_rect = title_surf.get_rect(center=(self.screen_w // 2, panel_rect.top - 50))
        screen.blit(title_surf, title_rect)
        
        # Status Points
        points_color = (100, 255, 100) if AppleManager.status_points > 0 else (200, 200, 200)
        points_surf = self.upgrade_font.render(f"STATUS POINTS: {AppleManager.status_points}", True, points_color)
        screen.blit(points_surf, (panel_rect.left + 40, panel_rect.top + 20))
        
        start_y = panel_rect.top + 80
        row_h = 110
        
        for i, upg in enumerate(self.upgrades):
            row_rect = pygame.Rect(panel_rect.left + 40, start_y + i * row_h, panel_w - 80, 90)
            is_hover = row_rect.collidepoint(mouse_pos)
            
            bg_color = (50, 50, 70) if is_hover else (40, 40, 55)
            pygame.draw.rect(screen, bg_color, row_rect, border_radius=15)
            pygame.draw.circle(screen, (255, 215, 0), (row_rect.left + 40, row_rect.centery), 10)
            
            name_surf = self.upgrade_font.render(upg.name, True, (255, 255, 255))
            screen.blit(name_surf, (row_rect.left + 80, row_rect.top + 15))
            desc_surf = self.stat_font.render(upg.description, True, (160, 160, 170))
            screen.blit(desc_surf, (row_rect.left + 80, row_rect.top + 55))
            
            btn_w, btn_h = 160, 50
            btn_rect = pygame.Rect(row_rect.right - 180, row_rect.centery - btn_h//2, btn_w, btn_h)
            can_upgrade = AppleManager.status_points > 0
            
            if btn_rect.collidepoint(mouse_pos) and can_upgrade:
                self.hovered_idx = i
                btn_color = (50, 255, 50)
            else:
                btn_color = (30, 180, 30) if can_upgrade else (80, 80, 80)
                
            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)
            btn_text = self.upgrade_font.render("UPGRADE", True, (0, 0, 0))
            screen.blit(btn_text, btn_text.get_rect(center=btn_rect.center))

        # RESET STATUS
        reset_w, reset_h = 300, 50
        reset_rect = pygame.Rect(panel_rect.right - reset_w - 40, panel_rect.bottom - 70, reset_w, reset_h)
        can_reset = AppleManager.coins >= 1000
        
        if reset_rect.collidepoint(mouse_pos) and can_reset:
            self.hovered_reset = True
            reset_color = (255, 50, 50)
        else:
            reset_color = (180, 30, 30) if can_reset else (60, 60, 60)
            
        pygame.draw.rect(screen, reset_color, reset_rect, border_radius=10)
        reset_text = self.stat_font.render("RESET STATS (1000 C)", True, (255, 255, 255))
        screen.blit(reset_text, reset_text.get_rect(center=reset_rect.center))

        # Footer
        level_text = self.stat_font.render(f"LV {AppleManager.level} | COINS: {AppleManager.coins}", True, (200, 200, 200))
        screen.blit(level_text, (panel_rect.left + 40, panel_rect.bottom - 40))

        # Hint
        hint_text = self.stat_font.render("PRESS [I] OR [ESC] TO CLOSE", True, (150, 150, 150))
        screen.blit(hint_text, hint_text.get_rect(midtop=(self.screen_w // 2, panel_rect.bottom + 15)))

    def handle_event(self, event):
        from apple import AppleManager
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.hovered_idx != -1:
                    # Gọi apply trực tiếp để chạy effect_fn (bao gồm cả trừ điểm và buff chỉ số)
                    self.upgrades[self.hovered_idx].apply()
                    # Refresh lại danh sách nâng cấp để cập nhật text (Lvl mới)
                    import upgrade
                    self.setup_cards(upgrade.get_available_upgrades())
                    return "upgrade_selected"
                elif getattr(self, 'hovered_reset', False):
                    if AppleManager.reset_stats():
                        import upgrade
                        self.setup_cards(upgrade.get_available_upgrades())
                        return "stats_reset"
        return None
