import pygame
import math
import noise
import time
import random
from entity import Node, active_nodes
from resources import get_surfaces
from config import GetRockConfig, GetTreeConfig, GLOBAL_SCALE

TILE_SIZE = 64.0
GRID_COLS = int(24 / GLOBAL_SCALE)
GRID_ROWS = int(18 / GLOBAL_SCALE)
TOTAL_WIDTH = TILE_SIZE * GRID_COLS
TOTAL_HEIGHT = TILE_SIZE * GRID_ROWS

def get_terrain_type(grid_x, grid_y):
    # Dùng Scale nhỏ lại rất lới để tạo thành các VÙNG BIOME (quần xã) khổng lồ
    # Càng nhỏ thì bãi đá/cỏ càng rộng và liền mạch.
    scale = 0.05
    
    # Octaves cao giúp rìa biome có độ gồ ghề ngẫu nhiên một chút
    noise_val = noise.pnoise2(grid_x * scale, 
                              grid_y * scale, 
                              octaves=3, 
                              persistence=0.5, 
                              lacunarity=2.0)
    
    # Giá trị noise thường nằm trong khoảng -1.0 -> 1.0
    if noise_val > 0.4:  # Tăng ngưỡng lên để Cỏ (grass) chiếm phần lớn diện tích
        tex = "stone"
    else:
        tex = "grass"
        
    frame_idx = 0 if (grid_x + grid_y) % 2 == 0 else 1
    return tex, frame_idx

class EnvironmentalManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None: cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.broken_objects = {}  # {(grid_x, grid_y): respawn_time}
        self.spawned_entities = {} # {(grid_x, grid_y): Node}
        self.active_objects = []   # [Node] - Danh sách các vật thể đang sống để update

    def get_object_type(self, gx, gy, terrain_type):
        # Dùng chung 1 noise để quyết định có mọc vật thể hay không
        scale = 0.12
        val = noise.pnoise2(gx * scale + 5000, gy * scale + 5000, octaves=2)
        
        # Ngưỡng vật thể (tăng lên để thưa hơn, tui để 0.35 cho thoáng)
        if val > 0.35: 
            if terrain_type == "stone": return "rock"
            if terrain_type == "grass": return "tree"
        return None

    def update_respawns(self):
        curr = time.time()
        to_remove = []
        for pos, respawn_t in self.broken_objects.items():
            if curr >= respawn_t:
                to_remove.append(pos)
        for pos in to_remove:
            del self.broken_objects[pos]

    def spawn_at(self, gx, gy, pos, terrain_type):
        # Kiểm tra nếu đang trong thời gian chờ respawn
        if (gx, gy) in self.broken_objects:
            if time.time() < self.broken_objects[(gx, gy)]:
                return None # Chưa đến lúc mọc lại
            else:
                del self.broken_objects[(gx, gy)] # Đã đủ thời gian, xóa khỏi danh sách đen

        obj_type = self.get_object_type(gx, gy, terrain_type)
        if not obj_type: return

        # Tạo Entity mới và áp dụng Config từ config.py
        obj = Node(pos)
        if obj_type == "rock":
            obj.apply_config(GetRockConfig())
        else:
            obj.apply_config(GetTreeConfig())
        
        # Đăng ký quản lý
        self.spawned_entities[(gx, gy)] = obj
        self.active_objects.append(obj)
        return obj

    def on_object_broken(self, obj):
        # Tìm tọa độ grid của object này
        found_pos = None
        for k, v in self.spawned_entities.items():
            if v == obj:
                found_pos = k
                break
        
        if found_pos:
            self.broken_objects[found_pos] = time.time() + 30.0
            del self.spawned_entities[found_pos]
            
        if obj in self.active_objects:
            self.active_objects.remove(obj)

    def unregister_object(self, obj):
        """Gỡ bỏ vật thể (dùng khi cuộn màn hình)"""
        if obj in self.active_objects:
            self.active_objects.remove(obj)
        keys_to_del = [k for k, v in self.spawned_entities.items() if v == obj]
        for k in keys_to_del: del self.spawned_entities[k]

    def process(self, dt):
        """Hàm cập nhật riêng cho các vật thể tĩnh (lerp về gốc và check nổ)"""
        import random
        from particle import ParticleManager
        from entity import Node
        pm = ParticleManager.get_instance()
        
        for obj in self.active_objects[:]:
            if obj.is_dead or obj.Hp <= 0:
                # XỬ LÝ NỔ VÀ RƠI ĐỒ (Chỉ khi Hp <= 0 thật sự)
                if obj.Hp <= 0:
                    color = (120, 120, 120) if obj.textureName == "rock" else (100, 70, 40)
                    pm.spawn(
                        pos=obj.position, count=15, color=color, alpha=200,
                        size_range=(4, 12), speed_range=(100, 300),
                        lifetime=0.6, gravity=400.0,
                    )
                    # Rơi táo (mask 2)
                    loot = Node(obj.position.copy())
                    loot.textureName = "apple"
                    loot.scaleMultiplier = 0.5
                    loot.MaxHp = 1.0; loot.Hp = 1.0; loot.mask = 2
                    loot.lifetime = 15.0 # Táo sẽ biến mất sau 15 giây nếu không được ăn
                    loot.velocity = pygame.math.Vector2(random.uniform(-150, 150), random.uniform(-150, 150))
                
                self.on_object_broken(obj)
                continue
            
            # LERP QUAY VỀ VỊ TRÍ CŨ (nếu bị đẩy lệch)
            dist_sq = obj.position.distance_squared_to(obj.origin_pos)
            if dist_sq > 0.1:
                obj.position = obj.position.lerp(obj.origin_pos, min(8.0 * dt, 1.0))

class Tile(Node):
    def __init__(self, pos):
        super().__init__(pos)
        self.textureWidth = 32.0
        self.textureHeight = 32.0
        self.scaleMultiplier = 0.5
        self.hasOutline = False
        self.hasShadow = False
        self.mask = -1
        self.maskOut = (-2,)
        self.current_obj = None # Vật thể đang đứng trên tile này
        self.update_terrain()

    def update_terrain(self):
        grid_x = int(round(self.position.x / TILE_SIZE))
        grid_y = int(round(self.position.y / TILE_SIZE))
        tex, f_idx = get_terrain_type(grid_x, grid_y)
        self.textureName = tex
        self.MinFrame = f_idx
        self.MaxFrame = f_idx
        self.frame = 0.0
        
        # --- AUTO-TILING TỐI ƯU ---
        # Tính toán luôn viền (borders) cho ô cỏ nếu bên cạnh nó là ô đá.
        # Chạy 1 lần duy nhất lúc tạo/wrap tile nên ko lag frame!
        self.borders = []
        if (grid_x + grid_y) % 2 == 0:
            # Gỉa sử spritesheet stone_border.png có 4 frame: 0=Up, 1=Right, 2=Down, 3=Left
            if get_terrain_type(grid_x, grid_y - 1)[0] == "stone":
                self.borders.append(0)
            if get_terrain_type(grid_x, grid_y + 1)[0] == "stone":
                self.borders.append(1)
            if get_terrain_type(grid_x - 1, grid_y)[0] == "stone":
                self.borders.append(2)
            if get_terrain_type(grid_x + 1, grid_y)[0] == "stone":
                self.borders.append(3)

        # --- SINH VẬT THỂ TĨNH ---
        mgr = EnvironmentalManager.get_instance()
        # Xóa vật thể cũ nếu có (khi wrap tile)
        if self.current_obj:
            mgr.unregister_object(self.current_obj)
            self.current_obj.is_dead = True 
            self.current_obj = None
            
        mgr = EnvironmentalManager.get_instance()
        self.current_obj = mgr.spawn_at(grid_x, grid_y, self.position.copy(), self.textureName)

    def process(self, camera, screen_width, screen_height):
        cam_center_x = camera.x + screen_width / 2.0
        cam_center_y = camera.y + screen_height / 2.0
        
        diff_x = self.position.x - cam_center_x
        diff_y = self.position.y - cam_center_y
        
        half_width = TOTAL_WIDTH / 2.0
        half_height = TOTAL_HEIGHT / 2.0
        
        position_changed = False
        
        if diff_x < -half_width:
            self.position.x += TOTAL_WIDTH
            position_changed = True
        elif diff_x > half_width:
            self.position.x -= TOTAL_WIDTH
            position_changed = True
            
        if diff_y < -half_height:
            self.position.y += TOTAL_HEIGHT
            position_changed = True
        elif diff_y > half_height:
            self.position.y -= TOTAL_HEIGHT
            position_changed = True
            
        if position_changed:
            self.update_terrain()

    def draw_sprite(self, screen, camera):
        target = camera + pygame.math.Vector2(600, 400)
        draw_pos = (self.position - target) * GLOBAL_SCALE + pygame.math.Vector2(600, 400)
        
        # Viewport Culling chung cho cả Tile và Border
        s = 64 * self.scaleMultiplier * GLOBAL_SCALE * 3 # Kích thước an toàn
        if draw_pos.x + s < 0 or draw_pos.x - s > screen.get_width() or draw_pos.y + s < 0 or draw_pos.y - s > screen.get_height():
            return
            
        # Vẽ base tile (cỏ/đá tĩnh)
        super().draw_sprite(screen, camera)
        
        # Load và vẽ viền lấn (autotile border) lên trên
        if hasattr(self, 'borders') and self.borders:
            for b_idx in self.borders:
                _, border_surf = get_surfaces("stone_border", b_idx, 4.0, self.scaleMultiplier, 0.0, 0.0, False)
                if border_surf:
                    b_pos = draw_pos + pygame.math.Vector2(self.textureOffsetX, self.textureOffsetY) * GLOBAL_SCALE
                    rect = border_surf.get_rect(center=(b_pos.x, b_pos.y))
                    screen.blit(border_surf, rect)

class TileManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.tiles = []
        for x in range(GRID_COLS):
            for y in range(GRID_ROWS):
                pos = (x * TILE_SIZE, y * TILE_SIZE)
                tile = Tile(pos)
                self.tiles.append(tile)

    def process_and_draw(self, screen, camera):
        if not hasattr(self, 'font'):
            self.font = pygame.font.SysFont("Arial", 16, bold=True)
            
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        
        # Cập nhật respawn định kỳ
        EnvironmentalManager.get_instance().update_respawns()
        
        for tile in self.tiles:
            tile.process(camera, screen_w, screen_h)
            tile.draw_sprite(screen, camera)
            
            # Nếu ô này đang trống (vừa bị phá hoặc vừa wrap), thử hồi sinh vật thể
            if tile.current_obj is None:
                gx = int(round(tile.position.x / TILE_SIZE))
                gy = int(round(tile.position.y / TILE_SIZE))
                tile.current_obj = EnvironmentalManager.get_instance().spawn_at(gx, gy, tile.position.copy(), tile.textureName)
            elif tile.current_obj.is_dead or tile.current_obj.Hp <= 0:
                # Nếu vật thể đã chết (được xử lý bởi EnvironmentalManager), dọn dẹp biến current_obj
                tile.current_obj = None
            
            # Print tile coordinates for debugging
            # text = self.font.render(f"({int(tile.position.x/64)}, {int(tile.position.y/64)})", True, (255, 255, 255))
            # draw_pos = tile.position - camera
            # text_rect = text.get_rect(center=(draw_pos.x, draw_pos.y))
            # screen.blit(text, text_rect)
