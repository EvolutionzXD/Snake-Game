import pygame
import math
import os
import random

pygame.init()

# ----------------- CONFIGS -----------------
class NodeConfig:
    def __init__(self, textureName="", mask=0, maskOut=0, hitbox_radius=30.0, 
                 MaxHp=100.0, knockback=10.0, damage=10.0, MinFrame=0, MaxFrame=0, 
                 textureWidth=32.0, textureHeight=32.0, scaleMultiplier=1.0, hasOutline=False):
        self.textureName = textureName
        self.mask = mask
        self.maskOut = maskOut
        self.hitbox_radius = hitbox_radius
        self.MaxHp = MaxHp
        self.knockback = knockback
        self.damage = damage
        self.MinFrame = MinFrame
        self.MaxFrame = MaxFrame
        self.textureWidth = textureWidth
        self.textureHeight = textureHeight
        self.scaleMultiplier = scaleMultiplier
        self.hasOutline = hasOutline

def GetSnakeHeadConfig(): return NodeConfig("snake", 1, 2, 30.0, 100.0, 700.0, 5.0, 0, 0, 32.0, 32.0, 0.5, True)
def GetSnakeBodyConfig(): return NodeConfig("snake", 1, 3, 30.0, 100.0, 10.0, 5.0, 1, 1, 32.0, 32.0, 0.5, True)
def GetAppleConfig(): return NodeConfig("apple", 2, 3, 20.0, 1000.0, 0.0, 0.0, 0, 1, 32.0, 32.0, 0.5, False)

# ----------------- RESOURCE MANAGER & CACHE -----------------
class ResourceManager:
    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None: cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.textures = {}

    def load_all_sprites(self, directory):
        if not os.path.exists(directory): return
        for file in os.listdir(directory):
            if file.endswith((".png", ".jpg", ".bmp")):
                name = os.path.splitext(file)[0]
                path = os.path.join(directory, file)
                try:
                    self.textures[name] = pygame.image.load(path).convert_alpha()
                except: continue

    def get_texture(self, name):
        return self.textures.get(name, None)

# --- DICTIONARY CACHE TỐI ƯU ---
_RENDER_CACHE = {}

def get_surfaces(texture_name, frame, base_scale, scale_mult, angle, flash_effect, hasOutline):
    tex = ResourceManager.get_instance().get_texture(texture_name)
    if not tex: return None, None

    # LÀM TRÒN ĐỂ ÉP VÀO CACHE (Giảm số lượng tổ hợp xuống hàng ngàn lần)
    q_angle = int((angle % 360) / 4) * 4   # Xoay mỗi bước 4 độ
    q_scale = round(scale_mult, 1)         # Thu gọn mức độ scale (0.2, 0.3, 0.4...)
    q_flash = 1 if flash_effect > 0 else 0 # Chỉ có 2 trạng thái chớp sáng
    
    key = (texture_name, frame, base_scale, q_scale, q_angle, q_flash, hasOutline)
    if key in _RENDER_CACHE:
        return _RENDER_CACHE[key]

    # --- TẠO MỚI NẾU CHƯA CÓ TRONG CACHE ---
    tex_w, tex_h = 32, 32  
    rect = pygame.Rect(int(tex_w * frame), 0, tex_w, tex_h)
    try: raw_surf = tex.subsurface(rect)
    except ValueError: raw_surf = tex

    final_scale = base_scale * q_scale
    if final_scale != 1.0:
        main_surf = pygame.transform.scale(raw_surf, (int(tex_w * final_scale), int(tex_h * final_scale)))
    else:
        main_surf = raw_surf.copy()

    # Xử lý Sprite
    sprite_surf = main_surf.copy()
    if q_flash > 0:
        glow = sprite_surf.copy()
        glow.fill((255, 255, 255, int(255 * 0.8)), special_flags=pygame.BLEND_RGBA_MULT)
        sprite_surf.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    # Xử lý Outline
    outline_surf = None
    if hasOutline:
        mask = pygame.mask.from_surface(main_surf)
        outline_base = mask.to_surface(setcolor=(0,0,0,255), unsetcolor=(0,0,0,0))
        t = 4
        new_w, new_h = main_surf.get_width() + t*2, main_surf.get_height() + t*2
        outline_surf = pygame.Surface((new_w, new_h), pygame.SRCALPHA)
        offsets = [(-t,0), (t,0), (0,-t), (0,t), (-t,-t), (-t,t), (t,-t), (t,t)]
        for dx, dy in offsets:
            outline_surf.blit(outline_base, (dx + t, dy + t))

    # Xoay chung 1 lần cho cả 2
    if q_angle != 0:
        sprite_surf = pygame.transform.rotate(sprite_surf, -q_angle)
        if outline_surf:
            outline_surf = pygame.transform.rotate(outline_surf, -q_angle)

    _RENDER_CACHE[key] = (outline_surf, sprite_surf)
    return outline_surf, sprite_surf


# ----------------- GLOBALS & ENTITY -----------------
STUN_TIME = 0.3
INVINCIBILITY_TIME = 0.1
CELL_SIZE = 60.0  

active_nodes = []
grid_mat = {}

class Node:
    __slots__ = ['position', 'velocity', 'direction', 'angle', 'textureName', 
                 'hitbox_radius', 'MaxHp', 'Hp', 'knockback', 'stun', 'invincibility', 
                 'damage', 'mask', 'maskOut', 'textureOffsetX', 'textureOffsetY', 
                 'MinFrame', 'MaxFrame', 'frame', 'textureWidth', 'textureHeight', 
                 'scaleMultiplier', 'hasOutline', 'flashEffect', 'is_dead', 'is_dummy']

    def __init__(self, pos):
        self.position = pygame.math.Vector2(pos)
        self.velocity = pygame.math.Vector2(0, 0)
        self.direction = pygame.math.Vector2(0, 0)
        self.angle = 0.0
        self.textureName = ""
        self.hitbox_radius = 30.0
        self.MaxHp = 100.0
        self.Hp = 100.0
        self.knockback = 10.0
        self.stun = 0.0
        self.invincibility = 0.0
        self.damage = 10.0
        self.mask = 0
        self.maskOut = 0
        self.textureOffsetX = 0.0
        self.textureOffsetY = 0.0
        self.MinFrame = 0
        self.MaxFrame = 0
        self.frame = 0.0
        self.textureWidth = 32.0
        self.textureHeight = 32.0
        self.scaleMultiplier = 1.0
        self.hasOutline = False
        self.flashEffect = 0.0
        self.is_dead = False
        self.is_dummy = False 
        active_nodes.append(self)

    def apply_config(self, config):
        self.textureName = config.textureName
        self.hitbox_radius = config.hitbox_radius
        self.MaxHp = config.MaxHp
        self.Hp = config.MaxHp
        self.knockback = config.knockback
        self.damage = config.damage
        self.mask = config.mask
        self.maskOut = config.maskOut
        self.MinFrame = config.MinFrame
        self.MaxFrame = config.MaxFrame
        self.textureWidth = config.textureWidth
        self.textureHeight = config.textureHeight
        self.scaleMultiplier = config.scaleMultiplier
        self.hasOutline = config.hasOutline

    def get_position_id(self):
        return (int(self.position.x // CELL_SIZE), int(self.position.y // CELL_SIZE))

    def get_surfaces(self):
        if not self.textureName or self.is_dead or self.is_dummy: return None, None
        curr_frame = int(self.frame) + self.MinFrame
        return get_surfaces(self.textureName, curr_frame, 4.0, self.scaleMultiplier, self.angle, self.flashEffect, self.hasOutline)

    def draw_outline(self, screen, camera):
        outline_surf, _ = self.get_surfaces()
        if not outline_surf: return
        draw_pos = self.position - camera + pygame.math.Vector2(self.textureOffsetX, self.textureOffsetY)
        rect = outline_surf.get_rect(center=(draw_pos.x, draw_pos.y))
        screen.blit(outline_surf, rect)

    def draw_sprite(self, screen, camera):
        _, sprite_surf = self.get_surfaces()
        if not sprite_surf: return
        draw_pos = self.position - camera + pygame.math.Vector2(self.textureOffsetX, self.textureOffsetY)
        rect = sprite_surf.get_rect(center=(draw_pos.x, draw_pos.y))
        screen.blit(sprite_surf, rect)

def process_physics_and_collisions(dt):
    global active_nodes
    
    if any(n.Hp <= 0 for n in active_nodes):
        active_nodes = [n for n in active_nodes if n.Hp > 0]

    grid_mat.clear()

    for node in active_nodes:
        if node.stun <= 0:
            frameVelocity = node.velocity + node.direction
        else:
            frameVelocity = node.velocity.copy()
            node.stun -= dt

        node.position += frameVelocity * dt
        node.velocity *= 0.9  
        
        if node.invincibility > 0: node.invincibility -= dt
        if node.flashEffect > 0: node.flashEffect -= dt
        
        node.frame += dt * 5
        if node.frame >= (node.MaxFrame - node.MinFrame + 1):
            node.frame = 0.0
            
        cell = node.get_position_id()
        if node.mask not in grid_mat: grid_mat[node.mask] = {}
        if cell not in grid_mat[node.mask]: grid_mat[node.mask][cell] = []
        grid_mat[node.mask][cell].append(node)

    offsets = [(-1,-1), (0,-1), (1,-1), (-1,0), (0,0), (1,0), (-1,1), (0,1), (1,1)]
    for node in active_nodes:
        maskOut = node.maskOut
        if maskOut not in grid_mat: continue
        
        px, py = node.get_position_id()
        for dx, dy in offsets:
            cell = (px + dx, py + dy)
            if cell in grid_mat[maskOut]:
                for other in grid_mat[maskOut][cell]:
                    if node is not other and other.invincibility <= 0:
                        r_sum = (node.hitbox_radius * node.scaleMultiplier) + (other.hitbox_radius * other.scaleMultiplier)
                        dist_sq = node.position.distance_squared_to(other.position)
                        
                        if dist_sq < r_sum * r_sum:
                            other.Hp -= node.damage
                            
                            if dist_sq > 0:
                                push_dir = (other.position - node.position).normalize()
                            else:
                                push_dir = pygame.math.Vector2(random.uniform(-1,1), random.uniform(-1,1)).normalize()
                            
                            other.velocity += push_dir * node.knockback
                            other.stun = STUN_TIME
                            other.invincibility = INVINCIBILITY_TIME
                            other.flashEffect = 0.5


# ----------------- ENTITIES -----------------
base_scale_logic = 4.0 

class Snake:
    def __init__(self, startPos, size, velocity, length, headSize=0.4):
        self.MaxVelocity = velocity
        self.BodyLength = length
        self.nodes = [Node(startPos) for _ in range(size)]
        
        if self.nodes:
            self.nodes[0].apply_config(GetSnakeHeadConfig())
            self.nodes[0].scaleMultiplier = headSize 
            
        for i in range(1, len(self.nodes)):
            shrinkRatio = headSize - 0.1 - (i / len(self.nodes)) * 0.1
            CurrentDistance = self.BodyLength * base_scale_logic * shrinkRatio
            
            self.nodes[i].position = pygame.math.Vector2(startPos) 
            self.nodes[i].apply_config(GetSnakeBodyConfig())
            self.nodes[i].scaleMultiplier = shrinkRatio
        #self.nodes[0].scaleMultiplier = 0.3 
    def GetPosition(self):
        return self.nodes[0].position if self.nodes else pygame.math.Vector2(0,0)

    def GetHead(self):
        return self.nodes[0] if self.nodes else None

    def attract(self, target_node, Smoothing):
        if not self.nodes or not target_node: return
        offset = target_node.position - self.nodes[0].position
        if offset.length_squared() > 0:
            TargetSpeed = offset.normalize() * (self.MaxVelocity if Smoothing >= 0 else -self.MaxVelocity)
            self.nodes[0].direction = self.nodes[0].direction.lerp(TargetSpeed, abs(Smoothing))

    def process(self, dt):
        if not self.nodes: return

        head = self.nodes[0]
        if head.direction.length_squared() > 0.01:
            head.angle = math.degrees(math.atan2(head.direction.y, head.direction.x))

        for i in range(1, len(self.nodes)):
            curr, prev = self.nodes[i], self.nodes[i-1]
            desired_dist = self.BodyLength * base_scale_logic * curr.scaleMultiplier
            offset = curr.position - prev.position
            dist = offset.length()
            
            if dist > desired_dist:
                target_pos = prev.position + (offset / dist) * desired_dist
                curr.position = curr.position.lerp(target_pos, 0.5)
                
                if dist > 0.1:
                    curr.angle = math.degrees(math.atan2(-offset.y, -offset.x))
            
            if dist < desired_dist * 0.8 and dist > 0:
                push_dir = offset / dist
                curr.velocity += push_dir * 50.0 * dt

    def draw_outline(self, screen, camera):
        if not self.nodes: return
        for i in range(len(self.nodes) - 1, -1, -1):
            self.nodes[i].draw_outline(screen, camera)

    def draw_sprite(self, screen, camera):
        if not self.nodes: return
        for i in range(len(self.nodes) - 1, -1, -1):
            self.nodes[i].draw_sprite(screen, camera)

class AppleManager:
    speed = 400.0
    apple_node = None

    @classmethod
    def Spawn(cls, pos):
        cls.apple_node = Node(pos)
        cls.apple_node.apply_config(GetAppleConfig())

    @classmethod
    def Process(cls, dt):
        if not cls.apple_node: return
        
        keys = pygame.key.get_pressed()
        move = pygame.math.Vector2(keys[pygame.K_d] - keys[pygame.K_a], keys[pygame.K_s] - keys[pygame.K_w])
        
        if move.length_squared() > 0:
            cls.apple_node.direction = cls.apple_node.direction.lerp(move.normalize() * cls.speed, 0.2)
            cls.apple_node.textureOffsetY = math.sin(pygame.time.get_ticks() / 100.0) * 3.0 
        else:
            cls.apple_node.direction *= 0.8
            cls.apple_node.textureOffsetY = 0.0

    @classmethod
    def GetPosition(cls):
        return cls.apple_node.position if cls.apple_node else pygame.math.Vector2(0,0)


# ----------------- MAIN LOOP -----------------
class GameManager:
    def __init__(self):
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Snake Game - Cache Optimized")
        self.clock = pygame.time.Clock()

    def run(self):
        ResourceManager.get_instance().load_all_sprites("assets/sprite")
        AppleManager.Spawn((600.0, 400.0))
        
        mouse_dummy = Node((0,0)) 
        mouse_dummy.is_dummy = True 
        
        snakes = []
        for _ in range(20):
            start_p = (random.randint(100, 5000), random.randint(100, 5000))
            snakes.append(Snake(start_p, 10, 350.0 + random.randint(0, 100), 15.0, random.uniform(0.3, 0.6)))
        
        camera = pygame.math.Vector2(AppleManager.GetPosition() - pygame.math.Vector2(self.screen_width/2, self.screen_height/2))
        running = True
        
        while running:
            dt = self.clock.tick(60) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            mouse_dummy.position = AppleManager.GetPosition()
            
            for i, snake_i in enumerate(snakes):
                snake_i.process(dt)
                head_i = snake_i.GetHead()
                if not head_i: continue

                for j, snake_j in enumerate(snakes):
                    if i != j:
                        head_j = snake_j.GetHead()
                        if head_j:
                            diff_sq = head_i.position.distance_squared_to(head_j.position)
                            if diff_sq < 150*150: 
                                snake_i.attract(head_j, -0.02) 
                
                snake_i.attract(mouse_dummy, 0.1)
                
            AppleManager.Process(dt)
            process_physics_and_collisions(dt)
            
            if AppleManager.apple_node:
                target_cam = AppleManager.apple_node.position - pygame.math.Vector2(self.screen_width/2, self.screen_height/2)
                camera = camera.lerp(target_cam, 0.1)

            self.screen.fill((200, 200, 200)) 
            
            # --- RENDER LỚP 1: TOÀN BỘ VIỀN ĐEN ---
            if AppleManager.apple_node:
                AppleManager.apple_node.draw_outline(self.screen, camera)
            for snake in snakes:
                snake.draw_outline(self.screen, camera)
                
            # --- RENDER LỚP 2: TOÀN BỘ SPRITE MÀU ĐÈ LÊN ---
            if AppleManager.apple_node:
                AppleManager.apple_node.draw_sprite(self.screen, camera)
            for snake in snakes:
                snake.draw_sprite(self.screen, camera)
                
            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    GameManager().run()