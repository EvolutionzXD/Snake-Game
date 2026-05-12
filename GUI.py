import pygame

class ProgressBar:
    def __init__(self, rect, color, bg_color=(30, 30, 35), smooth_color=(255, 255, 255), 
                 border_thickness=4, highlight_color=None, segment_step=0):
        self.rect = pygame.Rect(rect)
        self.color = color
        self.bg_color = bg_color
        self.smooth_color = smooth_color
        self.border_thickness = border_thickness
        self.highlight_color = highlight_color
        self.segment_step = segment_step
        self.last_ratio = -1.0
        
    def draw(self, screen, current_val, max_val, dt, force_lerp=False):
        if max_val <= 0: return
        ratio = max(0.0, min(1.0, current_val / max_val))
        
        if self.last_ratio < 0:
            self.last_ratio = ratio
            
        # Logic Lerp mượt mà
        if force_lerp:
            # Luôn lerp (dùng cho thanh tiến độ màn chơi)
            self.last_ratio += (ratio - self.last_ratio) * 5.0 * dt
        else:
            # Chỉ lerp khi tụt (dùng cho thanh máu)
            if self.last_ratio > ratio:
                self.last_ratio -= (self.last_ratio - ratio) * 5.0 * dt
                if self.last_ratio < ratio: self.last_ratio = ratio
            else:
                self.last_ratio = ratio

        radius = self.rect.height // 2
        # 1. Background
        pygame.draw.rect(screen, self.bg_color, self.rect, border_radius=radius)
        
        # Co lại phần ruột để không bị lòi qua viền dày
        inner_padding = self.border_thickness // 2
        inner_rect = self.rect.inflate(-self.border_thickness, -self.border_thickness)
        inner_radius = max(0, radius - inner_padding)
        
        # 2. Thanh Smooth (hiệu ứng tụt dần)
        fill_ratio = ratio if not force_lerp else self.last_ratio

        if not force_lerp and self.last_ratio > ratio:
            smooth_rect = inner_rect.copy()
            smooth_rect.width = int(inner_rect.width * self.last_ratio)
            if smooth_rect.width >= 1:
                pygame.draw.rect(screen, self.smooth_color, smooth_rect, border_radius=inner_radius)
        
        # 3. Thanh Fill chính
        if fill_ratio > 0:
            fill_rect = inner_rect.copy()
            fill_rect.width = int(inner_rect.width * fill_ratio)
            if fill_rect.width >= 1:
                pygame.draw.rect(screen, self.color, fill_rect, border_radius=inner_radius)
                
                # 4. Vẽ Highlight (Chỉ bo 2 góc trên)
                if self.highlight_color:
                    h_h = int(inner_rect.height * 0.4)
                    h_rect = pygame.Rect(inner_rect.x, inner_rect.y, fill_rect.width, h_h)
                    pygame.draw.rect(screen, self.highlight_color, h_rect, 
                                     border_top_left_radius=inner_radius, 
                                     border_top_right_radius=inner_radius)

                # 5. Vẽ vạch chia (Segments)
                if self.segment_step > 0:
                    for sx in range(self.segment_step, int(fill_rect.width), self.segment_step):
                        pygame.draw.line(screen, (0, 0, 0, 40), 
                                         (inner_rect.x + sx, inner_rect.y), 
                                         (inner_rect.x + sx, inner_rect.y + inner_rect.height), 1)
        
        # 6. Viền (Border) - Vẽ cuối cùng để đè lên ranh giới
        pygame.draw.rect(screen, (10, 10, 15), self.rect, self.border_thickness, border_radius=radius)

class PlayerGUI:
    def __init__(self):
        from resources import ResourceManager
        self.hp_bar = None
        self.stamina_bar = None
        self.exp_bar = None
        self.font = ResourceManager.get_instance().get_font("GrapeSoda", 28)
        self.label_font = ResourceManager.get_instance().get_font("GrapeSoda", 40)
        
        # Animation cho Weapon Slot
        self.slot_scale = 1.0
        self.slot_angle = 0.0
        self.was_holding_attack = False

    def draw(self, screen, player_node, dt):
        if not player_node: return
        
        # Xử lý animation cho Weapon Slot khi click chuột
        is_attacking = pygame.mouse.get_pressed()[0]
        if is_attacking and not self.was_holding_attack:
            self.slot_scale = 1.3 # Phồng to lên khi bắt đầu click
            self.slot_angle = 15.0 # Nghiêng đi một chút
        self.was_holding_attack = is_attacking
        
        # Nội suy về trạng thái bình thường
        self.slot_scale += (1.0 - self.slot_scale) * 12.0 * dt
        self.slot_angle += (0.0 - self.slot_angle) * 12.0 * dt
        
        from apple import AppleManager
        # ... (giữ nguyên phần vẽ các thanh bar)
        
        if not self.hp_bar:
            bar_w = 550*3/4
            bar_h = 30
            bar_x = 20
            bar_y = 35 # Để dành chỗ cho chữ Player ở trên
            # Đổi sang màu xanh lục đặc trưng của Player, thêm highlight trắng mờ
            self.hp_bar = ProgressBar((bar_x, bar_y, bar_w, bar_h), 
                                      color=(40, 180, 40), 
                                      highlight_color=(40, 191, 50),
                                      border_thickness=5)
            
            # Khởi tạo thanh Stamina ngay bên dưới 
            self.stamina_bar = ProgressBar((bar_x, bar_y + bar_h + 5, bar_w, bar_h), 
                                           color=(40, 120, 220), 
                                           highlight_color=(40, 190, 220),
                                           border_thickness=5)
            
            # Khởi tạo thanh EXP
            self.exp_bar = ProgressBar((bar_x, bar_y + bar_h*2 + 10, bar_w, 15), 
                                       color=(220, 180, 0), 
                                       highlight_color=(255, 230, 100),
                                       border_thickness=4)
            
        self.hp_bar.draw(screen, player_node.Hp, player_node.MaxHp, dt)
        self.stamina_bar.draw(screen, AppleManager.stamina, AppleManager.max_stamina, dt)
        self.exp_bar.draw(screen, AppleManager.exp, AppleManager.max_exp, dt)
        
        # Hiển thị Tên
        display_name = getattr(AppleManager, 'username', 'PLAYER').upper()
        label = self.label_font.render(display_name, True, (255, 255, 255))
        label_shadow = self.label_font.render(display_name, True, (0, 0, 0))
        label_pos = (self.hp_bar.rect.x, self.hp_bar.rect.y - 25)
        label_rect = label.get_rect(topleft=label_pos)
        
        screen.blit(label_shadow, (label_rect.x + 2, label_rect.y + 2))
        screen.blit(label, label_rect)
        
        # Hiển thị chỉ số máu
        hp_text = max(0, int(player_node.Hp))
        text = self.font.render(f"{hp_text} / {int(player_node.MaxHp)}", True, (255, 255, 255))
        text_shadow = self.font.render(f"{hp_text} / {int(player_node.MaxHp)}", True, (0, 0, 0))
        text_rect = text.get_rect(center=self.hp_bar.rect.center)
        screen.blit(text_shadow, (text_rect.x + 1, text_rect.y + 1))
        screen.blit(text, text_rect)
        
        # Hiển thị chỉ số Stamina
        stam_text = max(0, int(AppleManager.stamina))
        text_s = self.font.render(f"{stam_text} / {int(AppleManager.max_stamina)}", True, (255, 255, 255))
        text_s_shadow = self.font.render(f"{stam_text} / {int(AppleManager.max_stamina)}", True, (0, 0, 0))
        text_s_rect = text_s.get_rect(center=self.stamina_bar.rect.center)
        screen.blit(text_s_shadow, (text_s_rect.x + 1, text_s_rect.y + 1))
        screen.blit(text_s, text_s_rect)
        
        # Vẽ Weapon Slot
        self._draw_weapon_slot(screen)
        
        # Hiển thị Level
        lvl_text = self.font.render(f"LV {AppleManager.level}", True, (255, 200, 50))

        lvl_shadow = self.font.render(f"LV {AppleManager.level}", True, (0, 0, 0))
        # Căn chỉnh chân chữ (baseline) khớp hoàn toàn với tên PLAYER
        lvl_rect = lvl_text.get_rect(bottomleft=(label_rect.right + 15, label_rect.bottom - 4))
        screen.blit(lvl_shadow, (lvl_rect.x + 1, lvl_rect.y + 1))
        screen.blit(lvl_text, lvl_rect)

    def _draw_weapon_slot(self, screen):
        from weapon import WeaponManager
        from resources import ResourceManager
        weapon = WeaponManager.get_instance().active_weapon
        if not weapon: return
        
        # Cấu hình Slot hình tròn to hơn
        slot_radius = 55
        margin_x = 35
        margin_y = 70 # Tăng margin Y để đẩy toàn bộ cụm lên trên, tránh mất chữ hint
        center_x = screen.get_width() - slot_radius - margin_x
        center_y = screen.get_height() - slot_radius - margin_y
        slot_center = (center_x, center_y)
        
        # 1. Vẽ bóng đổ phía dưới
        pygame.draw.circle(screen, (15, 15, 15), (center_x + 5, center_y + 5), slot_radius)
        
        # 2. Vẽ nền hình tròn
        pygame.draw.circle(screen, (45, 45, 50), slot_center, slot_radius)
        
        # 3. Vẽ viền trắng trước (để vũ khí đè lên viền cho hiệu ứng pop-out)
        pygame.draw.circle(screen, (255, 255, 255), slot_center, slot_radius, 4)
        
        # 4. Vẽ Texture vũ khí (Áp dụng Animation: Pop & Tilt)
        tex = ResourceManager.get_instance().get_texture(weapon.texture_name)
        if tex:
            w, h = tex.get_size()
            # Scale gốc (1.2x đường kính) nhân thêm với animation scale
            total_scale = ((slot_radius * 2 * 1.2) / max(w, h)) * self.slot_scale
            draw_w, draw_h = int(w * total_scale), int(h * total_scale)
            scaled_tex = pygame.transform.scale(tex, (draw_w, draw_h))
            
            # Áp dụng độ nghiêng khi tấn công
            rotated_tex = pygame.transform.rotate(scaled_tex, self.slot_angle)
            
            img_rect = rotated_tex.get_rect(center=slot_center)
            screen.blit(rotated_tex, img_rect)
            
        # 5. Tên vũ khí (viết hoa, đổ bóng)
        name_surf = self.label_font.render(weapon.name.upper(), True, (255, 255, 255))
        name_shadow = self.label_font.render(weapon.name.upper(), True, (0, 0, 0))
        # Thu nhỏ tên lại một chút so với font PLAYER
        name_surf = pygame.transform.scale(name_surf, (int(name_surf.get_width() * 0.6), int(name_surf.get_height() * 0.6)))
        name_shadow = pygame.transform.scale(name_shadow, (int(name_shadow.get_width() * 0.6), int(name_shadow.get_height() * 0.6)))
        
        name_rect = name_surf.get_rect(midbottom=(center_x, center_y - slot_radius - 10))
        screen.blit(name_shadow, (name_rect.x + 2, name_rect.y + 2))
        screen.blit(name_surf, name_rect)

        # 6. Hiển thị phím tắt Q / E (nhỏ ở dưới)
        hint_text = "[Q] PREV   [E] NEXT"
        hint_surf = self.font.render(hint_text, True, (220, 220, 220))
        hint_shadow = self.font.render(hint_text, True, (0, 0, 0))
        hint_rect = hint_surf.get_rect(midtop=(center_x, center_y + slot_radius + 8))
        screen.blit(hint_shadow, (hint_rect.x + 1, hint_rect.y + 1))
        screen.blit(hint_surf, hint_rect)

class CustomCursor:
    def __init__(self):
        self.angle = 0.0
        self.scale = 1.0
        self.timer = 0.0
        self.click_scale = 1.0 # Scale biến thiên khi nhấn chuột
        self.was_holding = False # Lưu trạng thái frame trước
        
    def draw(self, screen, dt):
        from resources import ResourceManager
        tex = ResourceManager.get_instance().get_texture("aim")
        if not tex: return
        
        # Hide default cursor
        if pygame.mouse.get_visible():
            pygame.mouse.set_visible(False)
            
        mouse_pos = pygame.mouse.get_pos()
        
        # Thêm tí "juice": tự quay và scale nhẹ theo thời gian
        self.timer += dt
        self.angle += 90 * dt
        
        # Xử lý Scale Impact: nếu vừa nhấn thì vụt to lên
        is_holding = pygame.mouse.get_pressed()[0]
        if is_holding and not self.was_holding:
            self.click_scale = 1.5
        self.was_holding = is_holding
        
        # Nội suy scale về 1.0 (smooth shrink)
        self.click_scale += (1.0 - self.click_scale) * 15.0 * dt
        
        # pulse nhẹ
        pulse = 0.05 * pygame.math.Vector2(0, 1).rotate_rad(self.timer * 5).y
        current_scale = self.click_scale + pulse
        
        # Transform sprite
        try:
            surf_raw = tex.subsurface((0, 0, 32, 32))
        except:
            surf_raw = tex 
        
        w, h = surf_raw.get_size()
        scaled_size = (int(w * current_scale), int(h * current_scale))
        surf = pygame.transform.scale(surf_raw, scaled_size)
        surf = pygame.transform.rotate(surf, self.angle)
        
        rect = surf.get_rect(center=mouse_pos)
        screen.blit(surf, rect)
