import pygame
import random
import math
from resources import ResourceManager
from apple import AppleManager
from snake_entity import Snake
from entity import Node, process_physics_and_collisions, active_nodes
from config import GetSwordAirDashConfig
from fps import FPSCounter
from tile import TileManager, EnvironmentalManager
import drawhitbox
from GUI import PlayerGUI, CustomCursor
from effects import CameraShake, EffectManager
from projectile import ProjectileManager
from weapon import WeaponManager
from particle import ParticleManager
import config
from vfx import VFXManager
from screens import MainMenu, PauseMenu, GameOverMenu, LevelUpMenu, SaveSelectMenu
from grid import GridManager
from debug import DebugManager
from stage import StageManager
from settings_ui import SettingsScreen
import upgrade
from save_system import SaveSystem

pygame.init()

class GameManager:
    def __init__(self):
        self.screen_width = 1400
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.is_paused = False
        # Load tài nguyên ngay từ đầu để các thành phần GUI có thể lấy font/texture
        ResourceManager.get_instance().load_all_sprites("assets/sprite")
        ResourceManager.get_instance().load_all_fonts("assets/font")

        self.fps_counter = FPSCounter()
        self.player_gui = PlayerGUI()
        self.cursor = CustomCursor()
        
        self.state = "SAVE_SELECT" # Trạng thái bắt đầu
        self.settings_previous_state = "MENU"
        self.save_select_menu = SaveSelectMenu(self.screen_width, self.screen_height)
        self.main_menu = MainMenu(self.screen_width, self.screen_height)
        self.pause_menu = PauseMenu(self.screen_width, self.screen_height)
        self.game_over_menu = GameOverMenu(self.screen_width, self.screen_height)
        self.settings_menu = SettingsScreen(self.screen_width, self.screen_height)
        self.level_up_menu = LevelUpMenu(self.screen_width, self.screen_height)
        self.camera = pygame.math.Vector2(0, 0) # Khởi tạo camera mặc định để tránh crash
        
        self.running = False
        self.snakes = []
        self.spawn_timer = 0.0
        
        self.mouse_dummy = Node((0,0)) 
        self.mouse_dummy.is_dummy = True 
        self.seed = 0
        # Pre-bake Pause overlay một lần, không tạo lại mỗi frame
        self.pause_overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.pause_overlay.fill((0, 0, 0, 150))
        pause_font = ResourceManager.get_instance().get_font("GrapeSoda", 120)
        self.pause_text = pause_font.render("PAUSED", True, (255, 255, 255))
        self.pause_text_rect = self.pause_text.get_rect(center=(self.screen_width/2, self.screen_height/2))
        
        # Pre-bake Stop overlay
        self.stop_overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.stop_overlay.fill((0, 0, 0, 80))

    def setup(self):
        # Reset các biến game khi bắt đầu màn chơi mới
        self.seed = random.randint(0, 1000000)
        # Sử dụng seed để kết quả random tọa độ là duy nhất cho mỗi ván
        rng = random.Random(self.seed)
        
        # Ngẫu nhiên vị trí bắt đầu trong phạm vi rộng (ví dụ từ -2000 đến 2000)
        start_x = rng.uniform(-2000, 2000)
        start_y = rng.uniform(-2000, 2000)
   
        AppleManager.Spawn((start_x, start_y))
        self.snakes = []
        # Khởi tạo camera ngay tại vị trí Táo vừa mọc
        self.camera = pygame.math.Vector2(start_x - self.screen_width/2, start_y - self.screen_height/2)

    def run(self):
        self.running = True
        
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            self.handle_events()
            
            if self.state == "PLAYING":
                if not self.is_paused:
                    self.spawning(dt)
                    self.processing(dt)
            elif self.state == "MENU":
                # Logic cho Menu nếu cần thêm gì đó ngoài drawing
                pass
            elif self.state == "SETTINGS":
                self.settings_menu.update(pygame.mouse.get_pos(), dt)
                
            self.drawing(dt)
            
        pygame.quit()

    def reset_game(self):
        self.snakes.clear()
        import entity
        entity.active_nodes.clear()
        ParticleManager.get_instance().clear()
        EnvironmentalManager.get_instance().active_objects.clear()
        AppleManager.apple_node = None
        StageManager.get_instance().reset()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: WeaponManager.get_instance().switch_weapon("Pistol")
                if event.key == pygame.K_2: WeaponManager.get_instance().switch_weapon("SMG")
                if event.key == pygame.K_3: WeaponManager.get_instance().switch_weapon("AirSword")
                if event.key == pygame.K_4: WeaponManager.get_instance().switch_weapon("FlameThrower")
                if event.key == pygame.K_5: WeaponManager.get_instance().switch_weapon("StarPlatinum")
                if event.key == pygame.K_6: WeaponManager.get_instance().switch_weapon("FlameExtinguisher")
                if event.key == pygame.K_7: WeaponManager.get_instance().switch_weapon("RealitySlash") 
                
                if event.key == pygame.K_q: WeaponManager.get_instance().cycle_weapon(-1)
                if event.key == pygame.K_e: WeaponManager.get_instance().cycle_weapon(1)  
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                    if self.state == "PLAYING":
                        self.is_paused = not self.is_paused
                        if not self.is_paused:
                            self.pause_menu.confirming_quit = False # Tắt xác nhận nếu unpause
                    elif self.state == "SETTINGS":
                        self.state = self.settings_previous_state
            
            if event.type == pygame.MOUSEWHEEL:
                if self.state == "PLAYING" and not self.is_paused:
                    # event.y > 0 là cuộn lên (Next), event.y < 0 là cuộn xuống (Prev)
                    # Đảo ngược lại để cảm giác cuộn xuống là tiến tới trong danh sách
                    WeaponManager.get_instance().cycle_weapon(-event.y)
            
            if self.state == "SAVE_SELECT":
                action = self.save_select_menu.handle_event(event)
                if action in ["save_1", "save_2", "save_3"]:
                    slot = int(action[-1])
                    SaveSystem.get_instance().set_current_slot(slot)
                    save_data = SaveSystem.get_instance().load_game()
                    
                    # Cập nhật data
                    AppleManager.load_data(save_data)
                    StageManager.get_instance().max_unlocked_wave = save_data.get("unlocked_wave", 1)
                    self.main_menu.update_max_wave(StageManager.get_instance().max_unlocked_wave)
                    self.main_menu.is_level_select_mode = False # Reset mode
                    
                    self.state = "MENU"
                    
            elif self.state == "MENU":
                action = self.main_menu.handle_event(event)
                if action in ["start", "start?"]:
                    StageManager.get_instance().set_start_wave(self.main_menu.selected_wave)
                    self.setup() # Load tài nguyên và bắt đầu
                    self.state = "PLAYING"
                elif action == "options":
                    self.settings_previous_state = "MENU"
                    self.state = "SETTINGS"
                elif action == "quit":
                    self.running = False
            
            elif self.state == "SETTINGS":
                action = self.settings_menu.handle_event(event)
                if action == "back":
                    self.state = self.settings_previous_state
            
            elif self.state == "GAMEOVER":
                action = self.game_over_menu.handle_event(event)
                if action == "try_again":
                    self.reset_game()
                    self.setup()
                    self.state = "PLAYING"
                elif action == "main_menu":
                    self.reset_game()
                    self.main_menu.update_max_wave(StageManager.get_instance().max_unlocked_wave)
                    self.state = "MENU"
            
            elif self.state == "LEVEL_UP":
                action = self.level_up_menu.handle_event(event)
                if action == "upgrade_selected":
                    AppleManager.pending_level_ups -= 1
                    if AppleManager.pending_level_ups > 0:
                        self.level_up_menu.setup_cards(upgrade.get_available_upgrades())
                    else:
                        self.state = "PLAYING"
            
            if self.state == "PLAYING":
                if self.is_paused:
                    action = self.pause_menu.handle_event(event)
                    if action == "resume":
                        self.is_paused = False
                        self.pause_menu.confirming_quit = False
                    elif action == "options":
                        self.settings_previous_state = "PLAYING"
                        self.state = "SETTINGS"
                    elif action == "confirm_quit":
                        self.is_paused = False
                        AppleManager.save_stats()
                        self.reset_game()
                        self.main_menu.update_max_wave(StageManager.get_instance().max_unlocked_wave)
                        self.state = "MENU"
                        
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3: # Right click
                        AppleManager.Dash()

    def spawning(self, dt):
        stage_manager = StageManager.get_instance()
        active_snakes = sum(1 for s in self.snakes if any(node.Hp > 0 for node in s.nodes))
        
        spawn_rate = stage_manager.get_spawn_rate(active_snakes)
        if spawn_rate >= 9999.0:
            return # Đã đủ rắn cho Wave này
            
        # Khi qua wave mới, spawn_rate sẽ rất nhỏ (0.5s), ta cần ép spawn_timer xuống để đẻ rắn ngay
        self.spawn_timer = min(self.spawn_timer, spawn_rate)
        
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            player_pos = AppleManager.GetPosition()
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(800, 1200)
            spawn_pos = player_pos + pygame.math.Vector2(math.cos(angle) * distance, math.sin(angle) * distance)
            
            wave_config = stage_manager.get_current_wave_config()
            
            try:
                snake_configs = [config.GetNormalSnakeConfig, config.GetFastSnakeConfig, config.GetTankSnakeConfig, config.GetStoneSnakeConfig, config.GetVenomSnakeConfig, config.GetSniperSnakeConfig]
                weights = wave_config["weights"]
                chosen_config_func = random.choices(snake_configs, weights=weights, k=1)[0]
                new_snake = Snake(spawn_pos, chosen_config_func())
                
                # Apply difficulty multiplier (Buff: Máu, Dame, Kích thước - KHÔNG tăng tốc độ)
                diff = wave_config["difficulty"]
                
                for i, n in enumerate(new_snake.nodes):
                    n.MaxHp *= diff
                    n.Hp = n.MaxHp
                    n.damage *= diff
                    # Buff kích thước nhẹ (tăng tối đa 1.5 lần để tránh lag)
                    #size_buff = min(1.5, 1.0 + (diff - 1.0) * 0.2)
                    #n.scaleMultiplier *= size_buff
                    #n.hitbox_radius *= size_buff
            except (AttributeError, ImportError, IndexError):
                new_snake = Snake(spawn_pos, config.DefaultSnakeConfig())
            
            self.snakes.append(new_snake)
            stage_manager.notify_spawned()
            
            # Tính toán lại spawn rate sau khi sinh 1 con
            self.spawn_timer = stage_manager.get_spawn_rate(active_snakes + 1)


    def processing(self, dt):
        # Kiểm tra xem có level up không (Đưa lên đầu để ưu tiên)
        if AppleManager.pending_level_ups > 0:
            self.level_up_menu.setup_cards(upgrade.get_available_upgrades())
            self.state = "LEVEL_UP"
            return # Tạm dừng xử lý frame này để hiện menu

        if AppleManager.apple_node:
            target_cam = AppleManager.apple_node.position - pygame.math.Vector2(self.screen_width/2, self.screen_height/2)
            self.camera = self.camera.lerp(target_cam, 0.1)

        EffectManager.get_instance().update_and_draw(dt, self.screen, self.camera)
        CameraShake.get_instance().update(dt)
        VFXManager.get_instance().update(dt)
        
        if not EffectManager.get_instance().is_hitstopping():
            mouse_buttons = pygame.mouse.get_pressed()
            keys = pygame.key.get_pressed()
            is_trying_to_attack = mouse_buttons[0] or keys[pygame.K_SPACE]
            
            mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
            screen_center = pygame.math.Vector2(self.screen_width/2, self.screen_height/2)
            world_mouse = (mouse_pos - screen_center) / config.GLOBAL_SCALE + self.camera + screen_center
            WeaponManager.get_instance().attack(AppleManager.GetPosition(), world_mouse, is_holding=is_trying_to_attack)

            self.mouse_dummy.position = AppleManager.GetPosition()
            
            # Update Grid for AI (Lấy tất cả projectile - mask 3 và special - mask 4)
            all_projectiles = [n for n in active_nodes if n.mask in (3, 4)]
            all_obstacles = EnvironmentalManager.get_instance().active_objects
            wave_config = StageManager.get_instance().get_current_wave_config()
            GridManager.get_instance().update(self.camera, AppleManager.get_all_apples(), all_projectiles, all_obstacles, difficulty=wave_config["difficulty"])
            
            for snake in self.snakes:
                snake.process(dt)
                
            # Cleanup dead snakes
            self.snakes = [s for s in self.snakes if any(node.Hp > 0 for node in s.nodes)]

            # Tìm tất cả mục tiêu tiềm năng (mask 2 - gồm Player và Táo rơi)
            targets = [n for n in active_nodes if n.mask == 2 and not n.is_dead]
            
            for i in range(len(self.snakes)):
                head = self.snakes[i].GetHead()
                if not head: continue
                
                # Tìm mục tiêu gần nhất
                best_target = None
                best_dist_sq = 99999999 # Vô hạn
                for t in targets:
                    d_sq = head.position.distance_squared_to(t.position)
                    if d_sq < best_dist_sq:
                        best_dist_sq = d_sq
                        best_target = t
                
                # Tấn công mục tiêu gần nhất
                if best_target:
                    self.snakes[i].attract(best_target, 0.1, self.camera)
                
                # Cày xéo lẫn nhau (Snake bầy đàn)
                for j in range(len(self.snakes)):
                    if i == j: continue
                    head_j = self.snakes[j].GetHead()
                    if head_j:
                        diff = head.position - head_j.position
                        if abs(diff.x) < 150 and abs(diff.y) < 150:
                            diff_sq = diff.length_squared()
                            if diff_sq < 150*150: 
                                self.snakes[i].attract(head_j, -0.02, self.camera)
                
            AppleManager.Process(dt)
            process_physics_and_collisions(dt)
            EnvironmentalManager.get_instance().process(dt)
            ParticleManager.get_instance().update(dt)
            
            if AppleManager.apple_node and AppleManager.apple_node.Hp <= 0:
                AppleManager.save_stats()
                self.state = "GAMEOVER"

    def drawing(self, dt):
        shaken_camera = self.camera + CameraShake.get_instance().get_offset()
        self.screen.fill((200, 200, 200))            
        TileManager.get_instance().process_and_draw(self.screen, shaken_camera)
        
        if not self.is_paused and EffectManager.get_instance().is_hitstopping():
            self.screen.blit(self.stop_overlay, (0, 0))            
            
        # --- HỆ THỐNG Y-SORTING TỐI ƯU ---
        apple_node_ref = AppleManager.apple_node
        
        # --- VẼ TIA LAZER SNIPER ---
        from entity import _SCREEN_CENTER, GLOBAL_SCALE
        for snake in self.snakes:
            if getattr(snake, 'behavior', None) == "sniper" and getattr(snake, 'aim_timer', 0) > 0 and getattr(snake, 'aim_target_pos', None):
                start_pos = snake.nodes[0].position
                target_pos = snake.aim_target_pos
                
                # Chuyển đổi tọa độ sang màn hình (screen space)
                cam_offset = shaken_camera + _SCREEN_CENTER
                screen_start = (start_pos - cam_offset) * GLOBAL_SCALE + _SCREEN_CENTER
                
                # Tính toán hướng và kéo dài tia laze ra xa (vô tận)
                direction = target_pos - start_pos
                if direction.length_squared() > 0:
                    extended_target = start_pos + direction.normalize() * 3000
                    screen_target = (extended_target - cam_offset) * GLOBAL_SCALE + _SCREEN_CENTER
                else:
                    screen_target = screen_start
                
                # Vẽ tia laze đỏ mờ (Đậm hơn một chút, clamp alpha tránh lỗi)
                laze_alpha = max(0, min(255, int(100 + (1.5 - snake.aim_timer) * 120)))
                
                # Cảnh báo: Nhấp nháy nhanh khi sắp bắn (< 0.4s)
                if snake.aim_timer < 0.4:
                    if (int(pygame.time.get_ticks() / 50) % 2 == 0):
                        laze_alpha = 255 # Nháy cực sáng
                    else:
                        laze_alpha = 0 # Tắt tạm thời
                
                laze_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                pygame.draw.line(laze_surf, (255, 0, 0, laze_alpha), screen_start, screen_target, 3)
                self.screen.blit(laze_surf, (0, 0))

        def get_render_priority(node):
            # Các layer đặc biệt luôn nằm trên cùng
            if node.textureName == "projectile":  return 2000000
            if node.textureName == "sword air dash": return 2100000
            
            # Lấy Y gốc
            y_val = node.position.y
            if node.snake_head:
                y_val = node.snake_head.position.y - (node.snake_depth * 0.01)
                
            return y_val

        render_nodes = sorted(
            (n for n in active_nodes if n.mask != -1),
            key=get_render_priority
        )

        for node in render_nodes: node.draw_shadow(self.screen, shaken_camera)
        for node in render_nodes: node.draw_outline(self.screen, shaken_camera)
        for node in render_nodes: node.draw_sprite(self.screen, shaken_camera)

        if AppleManager.apple_node:
            weapon_dt = 0 if EffectManager.get_instance().is_hitstopping() else dt
            WeaponManager.get_instance().update_and_draw(self.screen, AppleManager.GetPosition(), shaken_camera, weapon_dt)
        
        ParticleManager.get_instance().draw(self.screen, shaken_camera)
            
        EffectManager.get_instance().update_and_draw(dt, self.screen, shaken_camera)
        
        # Process and draw EXP Orbs (Should ideally be separated, but doing it here is fine)
        StageManager.get_instance().process_and_draw(dt, self.screen, shaken_camera)
        
        DebugManager.draw(self.screen, shaken_camera, active_nodes)
        
        # UI overlays
        self.player_gui.draw(self.screen, AppleManager.apple_node, dt)
        StageManager.get_instance().draw_progress_bar(self.screen, dt)
        self.fps_counter.draw(self.screen, self.clock, len(active_nodes), len(self.snakes), len(EnvironmentalManager.get_instance().active_objects))

        if self.is_paused:
            self.screen.blit(self.pause_overlay, (0, 0))
            self.pause_menu.draw(self.screen, dt)
            
        vfx_dt = dt if not self.is_paused else 0
        VFXManager.get_instance().apply_post_processing(self.screen)
        
        # Vẽ Menu đè lên trên cùng nếu ở trạng thái MENU hoặc SETTINGS
        if self.state == "SAVE_SELECT":
            self.save_select_menu.draw(self.screen, dt)
        elif self.state == "MENU":
            self.main_menu.draw(self.screen, dt)
        elif self.state == "SETTINGS":
            self.settings_menu.draw(self.screen)
        elif self.state == "GAMEOVER":
            score = StageManager.get_instance().killed_snakes
            level = AppleManager.level
            self.game_over_menu.draw(self.screen, dt, score, level)
        elif self.state == "LEVEL_UP":
            self.level_up_menu.draw(self.screen, dt)
            
        self.cursor.draw(self.screen, dt) # Vẽ cursor trên cả Menu
        pygame.display.flip()

if __name__ == "__main__":
    GameManager().run()