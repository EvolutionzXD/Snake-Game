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
    """Xác định loại biôm (grass/stone) cho một ô lưới dựa trên thuật toán **Perlin Noise**.

    - Sử dụng `pnoise2` với scale rất nhỏ (0.01) để tạo ra các **Vùng biôm (Biome) khổng lồ** liền mạch.
    - `octaves=3`: chồng 3 lớp noise, lớp sau mịn hơn, tạo riề biôm có độ gồ ghề tự nhiên.
    - Trả về cặp (texture_name, frame_idx) để render tile đúng loại.
    - `frame_idx` xây dựng từ biểu thức `(grid_x + grid_y) % 2` — hàm hash đơn giản để
      tạo bàn cờ (checkerboard) phân biệt 2 frame mời mà không cần random."""
    # Dùng Scale nhỏ lại rất lới để tạo thành các VÙNG BIOME (quần xã) khổng lồ
    # Càng nhỏ thì bãi đá/cỏ càng rộng và liền mạch.
    scale = 0.01
    
    # Octaves cao giúp rìa biome có độ gồ ghề ngẫu nhiên một chút
    noise_val = noise.pnoise2(grid_x * scale, 
                              grid_y * scale, 
                              octaves=3, 
                              persistence=0.5, 
                              lacunarity=2.0)
    
    # Giá trị noise thường nằm trong khoảng -1.0 -> 1.0
    if noise_val > 0.1:  # Giảm ngưỡng để Biome Đá xuất hiện nhiều hơn
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
        """Quyết định có sinh vật thể tỉnh (rock/tree) tại ô (gx, gy) hay không bằng **Perlin Noise**.

        - Dùng offset seed lớn (+5000) để cảnh quan vật cản **độc lập hoàn toàn** với biôm nền.
        - Ngưỡng noise khác nhau cho từng loại đảm bảo:
          * grass (val > 0.2): xuất hiện nhiều bush hơn.
          * stone (val > 0.4): đá mọc ít hơn, rải rác hơn.
        - Trả về None nếu ô đó trống."""
        # Dùng chung 1 noise để quyết định có mọc vật thể hay không
        scale = 0.12
        val = noise.pnoise2(gx * scale + 5000, gy * scale + 5000, octaves=2)
        
        # Ngưỡng vật thể (Hạ thấp ngưỡng của grass để ra nhiều bụi cỏ hơn)
        if terrain_type == "grass" and val > 0.2: # Nhiều bush hơn
            return "tree" # "tree" thực chất là bush trong config
        elif terrain_type == "stone" and val > 0.4: # Tăng ngưỡng lên 0.6 để đá mọc rất ít
            return "rock"
            
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
        """Sinh vật thể tỉnh tại ô (gx, gy) nếu đầu đủ điều kiện.

        Phương pháp hash tích hợp để tạo đa dạng xác định bằng biểu thức:
        - **Kích thước đá**: `(gx * 41 + gy * 89) % 40` — hàm hash tuyến tính 2 biến
          đảm bảo mỗi ô có kích thước riêng không trùng lặp.
        - **Frame đá**: `(gx * 97 + gy * 43) % 100` cộng với Easter Egg 2% tại frame 3.
        - **Frame bụi**: `(gx * 31 + gy * 17) % 3` để chọn frame 0/1/2 cố định mỗi ô."""
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
            
            # Kích thước đá đa dạng
            hash_scale = ((gx * 41 + gy * 89) % 40) / 100.0 # Sinh ra từ 0.0 đến 0.39
            obj.scaleMultiplier = 1.0 + hash_scale # Kích thước từ 1.0 đến 1.39
            
            # Khởi tạo offset để gốc hòn đá bám sát đất
            obj.textureOffsetY = -(32 * obj.scaleMultiplier / 2.0) + 2.8

            # Chọn Frame cho Đá (Easter Egg siêu hiếm ở Frame 3)
            rock_hash = (gx * 97 + gy * 43) % 100
            if rock_hash < 2: # Tỉ lệ 2% ra Đá Siêu Hiếm
                rock_frame = 3
                obj.MaxHp = 100000.0
                obj.Hp = 100000.0
            else:
                rock_frame = rock_hash % 3 # Tỉ lệ 98% chia đều cho 3 frame đầu
            
            obj.MinFrame = rock_frame
            obj.MaxFrame = rock_frame
        else:
            obj.apply_config(GetTreeConfig())
            # Hash tọa độ để chọn frame cố định (0, 1, hoặc 2) cho từng bụi cây
            bush_frame = (gx * 31 + gy * 17) % 3
            obj.MinFrame = bush_frame
            obj.MaxFrame = bush_frame
            
            # Kích thước (Scale) đa dạng dựa trên hash để tránh trùng lặp
            hash_scale = ((gx * 73 + gy * 37) % 30) / 100.0 # Sinh ra từ 0.0 đến 0.29
            obj.scaleMultiplier = 0.65 + hash_scale # Kích thước từ 0.65 đến 0.94
            
            # Khởi tạo offset (sẽ được cập nhật liên tục trong process)
            obj.textureOffsetY = -(32 * obj.scaleMultiplier / 2.0) + 2.8
        
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
                    # Đá thì văng bụi xám, Bụi cây thì văng lá xanh
                    is_bush = obj.textureName != "rock"
                    color = (120, 120, 120) if not is_bush else (34, 139, 34)
                    pm.spawn(
                        pos=obj.position, count=15, color=color, alpha=200,
                        size_range=(4, 12), speed_range=(100, 300),
                        lifetime=0.6, gravity=400.0,
                    )
                    
                    # RƠI ĐỒ: Bụi cây rơi EXP/Coin, Đá rơi Pepper (Rock-coin)
                    if is_bush:
                        from stage import StageManager
                        StageManager.get_instance().spawn_exp(obj.position, value=5)
                        if random.random() < 0.25:
                            StageManager.get_instance().spawn_coin(obj.position, value=1)
                        # ĐỒNG THỜI rơi Táo vật lý (xác suất 25%)
                        if random.random() < 0.25:
                            loot = Node(obj.position.copy())
                            loot.textureName = "apple"
                            loot.scaleMultiplier = 0.5
                            loot.MaxHp = 1.0; loot.Hp = 1.0; loot.mask = 2
                            loot.lifetime = 15.0
                            loot.velocity = pygame.math.Vector2(random.uniform(-150, 150), random.uniform(-150, 150))
                            from entity import active_nodes
                            active_nodes.append(loot)
                    else:
                        # RƠI PEPPER (ROCK-COIN) TỪ ĐÁ
                        from stage import StageManager
                        is_rare_rock = obj.MinFrame == 3
                        if is_rare_rock:
                            # Đá 100k HP rơi siêu nhiều Pepper (từ 50-100 viên)
                            count = random.randint(50, 100)
                            for _ in range(count):
                                StageManager.get_instance().spawn_pepper(obj.position, value=1)
                        elif random.random() < 0.5: # Đá thường 50% xác suất rơi
                            count = random.randint(3, 10)
                            for _ in range(count):
                                StageManager.get_instance().spawn_pepper(obj.position, value=1)
                
                self.on_object_broken(obj)
                continue
            
            # LERP QUAY VỀ VỊ TRÍ CŨ (nếu bị đẩy lệch)
            dist_sq = obj.position.distance_squared_to(obj.origin_pos)
            if dist_sq > 0.1:
                obj.position = obj.position.lerp(obj.origin_pos, min(8.0 * dt, 1.0))

            # --- HIỆU ỨNG SIN CHO BỤI CÂY (Nhún nhảy bằng Offset) ---
            if obj.textureName == "bush":
                # Pha dao động khác nhau xa nhau dựa trên cả X và Y
                phase_offset = (obj.origin_pos.x * 0.07) + (obj.origin_pos.y * 0.11)
                t = pygame.time.get_ticks() / 1000.0 + phase_offset
                
                # Tính toán lại tâm gốc của hình ảnh (Base Y) dựa trên kích thước hiện tại
                base_y = -(32 * obj.scaleMultiplier / 2.0) + 2.8
                # Đung đưa quanh vị trí gốc
                obj.textureOffsetY = base_y + math.sin(t * 1.5) * 1.5

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
        """Cập nhật texture, frame và các phần tử trang trí của tile dựa trên vị trí lưới mới.

        - **Auto-tiling**: Kiểm tra 4 ô lân cận, nếu tiếp giáp stone thì vẽ viền chuyển tiếp `stone_border`.
        - **Cỏ trang trí (Decoration)**: Dùng **XOR Hash** `(grid_x * 73856093) ^ (grid_y * 19349663)`
          — một kỹ thuật phần tán bằng số nguyên tố lớn đảm bảo phân phối đồng đều để
          quyết định số lượng và vị trí ngẫu nhiên của các bụi cỏ nhỏ mà không dùng random()."""
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

        # --- SINH CỎ TRANG TRÍ (DECORATION) ---
        seed = (grid_x * 73856093) ^ (grid_y * 19349663)
        self.grass_data = []
        if tex == "grass" and (seed % 10) < 4: # Chỉ 40% ô cỏ có mọc cỏ trang trí
            count = (seed // 7) % 3 + 1 # 1 đến 3 bụi
            for i in range(count):
                # Tạo seed con cho từng bụi cỏ
                sub_seed = (seed ^ (i * 1234567))
                rx = (sub_seed % 50) - 25 # Offset rộng hơn chút
                ry = ((sub_seed // 100) % 50) - 25
                f_idx = (sub_seed // 1000) % 5 # Đã có 5 frame
                self.grass_data.append((rx, ry, f_idx))

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
        """Thực hiện kỹ thuật **Infinite Scrolling bằng Tile Wrapping**:

        - So sánh vị trí tile với tâm camera. Nếu tile ra khỏi phạm vi `[-half_width, half_width]`
          theo X hoặc Y, nó sẽ được **dịch chuyển sang phía đối diện** (cong nối 2 đầu).
        - Sau khi dịch, gọi `update_terrain()` để sinh lại texture và vật thể tỉnh đúng với
          toạ độ mới (dùng Perlin Noise + Hash nên kết quả luôn nhất quán).
        - Dùng `TOTAL_WIDTH = TILE_SIZE * GRID_COLS` làm chu kỳ cuộn để bản đồ trải dài vô tận."""
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

        # --- VẼ CỎ TRANG TRÍ ---
        if hasattr(self, 'grass_data') and self.grass_data:
            for rx, ry, f_idx in self.grass_data:
                _, grass_surf = get_surfaces("small_grass", f_idx, 4.0, self.scaleMultiplier, 0.0, 0.0, False)
                if grass_surf:
                    # Tính toán vị trí vẽ cỏ (có offset so với tâm tile)
                    g_pos = draw_pos + pygame.math.Vector2(rx, ry) * GLOBAL_SCALE
                    rect = grass_surf.get_rect(center=(g_pos.x, g_pos.y))
                    screen.blit(grass_surf, rect)
        
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
            from resources import ResourceManager
            self.font = ResourceManager.get_instance().get_font("VCRosdNEUE", 16)
            
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
