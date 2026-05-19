import pygame
import random
import math
import time

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

# --- EFFECT CLASSES FOR UI ---
class AuraParticle:
    def __init__(self, pos, color):
        self.pos = pygame.math.Vector2(pos)
        # Bay lên với vận tốc ngẫu nhiên
        self.vel = pygame.math.Vector2(random.uniform(-40, 40), random.uniform(-180, -60))
        self.color = color
        self.size = random.uniform(10, 25)
        self.lifetime = 1.0
        self.max_lifetime = 1.0
        
    def update(self, dt):
        self.lifetime -= dt
        self.pos += self.vel * dt
        # Giảm dần kích thước và alpha
        return self.lifetime > 0

    def draw(self, screen, color):
        # Giữ alpha cố định ở mức cao để không bị mờ đi theo thời gian
        alpha = 230 
        # Tạo surface nhỏ để vẽ alpha cho hình tròn
        s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, alpha), (int(self.size), int(self.size)), int(self.size))
        screen.blit(s, (self.pos.x - self.size, self.pos.y - self.size))

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
        self.aura_particles = [] # Danh sách hạt lửa cho Awaken

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
        
        # --- JACKPOT RGB EFFECT ---
        from weapon import WeaponManager, TarotCardWeapon
        active_w = WeaponManager.get_instance().active_weapon
        if isinstance(active_w, TarotCardWeapon) and active_w.jackpot_timer > 0:
            # Tính toán màu RGB xoay vòng
            t = pygame.time.get_ticks() * 0.005
            r = int(127 + 127 * math.sin(t))
            g = int(127 + 127 * math.sin(t + 2.094))
            b = int(127 + 127 * math.sin(t + 4.188))
            rainbow = (r, g, b)
            highlight = (min(255, r+50), min(255, g+50), min(255, b+50))
            
            self.hp_bar.color = rainbow
            self.hp_bar.highlight_color = highlight
            self.stamina_bar.color = rainbow
            self.stamina_bar.highlight_color = highlight
        else:
            # Khôi phục màu gốc
            self.hp_bar.color = (40, 180, 40)
            self.hp_bar.highlight_color = (40, 191, 50)
            self.stamina_bar.color = (40, 120, 220)
            self.stamina_bar.highlight_color = (40, 190, 220)

        # Hiển thị Tên
        display_name = getattr(AppleManager, 'username', 'PLAYER').upper()
        label = self.label_font.render(display_name, True, (255, 255, 255))
        label_shadow = self.label_font.render(display_name, True, (0, 0, 0))
        label_pos = (self.hp_bar.rect.x, self.hp_bar.rect.y - 25)
        label_rect = label.get_rect(topleft=label_pos)
        
        screen.blit(label_shadow, (label_rect.x + 2, label_rect.y + 2))
        screen.blit(label, label_rect)
        
        # --- THÔNG BÁO STATUS POINT ---
        # Dấu "!" nếu có điểm thừa (vẽ bên phải thanh EXP)
        if AppleManager.status_points > 0:
            # Hiệu ứng nhấp nháy cho dấu chấm than
            alpha = int(155 + 100 * math.sin(pygame.time.get_ticks() * 0.01))
            alert_surf = self.label_font.render("!", True, (255, 255, 50))
            alert_surf.set_alpha(alpha)
            alert_pos = (self.exp_bar.rect.right + 15, self.exp_bar.rect.centery - 20)
            screen.blit(alert_surf, alert_pos)
            
            # Text hướng dẫn: Press "I" to upgrade (nằm dưới thanh EXP)
            hint_surf = self.font.render('Press "I" to upgrade', True, (255, 255, 50))
            hint_surf.set_alpha(alpha)
            screen.blit(hint_surf, (self.exp_bar.rect.x + 20, self.exp_bar.rect.bottom + 5))
        
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
        
        # Vẽ Weapon Slots (3 slot)
        self.draw_weapon_effects(screen, dt) # Vẽ hiệu ứng bốc lửa trước
        self._draw_weapon_slots(screen)
        
        # Hiển thị Level
        lvl_text = self.font.render(f"LV {AppleManager.level}", True, (255, 200, 50))

        lvl_shadow = self.font.render(f"LV {AppleManager.level}", True, (0, 0, 0))
        # Căn chỉnh chân chữ (baseline) khớp hoàn toàn với tên PLAYER
        lvl_rect = lvl_text.get_rect(bottomleft=(label_rect.right + 15, label_rect.bottom - 4))
        screen.blit(lvl_shadow, (lvl_rect.x + 1, lvl_rect.y + 1))
        screen.blit(lvl_text, lvl_rect)
        
        # Vẽ UI Tiền Táo
        self._draw_coins(screen)

    def _draw_coins(self, screen):
        from apple import AppleManager
        sw = screen.get_width()
        
        # --- 1. VẼ APPLE COINS ---
        self._draw_coin_pill(screen, sw - 60, 20, "apple", AppleManager.coins, (255, 215, 0))
        
        # --- 2. VẼ ROCK COINS (PEPPER) ---
        # Vẽ ngay bên dưới Apple Coin
        self._draw_coin_pill(screen, sw - 60, 70, "rock", AppleManager.pepper_coins, (210, 245, 255))

    def _draw_coin_pill(self, screen, right_x, top_y, icon_name, amount, text_color):
        from resources import ResourceManager
        tex = ResourceManager.get_instance().get_texture(icon_name)
        if not tex: return

        # Render Text
        amount_str = str(amount)
        text_surf = self.label_font.render(amount_str, True, text_color)
        text_shadow = self.label_font.render(amount_str, True, (0, 0, 0))
        
        # Prepare Icon
        tex_w, tex_h = 32, 32
        # Nếu là rock thì lấy frame đầu
        icon_img = tex.subsurface(pygame.Rect(0, 0, tex_w, tex_h)) if tex.get_width() > 32 else tex
        icon_scale = 1.5
        icon_w, icon_h = int(tex_w * icon_scale), int(tex_h * icon_scale)
        icon_img = pygame.transform.scale(icon_img, (icon_w, icon_h))
        
        # Pill Dimensions
        pill_h = 36
        pill_w = text_surf.get_width() + 45
        pill_x = right_x - pill_w
        pill_rect = pygame.Rect(pill_x, top_y + (icon_h - pill_h)//2, pill_w, pill_h)
        
        # Draw Pill BG
        pill_surf = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        pygame.draw.rect(pill_surf, (20, 20, 20, 180), pill_surf.get_rect(), border_radius=pill_h//2)
        pygame.draw.rect(pill_surf, (255, 255, 255, 100), pill_surf.get_rect(), width=2, border_radius=pill_h//2)
        screen.blit(pill_surf, pill_rect.topleft)
        
        # Draw Icon
        screen.blit(icon_img, (pill_x - icon_w//2, top_y))
        
        # Draw Text
        text_x = pill_x + 25
        text_y = pill_rect.centery - text_surf.get_height()//2
        screen.blit(text_shadow, (text_x + 2, text_y + 2))
        screen.blit(text_surf, (text_x, text_y))

    def draw_weapon_effects(self, screen, dt):
        """Vẽ hiệu ứng bốc lửa và glow cho vũ khí Awakened hoặc khi Jackpot."""
        from weapon import WeaponManager, TarotCardWeapon
        manager = WeaponManager.get_instance()
        active_weapon = manager.active_weapon
        
        # Kiểm tra Jackpot từ TarotCard (nếu có)
        tarot = manager.weapons.get("TarotCard")
        is_jackpot = tarot and getattr(tarot, "jackpot_timer", 0) > 0
        
        # Hiện aura nếu vũ khí đang cầm là Awaken HOẶC đang trong trạng thái Jackpot
        if not (active_weapon and getattr(active_weapon, "is_awakened", False)) and not is_jackpot:
            self.aura_particles.clear()
            return
            
        sw, sh = screen.get_size()
        bx = sw - 100 # Vị trí bx, by khớp với Active Slot ở dưới
        by = sh - 100
        
        # 1. Phát sáng Glow phía sau (RGB Cycle)
        t = time.time() * 2.0
        r = int(127 + 127 * math.sin(t))
        g = int(127 + 127 * math.sin(t + 2))
        b = int(127 + 127 * math.sin(t + 4))
        glow_color = (r, g, b)
        
        glow_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        for radius in range(70, 40, -5):
            alpha = int(30 * (1.0 - (radius-40)/30))
            pygame.draw.circle(glow_surf, (*glow_color, alpha), (100, 100), radius)
        screen.blit(glow_surf, glow_surf.get_rect(center=(bx, by)))
        
        # 2. Sinh hạt lửa/bọt (Aura) - To hơn và ít hơn cho đỡ rối
        for _ in range(2): # Giảm xuống còn 2 hạt mỗi frame
            spawn_pos = (bx + random.uniform(-60, 60), by + random.uniform(20, 50))
            self.aura_particles.append(AuraParticle(spawn_pos, glow_color))
            
        # 3. Cập nhật và vẽ hạt
        for p in self.aura_particles[:]:
            if not p.update(dt):
                self.aura_particles.remove(p)
            else:
                p.draw(screen, glow_color) # Truyền glow_color để đồng bộ tất cả hạt

    def _draw_weapon_slots(self, screen):
        from weapon import WeaponManager
        from inventory import InventoryManager
        from resources import ResourceManager
        
        manager = WeaponManager.get_instance()
        inv = InventoryManager.get_instance()
        
        sw, sh = screen.get_size()
        
        # --- 1. VẼ 3 SLOT DỌC BÊN PHẢI (KIỂU GENSHIN) ---
        slot_size = 50 # Thu nhỏ slot nhỏ
        margin_right = 30
        start_y = sh // 2 - 80
        spacing_y = 65 # Đẩy sát nhau hơn
        
        for i, name in enumerate(manager.slot_names):
            is_active = (inv.current_slot_idx == i)
            
            # Vị trí tâm slot nhỏ
            cx = sw - margin_right - slot_size // 2
            cy = start_y + i * spacing_y
            rect = pygame.Rect(0, 0, slot_size, slot_size)
            rect.center = (cx, cy)
            
            # Tên vũ khí ở bên trái slot
            weapon = manager.weapons.get(name)
            if weapon:
                name_color = (255, 255, 255) if is_active else (150, 150, 150)
                n_surf = self.font.render(weapon.name.upper(), True, name_color)
                # Đổ bóng nhẹ
                n_shadow = self.font.render(weapon.name.upper(), True, (0, 0, 0))
                n_rect = n_surf.get_rect(midright=(cx - slot_size // 2 - 15, cy))
                screen.blit(n_shadow, (n_rect.x + 1, n_rect.y + 1))
                screen.blit(n_surf, n_rect)

            # Nền slot nhỏ - CÓ VIỀN TRẮNG ĐẬM & ĐỔ BÓNG
            pygame.draw.circle(screen, (0, 0, 0, 180), (cx + 3, cy + 3), slot_size // 2) # Shadow
            pygame.draw.circle(screen, (70, 70, 80) if is_active else (40, 40, 45), (cx, cy), slot_size // 2)
            
            # Viền trắng đậm cho tất cả slot nhỏ
            pygame.draw.circle(screen, (255, 255, 255), (cx, cy), slot_size // 2, 4 if is_active else 2)
            
            # Icon vũ khí nhỏ
            if weapon:
                tex = ResourceManager.get_instance().get_texture(weapon.texture_name)
                if tex:
                    tw, th = tex.get_size()
                    # Scale vừa khít hoặc hơi tràn nhẹ (1.0x)
                    s = (slot_size * 1.0) / max(tw, th)
                    icon = pygame.transform.scale(tex, (int(tw * s), int(th * s)))
                    if not is_active: icon.set_alpha(150)
                    screen.blit(icon, icon.get_rect(center=(cx, cy)))
            
            # Số phím tắt [1, 2, 3]
            key_text = f"{i+1}"
            key_surf = self.font.render(key_text, True, (255, 255, 255))
            screen.blit(key_surf, (rect.right - 8, rect.top - 2))

        # --- 2. VẼ CỤM VŨ KHÍ ĐANG CHỌN (GÓC PHẢI DƯỚI) ---
        active_weapon = manager.active_weapon
        if active_weapon:
            big_radius = 55 # Thu nhỏ slot active
            bx = sw - big_radius - 45
            by = sh - big_radius - 45
            
            # Nền bự
            # Đổ bóng đen (Bỏ hình tròn nền theo ý ông)
            pygame.draw.circle(screen, (0, 0, 0, 200), (bx + 5, by + 5), big_radius)
            # Viền SIÊU ĐẬM cho Active Slot
            pygame.draw.circle(screen, (255, 255, 255), (bx, by), big_radius, 8)
            
            # Icon vũ khí bự (có animation)
            tex = ResourceManager.get_instance().get_texture(active_weapon.texture_name)
            if tex:
                tw, th = tex.get_size()
                # Scale vừa phải (1.1x)
                s = ((big_radius * 2 * 1.1) / max(tw, th)) * self.slot_scale
                big_icon = pygame.transform.scale(tex, (int(tw * s), int(th * s)))
                rotated_icon = pygame.transform.rotate(big_icon, self.slot_angle)
                screen.blit(rotated_icon, rotated_icon.get_rect(center=(bx, by)))
                
            # Tên vũ khí bự ở bên trái - TO & RÕ HƠN
            name_surf = self.label_font.render(active_weapon.name.upper(), True, (255, 255, 255))
            name_surf = pygame.transform.scale(name_surf, (int(name_surf.get_width() * 0.8), int(name_surf.get_height() * 0.8)))
            name_rect = name_surf.get_rect(midright=(bx - big_radius - 30, by))
            
            shadow_surf = pygame.transform.scale(self.label_font.render(active_weapon.name.upper(), True, (0, 0, 0)), (name_surf.get_size()))
            screen.blit(shadow_surf, (name_rect.x + 2, name_rect.y + 2))
            screen.blit(name_surf, name_rect)
            
            # Hint cuộn chuột nhỏ lại
            hint_surf = self.font.render("SCROLL", True, (150, 150, 150))
            screen.blit(hint_surf, hint_surf.get_rect(midtop=(bx, by + big_radius + 5)))
            
            # --- 3. VẼ BÀI TAROT (NẾU ĐANG CẦM) ---
            if active_weapon.name == "TarotCard":
                self._draw_card_hand(screen, active_weapon)

    def _draw_card_hand(self, screen, weapon):
        import math
        from resources import get_surfaces
        cards = weapon.hand
        num_cards = len(cards)
        if num_cards == 0: return
        
        # Cấu hình mới: Bẻ góc nhiều hơn và to hơn
        center_x = screen.get_width() - 250
        center_y = screen.get_height() - 150 
        spread_angle = 35 
        start_angle = - (num_cards - 1) * spread_angle / 2
        
        current_time = pygame.time.get_ticks() / 1000.0
        
        for i, card_type in enumerate(cards):
            angle = start_angle + i * spread_angle
            
            # Animation bay bổng nhịp nhàng
            time_offset = current_time * 2.5 + i * 1.0
            float_y = math.sin(time_offset) * 12.0
            
            rad = math.radians(angle - 90) 
            radius = 60 # Dời tâm ra xa hơn chút để không bị dính chùm
            cx = center_x + math.cos(rad) * radius
            cy = center_y + math.sin(rad) * radius + float_y
            
            # Lấy surface có cả outline (scale 6.0 cho to rõ)
            # Sửa lại thứ tự: (name, frame, base_scale, scale_mult, angle, flash, outline)
            outline_surf, sprite_surf = get_surfaces("card_visual", card_type, 6.0, 1.0, angle, 0, True)
            
            if sprite_surf:
                # Vẽ Outline trước
                if outline_surf:
                    rect_o = outline_surf.get_rect(center=(cx, cy))
                    screen.blit(outline_surf, rect_o)
                # Vẽ Sprite chính lên trên
                rect_s = sprite_surf.get_rect(center=(cx, cy))
                screen.blit(sprite_surf, rect_s)

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
