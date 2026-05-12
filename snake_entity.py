import pygame
import math
import random
from entity import Node
from config import GetSnakeHeadConfig, GetSnakeBodyConfig
from particle import ParticleManager
from apple import AppleManager
from grid import GridManager

class Snake:
    def __init__(self, startPos, config):
        self.config = config
        self.MaxVelocity = getattr(config, 'velocity', 350.0)
        self.BodyLength = getattr(config, 'length', 15.0)
        self.nodes = [Node(startPos) for _ in range(getattr(config, 'size', 10))]
        
        # 15% xác suất rắn "não to" (đón đầu gắt), còn lại "não nhỏ" (ngắm thẳng)
        self.is_big_brain = getattr(config, 'is_big_brain', random.random() < 0.15)
        self.intercept_factor = random.uniform(0.5, 1.2) if self.is_big_brain else random.uniform(-0.1, 0.2)
        self.intercept_timer = random.uniform(1.0, 3.0)
        
        # Scaling logic constant
        self.scale_logic = getattr(config, 'scale_logic', 4.0)
        
        if self.nodes:
            head_cfg = getattr(config, 'headConfig', None)
            if head_cfg: self.nodes[0].apply_config(head_cfg)
            self.nodes[0].scaleMultiplier = getattr(config, 'headSize', 0.5)
            
        for i in range(1, len(self.nodes)):
            shrinkRatio = getattr(config, 'headSize', 0.5) - 0.1 - (i / len(self.nodes)) * 0.1
            self.nodes[i].position = pygame.math.Vector2(startPos) 
            body_cfg = getattr(config, 'bodyConfig', None)
            if body_cfg: self.nodes[i].apply_config(body_cfg)
            self.nodes[i].scaleMultiplier = shrinkRatio

        if self.nodes:
            head_node = self.nodes[0]
            for i, node in enumerate(self.nodes):
                node.snake_head = head_node
                node.snake_depth = i
        
        self.shoot_timer = random.uniform(1.0, 3.0)
        self.aim_timer = 0.0
        self.aim_target_pos = None
        self.behavior = getattr(config, 'behavior', 'melee')

    def GetPosition(self):
        return self.nodes[0].position if self.nodes else pygame.math.Vector2(0,0)

    def GetHead(self):
        return self.nodes[0] if self.nodes else None

    def attract(self, target_node, Smoothing, camera=None):
        if not self.nodes: return
        
        # Grid-based logic
        if camera and Smoothing >= 0:
            grid_target = GridManager.get_instance().get_best_direction(
                self.nodes[0].position, 
                camera, 
                getattr(self.config, 'has_bullet_awareness', False)
            )
            
            if grid_target:
                # Nếu có grid target, ưu tiên di chuyển theo grid
                offset = grid_target - self.nodes[0].position
                if offset.length_squared() > 0:
                    TargetSpeed = offset.normalize() * self.MaxVelocity
                    self.nodes[0].direction = self.nodes[0].direction.lerp(TargetSpeed, abs(Smoothing))
                return

        # Fallback to direct attraction (for repulsion or if out of grid)
        if not target_node: return
        
        if Smoothing >= 0:
            target_vel = target_node.direction + target_node.velocity
            predicted_pos = target_node.position + target_vel * self.intercept_factor
            
            # Logic giữ khoảng cách cho Ranged Snake (Cải tiến: Thêm di chuyển ngang)
            if self.behavior == "ranged":
                dist = self.nodes[0].position.distance_to(target_node.position)
                if dist < 550:
                    # Bỏ chạy ngang (Diagonal fleeing) để né đạn tốt hơn
                    Smoothing = 0.12 
                    away_dir = (self.nodes[0].position - target_node.position).normalize()
                    side_dir = pygame.math.Vector2(-away_dir.y, away_dir.x) # Hướng ngang
                    
                    # Kết hợp chạy ra xa + chạy ngang
                    flee_dir = (away_dir * 0.6 + side_dir * 0.4).normalize()
                    TargetSpeed = flee_dir * self.MaxVelocity
                    self.nodes[0].direction = self.nodes[0].direction.lerp(TargetSpeed, abs(Smoothing))
                    return
                elif dist < 850:
                    # Kiting: Di chuyển ngang (Sidewinding) để tránh bị kẹt
                    Smoothing = 0.05 
                    to_target = target_node.position - self.nodes[0].position
                    if to_target.length_squared() > 0:
                        side_dir = pygame.math.Vector2(-to_target.y, to_target.x).normalize()
                        # Thêm một chút hướng về mục tiêu để không bị trôi quá xa
                        TargetSpeed = (side_dir * 0.8 + to_target.normalize() * 0.2) * self.MaxVelocity
                        self.nodes[0].direction = self.nodes[0].direction.lerp(TargetSpeed, abs(Smoothing))
                        return
            
            # Logic cho Sniper Snake: Giữ khoảng cách tầm trung và đứng yên khi ngắm
            elif self.behavior == "sniper":
                if self.aim_timer > 0:
                    # Đang ngắm: Đứng yên
                    self.nodes[0].velocity *= 0.9 # Giảm tốc dần về 0
                    self.nodes[0].direction *= 0.9
                    return
                
                dist = self.nodes[0].position.distance_to(target_node.position)
                if dist < 500:
                    Smoothing = -0.1 # Lùi lại nếu quá gần
                elif dist > 800:
                    Smoothing = 0.05 # Tiến lại gần nếu quá xa
                else:
                    Smoothing = 0 # Đứng im ở tầm lý tưởng
        else:
            predicted_pos = target_node.position
            
        offset = predicted_pos - self.nodes[0].position
        if offset.length_squared() > 0:
            TargetSpeed = offset.normalize() * (self.MaxVelocity if Smoothing >= 0 else -self.MaxVelocity)
            self.nodes[0].direction = self.nodes[0].direction.lerp(TargetSpeed, abs(Smoothing))

    def process(self, dt):
        if not self.nodes: return
        
        # Allow for a custom behavior override if defined in config
        update_func = getattr(self.config, 'custom_update', None)
        if update_func:
            update_func(self, dt)
            return

        self._update_intercept_factor(dt)
        self._handle_outscreen_teleport()
        if not self.nodes: return
        
        self._handle_death_propagation(dt)
        self._update_movement(dt)
        self._update_body_trailing(dt)
        self._update_broken_frames(dt)
        self._emit_particles(dt)
        self._handle_ranged_attack(dt)

    def _handle_ranged_attack(self, dt):
        if self.behavior not in ["ranged", "sniper"]: return
        if not self.nodes or self.nodes[0].Hp <= 0: return
        
        player_pos = AppleManager.GetPosition()
        dist = self.nodes[0].position.distance_to(player_pos)
        
        # Sniper Logic: Ngắm bắn trước khi khai hỏa
        if self.behavior == "sniper":
            if self.shoot_timer <= 1.5 and self.aim_timer <= 0:
                # Bắt đầu ngắm
                self.aim_timer = 1.5
            
            if self.aim_timer > 0:
                self.aim_timer -= dt
                
                # Cảnh báo nhấp nháy trên đầu rắn
                if self.aim_timer < 0.4:
                    self.nodes[0].flashEffect = 0.1 # Nháy liên tục
                
                # Cập nhật vị trí dự đoán liên tục khi đang ngắm (để vẽ laze)
                player_node = AppleManager.apple_node
                if player_node:
                    # Dự đoán cực nhẹ (gần như nhắm thẳng) để nhìn tự nhiên hơn
                    player_vel = player_node.direction + player_node.velocity
                    self.aim_target_pos = player_pos + player_vel * (random.uniform(0, 1) / 100) 
                else:
                    self.aim_target_pos = player_pos

                # Khi hết thời gian ngắm -> Khai hỏa
                if self.aim_timer <= 0:
                    from projectile import ProjectileManager
                    from config import GetProjectileConfig
                    
                    def SniperBulletConfig():
                        cfg = GetProjectileConfig()
                        cfg.lifetime = 0.8
                        cfg.textureName = "sniper_projectile"
                        cfg.damage = getattr(self.config, 'ranged_damage', 50.0)
                        cfg.mask = 4 
                        cfg.maskOut = [2, 5]
                        cfg.scaleMultiplier = 0.2
                        cfg.hasShadow = True
                        cfg.hasOutline = False
                        cfg.has_trail_particles = True
                        cfg.trail_color = (255, 150, 0) # Màu cam rực rỡ cho Sniper
                        return cfg
                    
                    # Tính toán vận tốc chủ động (không phụ thuộc vào vận tốc của rắn)
                    direction = (self.aim_target_pos - self.nodes[0].position)
                    if direction.length_squared() > 0:
                        active_velocity = direction.normalize() * 4000.0
                    else:
                        active_velocity = pygame.math.Vector2(0, 0)

                    ProjectileManager.Spawn(
                        pos = self.nodes[0].position,
                        target_pos = self.aim_target_pos,
                        config_func = SniperBulletConfig,
                        lifetime_override = 1.0,
                        velocity_override = active_velocity,
                        is_enemy = True
                    )
                    self.shoot_timer = getattr(self.config, 'shoot_interval', 4.0) + random.uniform(-0.5, 0.5)
            else:
                self.shoot_timer -= dt
            return

        # Ranged (Venom) Logic: Bắn liên tục
        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            if dist < 800:
                from projectile import ProjectileManager
                from config import GetProjectileConfig
                
                # Bắn một viên đạn của quái (có thể tùy chỉnh config riêng sau)
                def EnemyBulletConfig():
                    cfg = GetProjectileConfig()
                    cfg.textureName = "venom_projectile"
                    cfg.damage = getattr(self.config, 'ranged_damage', 10.0)
                    cfg.mask = 4 # Coi như đạn kẻ thù (va chạm với Apple)
                    cfg.maskOut = [2, 5] # Va chạm với Apple (2) và Bush (5)
                    cfg.scaleMultiplier = 0.2
                    cfg.hasShadow = True
                    cfg.hasOutline = False
                    cfg.has_trail_particles = True
                    cfg.trail_color = (0, 255, 0)
                    return cfg
                
                ProjectileManager.Spawn(
                    pos = self.nodes[0].position,
                    target_pos = player_pos,
                    config_func = EnemyBulletConfig,
                    speed = 1200.0,
                    lifetime_override = 1.5,
                    inherited_velocity = self.nodes[0].velocity + self.nodes[0].direction,
                    is_enemy = True
                )
                self.shoot_timer = getattr(self.config, 'shoot_interval', 2.0) + random.uniform(-0.1, 0.1)

    def _update_intercept_factor(self, dt):
        self.intercept_timer -= dt
        if self.intercept_timer <= 0:
            # Rắn não to giữ thói quen đón đầu, rắn thường chỉ ngắm thẳng hoặc hơi bám đuôi
            self.intercept_factor = random.uniform(0.5, 1.2) if getattr(self, 'is_big_brain', False) else random.uniform(-0.1, 0.2)
            self.intercept_timer = random.uniform(2.0, 5.0)

    def _handle_outscreen_teleport(self):
        player_pos = AppleManager.GetPosition()
        head = self.nodes[0]
        dist_sq = head.position.distance_squared_to(player_pos)
        
        if dist_sq > 1200 * 1200:
            # Nếu đầu rắn đã chết mà còn ở xa thì dọn dẹp sạch sẽ các node
            if head.Hp <= 0:
                for node in self.nodes:
                    node.Hp = 0
                    node.is_dead = True # Đánh dấu chết để entity.py tự dọn dẹp
                self.nodes.clear()
                return
                
            player_node = AppleManager.apple_node
            if player_node and (player_node.direction.length_squared() > 10 or player_node.velocity.length_squared() > 10):
                player_vel = player_node.direction + player_node.velocity
                move_angle = math.atan2(player_vel.y, player_vel.x)
                angle = move_angle + random.uniform(-0.5, 0.5)
            else:
                angle = random.uniform(0, 2 * math.pi)
            
            teleport_dir = pygame.math.Vector2(math.cos(angle), math.sin(angle))
            teleport_pos = player_pos + teleport_dir * random.uniform(1000, 1300)
            
            for node in self.nodes:
                node.position = pygame.math.Vector2(teleport_pos)
                node.velocity *= 0

    def _handle_death_propagation(self, dt):
        num_nodes = len(self.nodes)
        death_damage = getattr(self.config, 'death_damage', 400.0)
        for i in range(num_nodes - 1):
            curr_node = self.nodes[i]
            next_node = self.nodes[i+1]
            if curr_node and curr_node.Hp <= 0:
                if next_node:
                    next_node.Hp -= death_damage * dt

    def _update_movement(self, dt):
        head = self.nodes[0]
        move_vec = head.direction + head.velocity
        if move_vec.length_squared() > 0.01:
            head.angle = math.degrees(math.atan2(move_vec.y, move_vec.x))

    def _update_body_trailing(self, dt):
        push_force = getattr(self.config, 'push_force', 50.0)
        lerp_factor = getattr(self.config, 'lerp_factor', 0.5)
        
        for i in range(1, len(self.nodes)):
            curr, prev = self.nodes[i], self.nodes[i-1]
            if prev.Hp <= 0 or curr.Hp <= 0:
                continue
                
            desired_dist = self.BodyLength * self.scale_logic * curr.scaleMultiplier
            offset = curr.position - prev.position
            dist = offset.length()
            
            if dist > desired_dist:
                target_pos = prev.position + (offset / dist) * desired_dist
                curr.position = curr.position.lerp(target_pos, lerp_factor)
                
                if dist > 0.1:
                    curr.angle = math.degrees(math.atan2(-offset.y, -offset.x))
            
            if dist < desired_dist * 0.8 and dist > 0:
                push_dir = offset / dist
                curr.velocity += push_dir * push_force * dt

    def _update_broken_frames(self, dt):
        broken_count = 0
        for i, node in enumerate(self.nodes):
            if getattr(node, 'textureName', '') == 'snake_stone':
                if 0 < node.Hp <= node.MaxHp * 0.5:
                    broken_count += 1
                    if i == 0:
                        node.MinFrame = 2
                        node.MaxFrame = 2
                    else:
                        node.MinFrame = 3
                        node.MaxFrame = 3
                        
                    # Twitching (Giật mạnh hơn khi sắp vỡ)
                    node.position.x += random.uniform(-2.5, 2.5)
                    node.position.y += random.uniform(-2.5, 2.5)
                    
                    # Nhả khói (Smoke particles) - Đã giảm để tối ưu hiệu năng
                    if random.random() < 0.3: # 5% cơ hội mỗi frame
                        pm = ParticleManager.get_instance()
                        pm.spawn(
                            pos         = node.position + pygame.math.Vector2(random.uniform(-15, 15), random.uniform(-15, 15)),
                            count       = random.randint(1, 2), # Sinh ra 1-2 hạt
                            color       = (100, 100, 100), 
                            alpha       = 180,
                            size_range  = (4, 10),
                            speed_range = (10, 30),
                            lifetime    = random.uniform(0.4, 0.8),
                            gravity     = -40.0 
                        )
        
        # Nếu là rắn đá, càng vỡ nhiều phần thì càng nhẹ và chạy càng nhanh
        if getattr(self.config.headConfig, 'textureName', '') == 'snake_stone':
            base_vel = getattr(self.config, 'velocity', 300.0)
            self.MaxVelocity = base_vel + (broken_count * 30.0)

    def _emit_particles(self, dt):
        head = self.nodes[0]
        speed_sq = head.direction.length_squared()
        if speed_sq > 5000:
            pm = ParticleManager.get_instance()
            
            head_particle_chance = getattr(self.config, 'head_particle_chance', 0.4)
            if random.random() < head_particle_chance:
                pm.spawn(
                    pos         = head.position,
                    count       = 1,
                    color       = getattr(self.config, 'head_particle_color', (40, 160, 60)),
                    alpha       = getattr(self.config, 'particle_alpha', 120),
                    size_range  = getattr(self.config, 'particle_size_range', (2, 5)),
                    speed_range = (10, 50),
                    lifetime    = 0.3,
                    gravity     = 80.0,
                )
                
            if len(self.nodes) > 2:
                body_particle_chance = getattr(self.config, 'body_particle_chance', 0.2)
                if random.random() < body_particle_chance:
                    rand_node = self.nodes[random.randint(1, len(self.nodes) - 1)]
                    pm.spawn(
                        pos         = rand_node.position,
                        count       = 1,
                        color       = getattr(self.config, 'body_particle_color', (30, 130, 50)),
                        alpha       = getattr(self.config, 'particle_alpha', 120) - 40,
                        size_range  = (2, 4),
                        speed_range = (5, 30),
                        lifetime    = 0.2,
                        gravity     = 60.0,
                    )

    def draw_shadow(self, screen, camera):
        if not self.nodes: return
        for i in range(len(self.nodes) - 1, -1, -1):
            self.nodes[i].draw_shadow(screen, camera)

    def draw_outline(self, screen, camera):
        if not self.nodes: return
        for i in range(len(self.nodes) - 1, -1, -1):
            self.nodes[i].draw_outline(screen, camera)

    def draw_sprite(self, screen, camera):
        if not self.nodes: return
        for i in range(len(self.nodes) - 1, -1, -1):
            self.nodes[i].draw_sprite(screen, camera)
