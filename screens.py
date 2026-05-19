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
            MenuButton("INVENTORY", (screen_w // 2, screen_h // 2 + 100)),
            MenuButton("OPTIONS", (screen_w // 2, screen_h // 2 + 180)),
            MenuButton("QUIT", (screen_w // 2, screen_h // 2 + 260))
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
            title_rect = title_surf.get_rect(center=(self.screen_w // 2, 200 + offset))
            screen.blit(title_surf, title_rect)

        # 2. Vẽ Sub-title
        sub_text = self.sub_font.render("EVOLVED", True, (150, 150, 150))
        sub_rect = sub_text.get_rect(center=(self.screen_w // 2, 270 + math.sin(self.timer * 2) * 5))
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

class InventoryMenu:
    def __init__(self, screen_w, screen_h):
        from resources import ResourceManager
        from arsenal import WEAPON_CATALOG
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.title_font = ResourceManager.get_instance().get_font("GrapeSoda", 80)
        self.stat_font = ResourceManager.get_instance().get_font("VCRosdNEUE", 24)
        self.small_font = ResourceManager.get_instance().get_font("VCRosdNEUE", 18) # Font nhỏ cho mô tả
        self.name_font = ResourceManager.get_instance().get_font("GrapeSoda", 36)
        
        self.catalog = WEAPON_CATALOG
        self.selected_slot = 0 
        self.hovered_weapon = None
        self.selected_weapon = None # Thêm biến này để giữ bảng nâng cấp cố định
        self.timer = 0.0
        self.desc_scroll_y = 0.0 # Cuộn cho mô tả
        
        # Load Icons tiền
        res = ResourceManager.get_instance()
        apple_tex = res.get_texture("apple")
        if apple_tex: self.apple_icon = apple_tex.subsurface((0, 0, 32, 32))
        else: self.apple_icon = None
        
        rock_tex = res.get_texture("rock")
        if rock_tex: self.rock_icon = rock_tex.subsurface((0, 0, 32, 32))
        else: self.rock_icon = None
        
        self.back_button = MenuButton("BACK", (screen_w // 2, screen_h - 60))
        
        # --- PHÂN TRANG ---
        self.page = 0
        self.items_per_page = 8 # 4 cột x 2 hàng
        # Nút chuyển trang (Nhỏ hơn nút menu thường)
        self.btn_prev = MenuButton("<", (125, 420), size=(60, 60))
        self.btn_next = MenuButton(">", (685, 420), size=(60, 60))

    def draw(self, screen, dt):
        from inventory import InventoryManager
        from apple import AppleManager
        from resources import ResourceManager
        
        self.timer += dt
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((10, 10, 15)) # Tối hơn chút cho sang
        
        inv = InventoryManager.get_instance()
        equipped = inv.get_equipped_list()
        
        # 2. Vẽ Danh sách vũ khí (Phân trang)
        self._draw_weapon_grid(screen, inv, mouse_pos)
        
        # 3. Vẽ Mũi tên chuyển trang nếu có nhiều hơn 1 trang
        num_pages = (len(self.catalog) + self.items_per_page - 1) // self.items_per_page
        if num_pages > 1:
            if self.page > 0:
                self.btn_prev.update(mouse_pos, dt)
                self.btn_prev.draw(screen)
            if self.page < num_pages - 1:
                self.btn_next.update(mouse_pos, dt)
                self.btn_next.draw(screen)
        
        # 4. Vẽ 3 Slot đang trang bị
        self._draw_equipped_slots(screen, equipped, mouse_pos)
        
        # 5. Vẽ chi tiết vũ khí (Ưu tiên hover, nếu ko hover thì hiện món đang chọn)
        viewing_weapon = self.hovered_weapon if self.hovered_weapon else self.selected_weapon
        if viewing_weapon:
            self._draw_weapon_details(screen, viewing_weapon)
            
        # 5.5 Vẽ số dư tiền (Ví tiền) ở góc trên bên phải - DÙNG THIẾT KẾ PILL ĐỒNG BỘ
        wallet_x = self.screen_w - 50
        # Vẽ Đá trước
        self._draw_coin_pill(screen, wallet_x, 40, self.rock_icon, AppleManager.pepper_coins, (210, 245, 255))
        # Vẽ Táo bên trái Đá
        txt_w = self.stat_font.size(str(AppleManager.pepper_coins))[0]
        self._draw_coin_pill(screen, wallet_x - txt_w - 80, 40, self.apple_icon, AppleManager.coins, (255, 215, 0))
            
        self.back_button.update(mouse_pos, dt)
        self.back_button.draw(screen)

    def _draw_coin_pill(self, screen, right_x, top_y, icon_img, amount, text_color):
        if not icon_img: return

        # 1. Render Text
        amount_str = str(amount)
        text_surf = self.stat_font.render(amount_str, True, text_color)
        text_shadow = self.stat_font.render(amount_str, True, (0, 0, 0))
        
        # 2. Pill Dimensions
        pill_h = 36
        pill_w = text_surf.get_width() + 50
        pill_x = right_x - pill_w
        pill_rect = pygame.Rect(pill_x, top_y + 8, pill_w, pill_h)
        
        # 3. Draw Pill BG (Trong suốt + Viền)
        pill_surf = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        pygame.draw.rect(pill_surf, (20, 20, 20, 180), pill_surf.get_rect(), border_radius=pill_h//2)
        pygame.draw.rect(pill_surf, (255, 255, 255, 80), pill_surf.get_rect(), width=2, border_radius=pill_h//2)
        screen.blit(pill_surf, pill_rect.topleft)
        
        # 4. Draw Icon (To hơn pill một chút và lệch ra ngoài)
        icon_scale = 1.3
        icon_w, icon_h = int(32 * icon_scale), int(32 * icon_scale)
        scaled_icon = pygame.transform.scale(icon_img, (icon_w, icon_h))
        screen.blit(scaled_icon, (pill_x - 15, top_y))
        
        # 5. Draw Text
        text_x = pill_x + 35
        text_y = pill_rect.centery - text_surf.get_height()//2
        screen.blit(text_shadow, (text_x + 2, text_y + 2))
        screen.blit(text_surf, (text_x, text_y))

    def _draw_corner_frame(self, screen, rect, color, thickness=5, size=20):
        """Vẽ khung chỉ hiện 4 góc (corner-only frame) - BO TRÒN NHẸ."""
        arc_r = 10 # Bán kính bo góc
        # Top-left
        pygame.draw.arc(screen, color, (rect.left, rect.top, arc_r*2, arc_r*2), math.pi/2, math.pi, thickness)
        pygame.draw.line(screen, color, (rect.left, rect.top + arc_r), (rect.left, rect.top + size), thickness)
        pygame.draw.line(screen, color, (rect.left + arc_r, rect.top), (rect.left + size, rect.top), thickness)
        
        # Top-right
        pygame.draw.arc(screen, color, (rect.right - arc_r*2, rect.top, arc_r*2, arc_r*2), 0, math.pi/2, thickness)
        pygame.draw.line(screen, color, (rect.right, rect.top + arc_r), (rect.right, rect.top + size), thickness)
        pygame.draw.line(screen, color, (rect.right - arc_r, rect.top), (rect.right - size, rect.top), thickness)
        
        # Bottom-left
        pygame.draw.arc(screen, color, (rect.left, rect.bottom - arc_r*2, arc_r*2, arc_r*2), math.pi, 3*math.pi/2, thickness)
        pygame.draw.line(screen, color, (rect.left, rect.bottom - arc_r), (rect.left, rect.bottom - size), thickness)
        pygame.draw.line(screen, color, (rect.left + arc_r, rect.bottom), (rect.left + size, rect.bottom), thickness)
        
        # Bottom-right
        pygame.draw.arc(screen, color, (rect.right - arc_r*2, rect.bottom - arc_r*2, arc_r*2, arc_r*2), 3*math.pi/2, 2*math.pi, thickness)
        pygame.draw.line(screen, color, (rect.right, rect.bottom - arc_r), (rect.right, rect.bottom - size), thickness)
        pygame.draw.line(screen, color, (rect.right - arc_r, rect.bottom), (rect.right - size, rect.bottom), thickness)

    def _draw_weapon_grid(self, screen, inv, mouse_pos):
        from resources import ResourceManager
        grid_x, grid_y = 150, 150
        cols = 4
        spacing = 130
        self.hovered_weapon = None
        
        # --- VẼ KHUNG TRẮNG BAO QUANH GRID (Cố định 2 hàng) ---
        grid_w = (cols - 1) * spacing + 110
        grid_h = (2 - 1) * spacing + 110
        padding = 45 
        full_grid_rect = pygame.Rect(grid_x - padding, grid_y - padding, grid_w + padding * 2, grid_h + padding * 2)
        
        pygame.draw.rect(screen, (255, 255, 255), full_grid_rect, width=2, border_radius=20)
        glow_surf = pygame.Surface((full_grid_rect.width, full_grid_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (255, 255, 255, 10), glow_surf.get_rect(), border_radius=20)
        screen.blit(glow_surf, full_grid_rect.topleft)
        
        # Lấy danh sách items cho trang hiện tại
        items_list = list(self.catalog.items())
        page_items = items_list[self.page * self.items_per_page : (self.page + 1) * self.items_per_page]
        
        for i, (wid, data) in enumerate(page_items):
            row, col = divmod(i, cols)
            
            # --- HIỆU ỨNG BAY BỔNG (SIN WAVE SIÊU NHẸ) ---
            bob_y = math.sin(self.timer * 2.5 + i * 0.5) * 3.5
            
            box_rect = pygame.Rect(grid_x + col * spacing, grid_y + row * spacing + bob_y, 110, 110)
            is_unlocked = inv.is_unlocked(wid)
            is_hover = box_rect.collidepoint(mouse_pos)
            
            if is_hover: self.hovered_weapon = wid
            
            # 1. Vẽ bóng đổ (Shadow)
            pygame.draw.rect(screen, (0, 0, 0, 100), box_rect.move(4, 4), border_radius=15)
            
            # 2. Vẽ Box background
            bg_color = (60, 60, 80) if is_hover else (35, 35, 45)
            if not is_unlocked: bg_color = (20, 20, 25)
            
            box_surf = pygame.Surface((110, 110), pygame.SRCALPHA)
            pygame.draw.rect(box_surf, (*bg_color, 200), box_surf.get_rect(), border_radius=15)
            screen.blit(box_surf, box_rect.topleft)
            
            # 3. Vẽ viền hộp
            border_color = (200, 200, 200) if is_hover else (80, 80, 90)
            if not is_unlocked: border_color = (50, 50, 60)
            pygame.draw.rect(screen, border_color, box_rect, width=2, border_radius=15)
            
            # 4. Vẽ khung VÀNG FULL nếu đang được trang bị
            if wid in inv.equipped_weapons:
                pygame.draw.rect(screen, (255, 215, 0), box_rect.inflate(12, 12), width=4, border_radius=20)
                gold_glow = pygame.Surface((box_rect.width + 20, box_rect.height + 20), pygame.SRCALPHA)
                pygame.draw.rect(gold_glow, (255, 215, 0, 30), gold_glow.get_rect(), border_radius=25)
                screen.blit(gold_glow, (box_rect.x - 10, box_rect.y - 10))
            
            # 5. Vẽ khung góc trắng (BO TRÒN) nếu đang hover
            if is_hover:
                self._draw_corner_frame(screen, box_rect.inflate(8, 8), (255, 255, 255), thickness=4, size=20)
            
            # 5.5 Vẽ Cấp độ
            lvl = inv.get_level(wid)
            if lvl > 0:
                is_awake = inv.is_awakened(wid)
                lvl_text = f"Lv.{lvl}" if not is_awake else "AWAKENED"
                lvl_color = (255, 215, 0) if is_awake else (255, 255, 255)
                lvl_surf = self.stat_font.render(lvl_text, True, lvl_color)
                screen.blit(lvl_surf, (box_rect.right - lvl_surf.get_width() - 5, box_rect.bottom - 25))
            
            # 6. Vẽ Icon Vũ khí
            avatar_name = data.get("avatar", data["kwargs"].get("texture_name", "stick"))
            tex = ResourceManager.get_instance().get_texture(avatar_name)
            if tex:
                tw, th = tex.get_size()
                scale = 85 / max(tw, th)
                icon = pygame.transform.scale(tex, (int(tw * scale), int(th * scale)))
                if not is_unlocked: 
                    icon.set_alpha(100)
                    # Biến icon thành màu đen/tối khi chưa mở khóa
                    icon.fill((20, 20, 20), special_flags=pygame.BLEND_MULT)
                icon_rect = icon.get_rect(center=box_rect.center)
                screen.blit(icon, icon_rect)
            

    def _draw_equipped_slots(self, screen, equipped, mouse_pos):
        panel_x = 750
        panel_y = 150
        slot_h = 140
        slot_w = 450
        
        title = self.name_font.render("SELECTED LOADOUT", True, (200, 200, 200))
        screen.blit(title, (panel_x, panel_y - 45))

        for i in range(3):
            # Sin wave siêu nhẹ cho slot
            slot_bob_y = math.sin(self.timer * 2.0 + i * 0.7) * 4.0
            slot_rect = pygame.Rect(panel_x, panel_y + i * (slot_h + 20) + slot_bob_y, slot_w, slot_h)
            is_selected = (self.selected_slot == i)
            is_hover = slot_rect.collidepoint(mouse_pos)
            
            # Slot background
            bg_color = (45, 45, 60) if is_selected else (25, 25, 35)
            pygame.draw.rect(screen, bg_color, slot_rect, border_radius=15)
            
            # Vẽ khung góc trắng cho slot đang được chọn để thay thế
            if is_selected:
                self._draw_corner_frame(screen, slot_rect.inflate(10, 10), (255, 255, 255), thickness=4, size=25)
                # Vẽ viền mờ bên trong
                pygame.draw.rect(screen, (100, 100, 150), slot_rect, width=2, border_radius=15)
            
            # Label
            key_surf = self.stat_font.render(f"SLOT {i+1}", True, (255, 255, 50) if is_selected else (100, 100, 100))
            screen.blit(key_surf, (slot_rect.left + 20, slot_rect.top + 15))
            
            # Weapon info
            wid = equipped[i]
            if wid in self.catalog:
                data = self.catalog[wid]
                from resources import ResourceManager
                avatar_name = data.get("avatar", data["kwargs"].get("texture_name", "stick"))
                tex = ResourceManager.get_instance().get_texture(avatar_name)
                if tex:
                    icon = pygame.transform.scale(tex, (70, 70))
                    screen.blit(icon, (slot_rect.left + 30, slot_rect.top + 45))
                
                name_surf = self.name_font.render(data["args"][0].upper(), True, (255, 255, 255))
                screen.blit(name_surf, (slot_rect.left + 120, slot_rect.top + 60))
            else:
                empty_surf = self.name_font.render("EMPTY", True, (60, 60, 70))
                screen.blit(empty_surf, (slot_rect.left + 120, slot_rect.top + 60))

            # Click để chọn slot này làm mục tiêu thay thế
            if is_hover and pygame.mouse.get_pressed()[0]:
                self.selected_slot = i

    def _draw_weapon_details(self, screen, wid):
        data = self.catalog[wid]
        kwargs = data["kwargs"]
        
        # 1. Chuẩn bị nội dung text
        name_str = data["args"][0].upper()
        desc_str = data["description"]
        stats_str = f"SPD: {int(kwargs.get('speed', 0))} | RATE: {kwargs.get('fire_rate', 0)}s | STAMINA: {kwargs.get('stamina_cost', 0)}"
        
        # 2. Render Header
        n_surf = self.name_font.render(name_str, True, data["color"])
        stats_str = f"SPD: {int(kwargs.get('speed', 0))} | RATE: {kwargs.get('fire_rate', 0)}s"
        s_surf = self.stat_font.render(stats_str, True, (100, 200, 255))
        
        # 3. Tính toán Rect (Dời sang trái x=50, cố định size)
        padding = 25
        panel_w = 400
        panel_h = 180
        panel_rect = pygame.Rect(50, 480, panel_w, panel_h)
        self.desc_panel_rect = panel_rect # Lưu để check scroll
        
        # 4. Vẽ nền và khung
        pygame.draw.rect(screen, (20, 20, 30, 240), panel_rect, border_radius=15)
        self._draw_corner_frame(screen, panel_rect, data["color"], thickness=2, size=15)
        
        # 5. Vẽ text lên panel
        screen.blit(n_surf, (panel_rect.left + padding, panel_rect.top + 15))
        screen.blit(s_surf, (panel_rect.left + padding, panel_rect.top + 50))
        
        # --- MULTI-LINE DESCRIPTION WITH SCROLL ---
        words = desc_str.split(' ')
        lines = []
        curr_line = ""
        for w in words:
            if self.small_font.size(curr_line + w)[0] < panel_w - 50:
                curr_line += w + " "
            else:
                lines.append(curr_line)
                curr_line = w + " "
        lines.append(curr_line)
        
        # Clip area cho text
        desc_area = pygame.Rect(panel_rect.left + 25, panel_rect.top + 85, panel_w - 40, panel_h - 100)
        # pygame.draw.rect(screen, (255,255,255,10), desc_area) # Debug
        
        for i, line in enumerate(lines):
            y_pos = desc_area.top + (i * 22) - self.desc_scroll_y
            if desc_area.top - 15 < y_pos < desc_area.bottom:
                l_surf = self.small_font.render(line, True, (180, 180, 180))
                screen.blit(l_surf, (desc_area.left, y_pos))
        
        # Vẽ thanh cuộn nhỏ nếu cần
        total_h = len(lines) * 22
        if total_h > desc_area.height:
            scroll_bar_h = (desc_area.height / total_h) * desc_area.height
            scroll_bar_y = desc_area.top + (self.desc_scroll_y / total_h) * desc_area.height
            pygame.draw.rect(screen, (100, 100, 100), (desc_area.right + 5, desc_area.top, 4, desc_area.height), border_radius=2)
            pygame.draw.rect(screen, data["color"], (desc_area.right + 5, scroll_bar_y, 4, scroll_bar_h), border_radius=2)

        # 6. PANEL NÂNG CẤP (DYNAMICS)
        from inventory import InventoryManager
        from apple import AppleManager
        inv = InventoryManager.get_instance()
        lvl = inv.get_level(wid)
        is_awake = inv.is_awakened(wid)
        max_lvl = data.get("max_level", 5)
        
        upg_rect = pygame.Rect(panel_rect.right + 20, panel_rect.top, 350, panel_rect.height)
        pygame.draw.rect(screen, (35, 35, 45), upg_rect, border_radius=15)
        pygame.draw.rect(screen, (100, 100, 120), upg_rect, width=2, border_radius=15)
        
        # Tiêu đề upgrade
        upg_title = self.name_font.render("UPGRADE", True, (255, 255, 255))
        screen.blit(upg_title, (upg_rect.left + 20, upg_rect.top + 15))
        
        # Kiểm tra mốc tiếp theo
        next_lvl = None
        if lvl < max_lvl:
            next_lvl = lvl + 1
        elif not is_awake:
            next_lvl = "awaken"
            
        if next_lvl and next_lvl in data.get("upgrades", {}):
            upg_info = data["upgrades"][next_lvl]
            cost_apple, cost_pepper = upg_info["cost"]
            
            # Mô tả nâng cấp (Dùng font nhỏ)
            desc_upg = self.small_font.render(upg_info["desc"], True, (150, 255, 150))
            screen.blit(desc_upg, (upg_rect.left + 20, upg_rect.top + 50))
            
            # Hiển thị giá (Dạng Icon + Text đơn giản cho thoáng)
            can_afford_apple = AppleManager.coins >= cost_apple
            can_afford_pepper = AppleManager.pepper_coins >= cost_pepper
            can_afford = can_afford_apple and can_afford_pepper
            
            draw_x = upg_rect.left + 25
            draw_y = upg_rect.top + 80
            
            # Icon Táo + Giá
            if self.apple_icon:
                screen.blit(pygame.transform.scale(self.apple_icon, (24, 24)), (draw_x, draw_y))
                txt_apple = self.stat_font.render(str(cost_apple), True, (255, 255, 255) if can_afford_apple else (255, 100, 100))
                screen.blit(txt_apple, (draw_x + 30, draw_y + 2))
                draw_x += 100
                
            # Icon Đá + Giá
            if self.rock_icon:
                screen.blit(pygame.transform.scale(self.rock_icon, (24, 24)), (draw_x, draw_y))
                txt_rock = self.stat_font.render(str(cost_pepper), True, (255, 255, 255) if can_afford_pepper else (255, 100, 100))
                screen.blit(txt_rock, (draw_x + 30, draw_y + 2))
            
            # Nút UPGRADE
            btn_rect = pygame.Rect(upg_rect.left + 20, upg_rect.bottom - 60, upg_rect.width - 40, 45)
            is_btn_hover = btn_rect.collidepoint(pygame.mouse.get_pos())
            btn_color = (0, 200, 0) if can_afford else (60, 60, 60)
            if is_btn_hover and can_afford: btn_color = (0, 255, 0)
            
            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)
            btn_txt = "AWAKEN!" if next_lvl == "awaken" else "LEVEL UP"
            btn_surf = self.stat_font.render(btn_txt, True, (0, 0, 0))
            screen.blit(btn_surf, btn_surf.get_rect(center=btn_rect.center))
            self.upgrade_btn_rect = btn_rect # Lưu để handle click
        else:
            msg = "MAX LEVEL REACHED" if is_awake else "COMING SOON"
            msg_surf = self.stat_font.render(msg, True, (100, 100, 100))
            screen.blit(msg_surf, msg_surf.get_rect(center=upg_rect.center))
            self.upgrade_btn_rect = None

    def handle_event(self, event):
        from inventory import InventoryManager
        inv = InventoryManager.get_instance()
        
        if event.type == pygame.MOUSEWHEEL:
            # Cuộn mô tả nếu đang hover panel mô tả
            if hasattr(self, 'desc_panel_rect') and self.desc_panel_rect.collidepoint(pygame.mouse.get_pos()):
                self.desc_scroll_y = max(0, self.desc_scroll_y - event.y * 20)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if self.back_button.is_hovered:
                    return "back"
                
                # Chuyển trang
                num_pages = (len(self.catalog) + self.items_per_page - 1) // self.items_per_page
                if self.btn_next.is_hovered and self.page < num_pages - 1:
                    self.page += 1
                if self.btn_prev.is_hovered and self.page > 0:
                    self.page -= 1
                
                # Khi click vào vũ khí trong grid
                if self.hovered_weapon:
                    self.selected_weapon = self.hovered_weapon # Chọn để nâng cấp
                    if inv.is_unlocked(self.hovered_weapon):
                        inv.equip_weapon(self.selected_slot, self.hovered_weapon)
                        return "weapon_equipped"
                    
                # Xử lý nâng cấp
                if hasattr(self, 'upgrade_btn_rect') and self.upgrade_btn_rect and self.upgrade_btn_rect.collidepoint(mouse_pos):
                    from apple import AppleManager
                    from arsenal import WEAPON_CATALOG
                    wid = self.hovered_weapon if self.hovered_weapon else self.selected_weapon
                    if not wid: return None
                    
                    lvl = inv.get_level(wid)
                    is_awake = inv.is_awakened(wid)
                    data = WEAPON_CATALOG[wid]
                    
                    next_lvl = None
                    if lvl < data["max_level"]: next_lvl = lvl + 1
                    elif not is_awake: next_lvl = "awaken"
                    
                    if next_lvl and next_lvl in data["upgrades"]:
                        upg_info = data["upgrades"][next_lvl]
                        cost_apple, cost_pepper = upg_info["cost"]
                        
                        if AppleManager.coins >= cost_apple and AppleManager.pepper_coins >= cost_pepper:
                            AppleManager.coins -= cost_apple
                            AppleManager.pepper_coins -= cost_pepper
                            
                            if next_lvl == "awaken":
                                inv.set_awakened(wid, True)
                            else:
                                inv.set_level(wid, next_lvl)
                                
                            AppleManager.save_stats()
                            return "weapon_upgraded"
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
                        from inventory import InventoryManager
                        name = self.input_text.strip()
                        # Lưu 1 file rỗng với tên này (Exp 0, Lvl 1, Wave 1)
                        SaveSystem.get_instance().set_current_slot(self.naming_slot)
                        SaveSystem.get_instance().save_game(
                            name, 0, 1, 1, 0.0, 0.0, 0.0, 0, 0, 
                            InventoryManager.get_instance().save_data()
                        )
                        
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
