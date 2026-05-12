import pygame
from collections import deque
import math
import config

class GridManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GridManager()
        return cls._instance

    def __init__(self):
        self.rows = config.GRID_ROWS
        self.cols = config.GRID_COLS
        self.screen_w = 1200
        self.screen_h = 800
        self.cell_w = self.screen_w // self.cols
        self.cell_h = self.screen_h // self.rows
        
        # Maps
        self.apple_dist = [[float('inf')] * self.cols for _ in range(self.rows)]
        self.danger_map = [[0.0] * self.cols for _ in range(self.rows)]
        self.obstacle_map = [[False] * self.cols for _ in range(self.rows)]

    def world_to_grid(self, world_pos, camera):
        """Chuyển tọa độ world sang tọa độ ô lưới (relative to camera)."""
        screen_x = world_pos.x - camera.x
        screen_y = world_pos.y - camera.y
        
        gx = int(screen_x // self.cell_w)
        gy = int(screen_y // self.cell_h)
        
        return gx, gy

    def grid_to_world(self, gx, gy, camera):
        """Chuyển tọa độ ô lưới sang tâm của ô trong world space."""
        screen_x = gx * self.cell_w + self.cell_w / 2
        screen_y = gy * self.cell_h + self.cell_h / 2
        
        return pygame.math.Vector2(screen_x + camera.x, screen_y + camera.y)

    def is_valid(self, gx, gy):
        return 0 <= gx < self.cols and 0 <= gy < self.rows

    def update(self, camera, apples, projectiles, obstacles, difficulty=1.0):
        # Reset maps
        self.apple_dist = [[float('inf')] * self.cols for _ in range(self.rows)]
        self.danger_map = [[0.0] * self.cols for _ in range(self.rows)]
        self.obstacle_map = [[False] * self.cols for _ in range(self.rows)]

        # 1. Map Obstacles
        for obj in obstacles:
            gx, gy = self.world_to_grid(obj.position, camera)
            if self.is_valid(gx, gy):
                self.obstacle_map[gy][gx] = True

        # 2. Map Projectiles (Danger) - Càng khó càng "khôn"
        # Hệ số sợ hãi: Bắt đầu từ 0.1 ở difficulty 1.0 và tăng mạnh
        fear_multiplier = max(0.1, (difficulty - 1.0) * 6.0)
        
        # Tầm nhìn quỹ đạo: Càng khó càng nhìn xa (từ 1 đến 6 ô)
        prediction_range = int(min(6, 1 + (difficulty - 1.0) * 4.0))
        
        for p in projectiles:
            p_pos = p.position
            p_vel = getattr(p, 'velocity', pygame.math.Vector2(0,0))
            
            if p_vel.length_squared() > 0:
                step_size = self.cell_w
                direction = p_vel.normalize()
                
                for i in range(prediction_range): 
                    predict_pos = p_pos + direction * (i * step_size)
                    gx, gy = self.world_to_grid(predict_pos, camera)
                    
                    if self.is_valid(gx, gy):
                        # Độ nguy hiểm (Chỉ thực sự cao khi fear_multiplier lớn)
                        danger_value = (800.0 / (i + 1)) * fear_multiplier
                        self.danger_map[gy][gx] += danger_value

        # 3. Multi-source BFS for Apple Distances
        queue = deque()
        for apple in apples:
            # Lấy các ô mà diện tích Táo đang chiếm giữ (dựa trên hitbox_radius)
            pos = apple.position
            r = getattr(apple, 'hitbox_radius', 30.0)
            
            # Kiểm tra 5 điểm: Tâm và 4 hướng xung quanh để bao phủ trọn vẹn Táo
            check_points = [
                pos,
                pos + pygame.math.Vector2(r, 0),
                pos + pygame.math.Vector2(-r, 0),
                pos + pygame.math.Vector2(0, r),
                pos + pygame.math.Vector2(0, -r)
            ]
            
            for p in check_points:
                gx, gy = self.world_to_grid(p, camera)
                if self.is_valid(gx, gy) and self.apple_dist[gy][gx] == float('inf'):
                    self.apple_dist[gy][gx] = 0
                    queue.append((gx, gy))

        while queue:
            cx, cy = queue.popleft()
            curr_dist = self.apple_dist[cy][cx]

            # 8-way movement (chung đỉnh)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    nx, ny = cx + dx, cy + dy
                    
                    if self.is_valid(nx, ny) and not self.obstacle_map[ny][nx]:
                        new_dist = curr_dist + (1.414 if dx != 0 and dy != 0 else 1.0)
                        if new_dist < self.apple_dist[ny][nx]:
                            self.apple_dist[ny][nx] = new_dist
                            queue.append((nx, ny))

    def get_best_direction(self, current_world_pos, camera, has_awareness):
        gx, gy = self.world_to_grid(current_world_pos, camera)
        
        if not self.is_valid(gx, gy):
            return None # Ngoài grid, dùng logic cũ (move thẳng tới táo)

        best_score = float('inf')
        best_target_gx, best_target_gy = gx, gy
        found = False

        # Check 8 neighbors + current cell
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = gx + dx, gy + dy
                
                if self.is_valid(nx, ny) and not self.obstacle_map[ny][nx]:
                    # Heuristic: distance to apple
                    score = self.apple_dist[ny][nx]
                    
                    # Cost: danger (if snake is aware)
                    if has_awareness:
                        score += self.danger_map[ny][nx]
                    
                    if score < best_score:
                        best_score = score
                        best_target_gx, best_target_gy = nx, ny
                        found = True

        # Trả về target nếu tìm được đường đi (score không phải vô hạn)
        if found and best_score < 1000000:
            # Nếu điểm tốt nhất là 0 (đã chạm vào Táo), trả về None 
            # để Snake quay lại logic "đuổi trực diện" thay vì đi vào tâm ô lưới
            if best_score == 0:
                return None
            return self.grid_to_world(best_target_gx, best_target_gy, camera)
        return None

    def draw_debug(self, screen, camera):
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        # Sử dụng font hệ thống đơn giản cho debug
        try:
            font = pygame.font.SysFont("Consolas", 14)
        except:
            font = pygame.font.SysFont("Arial", 14)

        for gy in range(self.rows):
            for gx in range(self.cols):
                rect = pygame.Rect(gx * self.cell_w, gy * self.cell_h, self.cell_w, self.cell_h)
                
                # Vẽ lưới - màu trắng mờ
                pygame.draw.rect(overlay, (255, 255, 255, 40), rect, 1)
                
                # 1. Visualize apple distance (Xanh lá)
                dist = self.apple_dist[gy][gx]
                if dist != float('inf'):
                    # Đậm dần khi gần táo
                    alpha = max(30, 200 - int(dist * 10))
                    pygame.draw.rect(overlay, (0, 255, 50, alpha), rect)
                    
                    # Text khoảng cách ở góc trên trái
                    dist_txt = font.render(f"{dist:.1f}", True, (255, 255, 255))
                    overlay.blit(dist_txt, (rect.x + 5, rect.y + 5))
                
                # 2. Visualize danger (Đỏ rực)
                danger = self.danger_map[gy][gx]
                if danger > 0:
                    alpha = min(230, int(danger * 0.8) + 50)
                    # Vẽ viền đỏ đậm hơn bên trong
                    pygame.draw.rect(overlay, (255, 0, 0, alpha), rect)
                    
                    # Text danger ở góc dưới trái
                    danger_txt = font.render(f"D:{int(danger)}", True, (255, 255, 0))
                    overlay.blit(danger_txt, (rect.x + 5, rect.y + rect.height - 20))

                # 3. Visualize obstacles (Xám đen)
                if self.obstacle_map[gy][gx]:
                    pygame.draw.rect(overlay, (0, 0, 0, 160), rect)
                    obs_txt = font.render("OBS", True, (200, 200, 200))
                    overlay.blit(obs_txt, (rect.centerx - 15, rect.centery - 7))

        screen.blit(overlay, (0, 0))
