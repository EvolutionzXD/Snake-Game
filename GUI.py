import pygame

class ProgressBar:
    def __init__(self, rect, color, bg_color=(50, 50, 50), smooth_color=(255, 200, 0)):
        self.rect = pygame.Rect(rect)
        self.color = color
        self.bg_color = bg_color
        self.smooth_color = smooth_color
        self.last_ratio = -1.0 # Bắt đầu ở -1 để snap ngay khung đầu tiên
        
    def draw(self, screen, current_val, max_val, dt):
        if max_val <= 0: return
        
        ratio = max(0.0, min(1.0, current_val / max_val))
        
        if self.last_ratio < 0:
            self.last_ratio = ratio
            
        # Nội suy tiến dầm về ratio hiện tại
        if self.last_ratio > ratio:
            self.last_ratio -= (self.last_ratio - ratio) * 5.0 * dt
            if self.last_ratio < ratio:
                self.last_ratio = ratio
        elif self.last_ratio < ratio:
            self.last_ratio = ratio # Nếu hồi máu thì thanh vụt đầy lên ngay lập tức
                
        # Background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        
        # Thanh smooth lastHP (Chậm chạp tụt xuống sau khi nhận sát thương)
        smooth_rect = self.rect.copy()
        smooth_rect.width = int(self.rect.width * self.last_ratio)
        pygame.draw.rect(screen, self.smooth_color, smooth_rect)
        
        # Thanh current HP
        fill_rect = self.rect.copy()
        fill_rect.width = int(self.rect.width * ratio)
        pygame.draw.rect(screen, self.color, fill_rect)
        
        # Viền
        pygame.draw.rect(screen, (20, 20, 20), self.rect, 3)

class PlayerGUI:
    def __init__(self):
        self.hp_bar = None
        self.stamina_bar = None
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.label_font = pygame.font.SysFont("Arial", 18, bold=True)
        
    def draw(self, screen, player_node, dt):
        if not player_node: return
        
        from apple import AppleManager
        
        if not self.hp_bar:
            bar_w = 250
            bar_h = 20
            bar_x = 20
            bar_y = 35 # Để dành chỗ cho chữ Player ở trên
            # Đổi sang màu xanh lục đặc trưng của Player, smooth màu trắng
            self.hp_bar = ProgressBar((bar_x, bar_y, bar_w, bar_h), color=(40, 200, 40), smooth_color=(255, 255, 255))
            
            # Khởi tạo thanh Stamina ngay bên dưới 
            self.stamina_bar = ProgressBar((bar_x, bar_y + bar_h + 5, bar_w - 50, bar_h - 6), color=(40, 150, 255), smooth_color=(255, 255, 255))
            
        self.hp_bar.draw(screen, player_node.Hp, player_node.MaxHp, dt)
        self.stamina_bar.draw(screen, AppleManager.stamina, AppleManager.max_stamina, dt)
        
        # Hiển thị Tên
        label = self.label_font.render("PLAYER", True, (255, 255, 255))
        label_shadow = self.label_font.render("PLAYER", True, (0, 0, 0))
        screen.blit(label_shadow, (self.hp_bar.rect.x + 2, self.hp_bar.rect.y - 23))
        screen.blit(label, (self.hp_bar.rect.x, self.hp_bar.rect.y - 25))
        
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
        
        # Kết hợp với hiệu ứng pulse nhẹ cũ để vẫn có cảm giác sống động (hoặc bỏ hẳn để tối giản)
        pulse = 0.05 * pygame.math.Vector2(0, 1).rotate_rad(self.timer * 5).y
        current_scale = self.click_scale + pulse
        
        # Dùng frame 1 (hoặc toàn bộ ảnh nếu không phải sprite sheet)
        # Vì ảnh của ông giờ là 64x32 nên tui vẫn cắt lấy frame 1 (32x32) cho chuẩn size
        try:
            surf_raw = tex.subsurface((0, 0, 32, 32))
        except:
            surf_raw = tex 
        
        # Transform sprite
        w, h = surf_raw.get_size()
        scaled_size = (int(w * current_scale), int(h * current_scale))
        surf = pygame.transform.scale(surf_raw, scaled_size)
        surf = pygame.transform.rotate(surf, self.angle)
        
        rect = surf.get_rect(center=mouse_pos)
        
        # Draw shadow
        # shadow_surf = surf.copy()
        # shadow_surf.fill((0, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
        # screen.blit(shadow_surf, (rect.x + 4, rect.y + 4))
        
        # Draw main cursor
        screen.blit(surf, rect)
