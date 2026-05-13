import pygame
import math
import random
import config
from apple import AppleManager
from config import GLOBAL_SCALE
class ExpOrb:
    def __init__(self, pos, value=10):
        """Khởi tạo một orb EXP tại `pos` với giá trị `value`, bắn tạt ra ngẫu nhiên khi vừa rơi."""
        self.position = pygame.math.Vector2(pos)
        self.value = value
        self.speed = 0.0
        self.velocity = pygame.math.Vector2(0, 0)
        
        # Bắn tung ra ngẫu nhiên khi rớt
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(100, 250)
        self.timer = 0.0
        
    def process(self, dt):
        self.timer += dt
        player_pos = AppleManager.GetPosition()
        dist_sq = self.position.distance_squared_to(player_pos)
        
        from settings import SettingsManager
        is_auto_collect = SettingsManager.get_instance().get("gameplay", "auto_collect_exp")
        
        # Hút vào người chơi nếu ở gần HOẶC sau khi nằm trên đất quá 1.0 giây (nếu bật Auto-collect)
        magnet_dist = AppleManager.magnet_radius
        if dist_sq < magnet_dist * magnet_dist or (self.timer > 1.0 and is_auto_collect): 
            self.speed += 1500 * dt
            target_dir = (player_pos - self.position).normalize() if dist_sq > 0 else pygame.math.Vector2(0, 0)
            self.velocity = self.velocity.lerp(target_dir * self.speed, 0.2)
        else:
            # Ma sát làm chậm lại nếu chưa bị hút
            self.velocity *= 0.9 
            
        self.position += self.velocity * dt
        
        # Thu thập nếu chạm vào
        if dist_sq < 40 * 40: 
            AppleManager.add_exp(self.value)
            return True # Bị thu thập
        return False
        
    def draw(self, screen, camera):
        """Vẽ orb EXP lên màn hình dưới dạng vòng tròn xanh ngọc."""
        draw_pos = self.position - camera
        pygame.draw.circle(screen, (50, 255, 150), (int(draw_pos.x), int(draw_pos.y)), 6 * GLOBAL_SCALE)
        pygame.draw.circle(screen, (200, 255, 220), (int(draw_pos.x), int(draw_pos.y)), 3 * GLOBAL_SCALE)

class CoinOrb:
    def __init__(self, pos, value=1):
        """Khởi tạo một orb Coin tại `pos` với giá trị `value`, bắn tạt ra ngẫu nhiên khi vừa rơi."""
        self.position = pygame.math.Vector2(pos)
        self.value = value
        self.speed = 0.0
        self.velocity = pygame.math.Vector2(0, 0)
        
        # Bắn tung ra ngẫu nhiên
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(150, 300)
        self.timer = 0.0
        
    def process(self, dt):
        self.timer += dt
        player_pos = AppleManager.GetPosition()
        dist_sq = self.position.distance_squared_to(player_pos)
        
        from settings import SettingsManager
        is_auto_collect = SettingsManager.get_instance().get("gameplay", "auto_collect_exp")
        
        magnet_dist = AppleManager.magnet_radius
        if dist_sq < magnet_dist * magnet_dist or (self.timer > 1.0 and is_auto_collect): 
            self.speed += 1500 * dt
            target_dir = (player_pos - self.position).normalize() if dist_sq > 0 else pygame.math.Vector2(0, 0)
            self.velocity = self.velocity.lerp(target_dir * self.speed, 0.2)
        else:
            self.velocity *= 0.9 
            
        self.position += self.velocity * dt
        
        if dist_sq < 40 * 40: 
            AppleManager.add_coin(self.value)
            return True
        return False
        
    def draw(self, screen, camera):
        """Vẽ orb Coin lên màn hình dưới dạng vòng tròn vàng."""
        draw_pos = self.position - camera
        pygame.draw.circle(screen, (255, 215, 0), (int(draw_pos.x), int(draw_pos.y)), 6 * GLOBAL_SCALE)
        pygame.draw.circle(screen, (255, 255, 100), (int(draw_pos.x), int(draw_pos.y)), 3 * GLOBAL_SCALE)

class StageManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if not cls._instance: cls._instance = StageManager()
        return cls._instance
        
    def __init__(self):
        self.max_unlocked_wave = 1
        self.start_wave = 1
        from GUI import ProgressBar
        bar_w, bar_h = 750, 26
        bar_x = (1200 - bar_w) // 2
        bar_y = 800 - bar_h - 25
        self.progress_bar_obj = ProgressBar(
            (bar_x, bar_y, bar_w, bar_h),
            color=(0, 100, 200),        
            highlight_color=(20, 150, 255), 
            border_thickness=6,         
            segment_step=50             
        )
        self.reset()
        
    def set_start_wave(self, wave):
        self.start_wave = wave
        self.current_wave = wave

    def reset(self):
        import config
        self.exp_orbs = []
        self.coin_orbs = []
        self.killed_snakes = 0
        self.current_wave = self.start_wave
        
        self.waves = config.WAVES_DATA
        
        self.spawned_snakes = 0
        self.flags_triggered = []
        self.flag_huge_wave_queue = 0
        self.target_kills = self.get_current_wave_config()["total"]
        self.displayed_progress = 0.0
        self.progress_bar_obj.ratio = 0.0
        self.progress_bar_obj.last_ratio = 0.0

    def spawn_exp(self, pos, value=10):
        """Sinh một orb EXP tại vị trí `pos`."""
        self.exp_orbs.append(ExpOrb(pos, value))

    def spawn_coin(self, pos, value=1):
        """Sinh một orb Coin tại vị trí `pos`."""
        self.coin_orbs.append(CoinOrb(pos, value))

    def on_snake_killed(self, pos, max_hp):
        """Gọi khi rắn chết: sinh EXP tứ lệ với MaxHp, 30% cơ hội rơi 1–3 Coin, đếm số rắn giết và kiểm tra điều kiện qua Wave."""
        # Rơi EXP tỉ lệ với máu của quái (10% MaxHp)
        exp_value = max_hp * 0.1
        self.spawn_exp(pos, value=int(exp_value))
        
        # Rơi Tiền (Tỉ lệ 30% rớt từ 1 đến 3 đồng)
        if random.random() < 0.3:
            count = random.randint(1, 3)
            for _ in range(count):
                self.spawn_coin(pos, value=1)
                
        self.killed_snakes += 1
        self.check_flags()
        
        if self.killed_snakes >= self.target_kills:
            self.next_wave()
            
    def next_wave(self):
        """Chuyển sang Wave kế tiếp: reset bộ đếm, cập nhật kỷ lục và lưu game."""
        self.current_wave += 1
        self.killed_snakes = 0
        self.spawned_snakes = 0
        self.flags_triggered = []
        self.flag_huge_wave_queue = 0
        self.target_kills = self.get_current_wave_config()["total"]
        self.displayed_progress = 0.0
        
        if self.current_wave > self.max_unlocked_wave:
            self.max_unlocked_wave = self.current_wave
            
        # Lưu game khi qua màn
        from save_system import SaveSystem
        from apple import AppleManager
        SaveSystem.get_instance().save_game(
            AppleManager.username, AppleManager.exp, AppleManager.level, self.max_unlocked_wave,
            AppleManager.hp_lvl, AppleManager.stamina_lvl, AppleManager.dmg_lvl, AppleManager.coins
        )
        
    def process_and_draw(self, dt, screen, camera):
        """Cập nhật vật lý và vẽ toàn bộ EXP Orb và Coin Orb lên màn hình."""
        alive_exp = []
        for orb in self.exp_orbs:
            if not orb.process(dt):
                alive_exp.append(orb)
        self.exp_orbs = alive_exp
        
        for orb in self.exp_orbs:
            orb.draw(screen, camera)

        alive_coins = []
        for orb in self.coin_orbs:
            if not orb.process(dt):
                alive_coins.append(orb)
        self.coin_orbs = alive_coins
        
        for orb in self.coin_orbs:
            orb.draw(screen, camera)
            
    def get_current_wave_config(self):
        """Trả về cấu hình của Wave hiện tại từ danh sách WAVES_DATA."""
        idx = min(self.current_wave - 1, len(self.waves) - 1)
        return self.waves[idx]

    def check_flags(self):
        """Kiểm tra cấu hình Flag của Wave, kích hoạt Huge Wave khi ngưỡng tiến trình đạt yêu cầu."""
        config = self.get_current_wave_config()
        # Tính toán progress dựa theo 'displayed_progress' để trigger khớp hoàn toàn với visual
        # Ta cần quy đổi displayed_progress (tỉ lệ trên target_kills) sang tỉ lệ trên total gốc
        visual_progress_in_original_scale = self.displayed_progress * (self.target_kills / config["total"])
        
        for flag in config["flags"]:
            if visual_progress_in_original_scale >= flag and flag not in self.flags_triggered:
                self.flags_triggered.append(flag)
                # Kích hoạt Huge Wave: Thêm 1 lượng rắn tương đương 25% tổng số vào hàng chờ sinh nhanh
                bonus_snakes = int(config["total"] * 0.25)
                self.flag_huge_wave_queue += bonus_snakes
                self.target_kills += bonus_snakes 
                

        
    def get_spawn_rate(self, active_snakes_count):
        """Tính thời gian chờ giữa 2 lần sinh rắn dựa theo số rắn đang trên sân và độ khó Wave."""
        config = self.get_current_wave_config()
        
        # Kiểm tra giới hạn số lượng rắn tối đa trên màn hình
        if active_snakes_count >= config.get("max_on_screen", 15):
            return 9999.0
            
        if self.spawned_snakes >= config["total"]:
            # Nếu đã đẻ đủ số lượng của màn thì ngưng
            if self.flag_huge_wave_queue <= 0:
                return 9999.0
                
        if self.flag_huge_wave_queue > 0:
            return 0.1 # Đẻ liên tục rất nhanh cho Huge Wave
            
        # Công thức sinh: Rắn trên sân càng nhiều, tốc độ đẻ càng chậm
        base_rate = 0.5
        delay_per_snake = 0.15
        rate = base_rate + (active_snakes_count * delay_per_snake)
        return rate / config["difficulty"]
        
    def notify_spawned(self):
        """Thông báo rằng một rắn mới vừa được sinh ra, giảm số rắn trong Huge Wave queue (nếu có)."""
        if self.flag_huge_wave_queue > 0:
            self.flag_huge_wave_queue -= 1
        else:
            self.spawned_snakes += 1
            
    def draw_progress_bar(self, screen, dt):
        """Vẽ thanh tiến trình Wave, các cờ mốc (Flags), chữ "Wave N" lên màn hình."""
        config = self.get_current_wave_config()
        
        # 1. Vẽ thanh tiến trình bằng đối tượng ProgressBar (OOP)
        self.progress_bar_obj.draw(screen, self.killed_snakes, self.target_kills, dt, force_lerp=True)
        
        # Cập nhật hiển thị để đồng bộ với Flags
        self.displayed_progress = self.progress_bar_obj.last_ratio
        
        # 2. Kiểm tra cờ kích hoạt
        self.check_flags()

        bar_rect = self.progress_bar_obj.rect
        bar_x, bar_y, bar_w, bar_h = bar_rect.x, bar_rect.y, bar_rect.width, bar_rect.height
        # Xóa bỏ phần vẽ thủ công cũ
        
        # Vẽ các cờ (Flags)
        from resources import ResourceManager
        flag_tex_raw = ResourceManager.get_instance().get_texture("flag")
        
        if flag_tex_raw:
            # Thu nhỏ lại cho vừa vặn
            orig_w, orig_h = flag_tex_raw.get_size()
            # Giả sử ta muốn chiều cao cờ tầm 45px
            target_h = 45
            scale_factor = target_h / orig_h if orig_h > 0 else 1
            scaled_w = int(orig_w * scale_factor)
            flag_tex = pygame.transform.scale(flag_tex_raw, (scaled_w, target_h))
            
            for flag in config["flags"]:
                flag_x = bar_x + bar_w * flag
                
                if flag in self.flags_triggered:
                    # Cờ đã đi qua thì mờ đi và ngừng lơ lửng
                    passed_flag = flag_tex.copy()
                    passed_flag.set_alpha(100) # Chỉ làm mờ, không fill để tránh lỗi hình vuông đen
                    rect = passed_flag.get_rect(center=(flag_x, bar_y + bar_h // 2))
                    screen.blit(passed_flag, rect)
                else:
                    # Cờ chưa tới thì lơ lửng chậm rãi
                    bob_y = math.sin(pygame.time.get_ticks() / 300.0) * 3.0
                    rect = flag_tex.get_rect(center=(flag_x, bar_y + bar_h // 2 + bob_y))
                    screen.blit(flag_tex, rect)
        else:
            for flag in config["flags"]:
                flag_x = bar_x + bar_w * flag
                pygame.draw.line(screen, (200, 200, 200), (flag_x, bar_y - 10), (flag_x, bar_y + bar_h), 2)
                if flag in self.flags_triggered:
                    pygame.draw.polygon(screen, (100, 50, 50), [(flag_x, bar_y - 5), (flag_x + 12, bar_y), (flag_x, bar_y + 5)])
                else:
                    pygame.draw.polygon(screen, (255, 50, 50), [(flag_x, bar_y - 10), (flag_x + 15, bar_y - 2), (flag_x, bar_y + 5)])
            
        # Text "Wave N"
        from resources import ResourceManager
        font = ResourceManager.get_instance().get_font("GrapeSoda", 32)
        text = font.render(f"WAVE {self.current_wave}", True, (255, 255, 255))
        text_shadow = font.render(f"WAVE {self.current_wave}", True, (0, 0, 0))
        
        # Đặt chữ WAVE N ở giữa, phía trên thanh tiến trình
        text_rect = text.get_rect(midbottom=(bar_x + bar_w // 2, bar_y - 5))
        screen.blit(text_shadow, (text_rect.x + 2, text_rect.y + 2))
        screen.blit(text, text_rect)
