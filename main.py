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
from screens import MainMenu

pygame.init()

class GameManager:
    def __init__(self):
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.is_paused = False
        self.fps_counter = FPSCounter()
        self.player_gui = PlayerGUI()
        self.cursor = CustomCursor()
        
        self.state = "MENU" # Trạng thái bắt đầu
        self.main_menu = MainMenu(self.screen_width, self.screen_height)
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
        pause_font = pygame.font.SysFont("Impact", 80)
        self.pause_text = pause_font.render("PAUSED", True, (255, 255, 255))
        self.pause_text_rect = self.pause_text.get_rect(center=(self.screen_width/2, self.screen_height/2))

    def setup(self):
        # Reset các biến game khi bắt đầu màn chơi mới
        self.seed = random.randint(0, 1000000)
   
        AppleManager.Spawn((600.0, 400.0))
        self.snakes = []
        self.camera = pygame.math.Vector2(AppleManager.GetPosition() - pygame.math.Vector2(self.screen_width/2, self.screen_height/2))

    def run(self):
        # Load tất cả sprite từ đầu để Menu có thể sử dụng (ví dụ: Custom Cursor)
        ResourceManager.get_instance().load_all_sprites("assets/sprite")
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
                
            self.drawing(dt)
            
        pygame.quit()

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
                
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                    if self.state == "PLAYING":
                        self.is_paused = not self.is_paused
            
            if self.state == "MENU":
                action = self.main_menu.handle_event(event)
                if action == "start_game":
                    self.setup() # Load tài nguyên và bắt đầu
                    self.state = "PLAYING"
                elif action == "quit":
                    self.running = False
            
            if self.state == "PLAYING":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3: # Right click
                        AppleManager.Dash()

    def spawning(self, dt):
        self.spawn_timer -= dt
        spawn_rate = 0.1 if len(self.snakes) <= 15 else 20
        self.spawn_timer = min(self.spawn_timer, spawn_rate)
        if self.spawn_timer <= 0:

            player_pos = AppleManager.GetPosition()
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(800, 1200)
            spawn_pos = player_pos + pygame.math.Vector2(math.cos(angle) * distance, math.sin(angle) * distance)
            
            try:
                snake_configs = [
                    config.GetNormalSnakeConfig,
                    config.GetFastSnakeConfig,
                    config.GetTankSnakeConfig
                ]
                chosen_config_func = random.choice(snake_configs)
                new_snake = Snake(spawn_pos, chosen_config_func())
            except (AttributeError, ImportError):
                new_snake = Snake(spawn_pos, config.DefaultSnakeConfig())
            
            self.snakes.append(new_snake)            
            spawn_rate = 0.1 if len(self.snakes) <= 15 else 20
            self.spawn_timer = spawn_rate

    def processing(self, dt):
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
            
            mouse_pos = pygame.mouse.get_pos()
            world_mouse = pygame.math.Vector2(mouse_pos) + self.camera
            WeaponManager.get_instance().attack(AppleManager.GetPosition(), world_mouse, is_holding=is_trying_to_attack)

            self.mouse_dummy.position = AppleManager.GetPosition()
            
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
                    self.snakes[i].attract(best_target, 0.1)
                
                # Cày xéo lẫn nhau (Snake bầy đàn)
                for j in range(len(self.snakes)):
                    if i == j: continue
                    head_j = self.snakes[j].GetHead()
                    if head_j:
                        diff = head.position - head_j.position
                        diff_sq = diff.length_squared()
                        if diff_sq < 150*150: 
                            self.snakes[i].attract(head_j, -0.02)
                
            AppleManager.Process(dt)
            process_physics_and_collisions(dt)
            EnvironmentalManager.get_instance().process(dt)
            ParticleManager.get_instance().update(dt)

    def drawing(self, dt):
        shaken_camera = self.camera + CameraShake.get_instance().get_offset()
        self.screen.fill((200, 200, 200))            
        TileManager.get_instance().process_and_draw(self.screen, shaken_camera)
        
        if not self.is_paused and EffectManager.get_instance().is_hitstopping():
            stop_overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            stop_overlay.fill((0, 0, 0, 80)) 
            self.screen.blit(stop_overlay, (0, 0))            
            
        # --- HỆ THỐNG Y-SORTING TỐI ƯU ---
        apple_node_ref = AppleManager.apple_node
        node_to_snake_head_y = {}
        node_to_depth = {}
        
        for s in self.snakes:
            if not s.nodes: continue
            head_y = s.nodes[0].position.y
            for idx, node in enumerate(s.nodes):
                nid = id(node)
                node_to_snake_head_y[nid] = head_y
                node_to_depth[nid] = idx # 0 là đầu, tăng dần là đuôi
        
        def get_render_priority(node):
            # Các layer đặc biệt luôn nằm trên cùng
            if node.textureName == "projectile":  return 2000000
            if node.textureName == "sword air dash": return 2100000
            if node is apple_node_ref: return node.position.y + 100000 # Táo (Player) luôn ưu tiên cao hơn chút trong cùng mức Y
            
            # Lấy Y gốc
            base_y = node.position.y
            
            # Nếu là đốt rắn, dùng Y của đầu để tính toán layer
            nid = id(node)
            if nid in node_to_snake_head_y:
                base_y = node_to_snake_head_y[nid]
                # Trong cùng 1 con rắn, vẽ từ đuôi (depth cao) đến đầu (depth 0)
                # Đuôi có priority thấp hơn đầu
                depth = node_to_depth.get(nid, 0)
                return base_y - (depth * 0.01) 
                
            return base_y

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
        drawhitbox.draw_node_hitboxes(self.screen, shaken_camera, active_nodes)
        self.player_gui.draw(self.screen, AppleManager.apple_node, dt)
        self.cursor.draw(self.screen, dt)
        self.fps_counter.draw(self.screen, self.clock, len(active_nodes), len(self.snakes), len(EnvironmentalManager.get_instance().active_objects))

        if self.is_paused:
            self.screen.blit(self.pause_overlay, (0, 0))
            self.screen.blit(self.pause_text, self.pause_text_rect)
            
        vfx_dt = dt if not self.is_paused else 0
        VFXManager.get_instance().apply_post_processing(self.screen)
        
        # Vẽ Menu đè lên trên cùng nếu ở trạng thái MENU
        if self.state == "MENU":
            self.main_menu.draw(self.screen, dt)
            
        self.cursor.draw(self.screen, dt) # Vẽ cursor trên cả Menu
        pygame.display.flip()

if __name__ == "__main__":
    GameManager().run()