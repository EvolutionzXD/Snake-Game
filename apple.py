import pygame
import math
import random
from entity import Node
from config import GetAppleConfig
from particle import ParticleManager

class AppleManager:
    speed = 400.0
    speed_multiplier = 1.0 # Vũ khí có thể ghi đè biến này để làm chậm
    apple_node = None
    
    stamina = 1000.0
    max_stamina = 1000.0
    
    dash_timer = 0.0      # Thời gian còn lại của cú Dash
    dash_cooldown = 0.0   # Thời gian hồi Dash
    DASH_DURATION = 0.5
    DASH_COOLDOWN_TIME = 0.6

    @classmethod
    def Spawn(cls, pos):
        cls.apple_node = Node(pos)
        cls.apple_node.apply_config(GetAppleConfig())

    @classmethod
    def Process(cls, dt):
        if not cls.apple_node: return
        
        # Hồi máu (1% mỗi giây) và Hồi thể lực (5% mỗi giây)
        if cls.apple_node.Hp > 0:
            cls.apple_node.Hp = min(cls.apple_node.MaxHp, cls.apple_node.Hp + cls.apple_node.MaxHp * 0.01 * dt)
        cls.stamina = min(cls.max_stamina, cls.stamina + cls.max_stamina * 0.05 * dt)

        # Reset multiplier mỗi frame, vũ khí sẽ set lại nếu cần
        current_mult = cls.speed_multiplier
        cls.speed_multiplier = 1.0 
        
        # Giảm cooldown
        if cls.dash_cooldown > 0: cls.dash_cooldown -= dt
        
        # Xử lý Dash & Animation
        if cls.dash_timer > 0:
            cls.dash_timer -= dt
            cls.apple_node.MinFrame = 2
            cls.apple_node.MaxFrame = 5
            progress = (cls.DASH_DURATION - cls.dash_timer) / cls.DASH_DURATION
            # Gán frame offset (0 đến 3) để khi cộng MinFrame=2 sẽ ra 2,3,4,5
            cls.apple_node.frame = int(progress * 3.9) 
        else:
            cls.apple_node.MinFrame = 0
            cls.apple_node.MaxFrame = 1
            # Không cần gán frame = 0 ở đây để entity.py tự chạy animation 0-1
            
        # Tính toán tốc độ di chuyển
        current_speed = cls.speed * current_mult
            
        keys = pygame.key.get_pressed()
        move = pygame.math.Vector2(keys[pygame.K_d] - keys[pygame.K_a], keys[pygame.K_s] - keys[pygame.K_w])
        
        # Di chuyển và lật hình ảnh
        if move.length_squared() > 0:
            if cls.dash_timer <= 0:
                cls.apple_node.direction = cls.apple_node.direction.lerp(move.normalize() * current_speed, 0.2)
                if move.x < 0: cls.apple_node.flipX = True
                elif move.x > 0: cls.apple_node.flipX = False
                
            cls.apple_node.textureOffsetY = math.sin(pygame.time.get_ticks() * cls.speed/10000) * 3.0 - cls.apple_node.textureHeight * cls.apple_node.scaleMultiplier
            
            # --- BỤI KHI CHẠY ---
            if random.random() < 0.5 and cls.dash_timer <= 0:
                back_dir = -move.normalize()
                dust_pos = cls.apple_node.position + back_dir * 15
                ParticleManager.get_instance().spawn(pos=dust_pos, count=1, color=(200, 185, 140), alpha=140, size_range=(3, 7), speed_range=(20, 80), lifetime=0.3, gravity=120.0)
        else:
            if cls.dash_timer <= 0:
                cls.apple_node.direction *= 0.8
            cls.apple_node.textureOffsetY = - cls.apple_node.textureHeight * cls.apple_node.scaleMultiplier

    @classmethod
    def Dash(cls, power=2000.0):
        if not cls.apple_node or cls.dash_cooldown > 0 or cls.stamina < 30.0: return
        
        cls.stamina -= 10.0 # Tiêu hao 10 thể lực mỗi lần Dash
        
        keys = pygame.key.get_pressed()
        move_dir = pygame.math.Vector2(keys[pygame.K_d] - keys[pygame.K_a], keys[pygame.K_s] - keys[pygame.K_w])
        
        if move_dir.length_squared() > 0:
            dash_direction = move_dir.normalize()
        else:
            if cls.apple_node.direction.length_squared() > 0:
                dash_direction = cls.apple_node.direction.normalize()
            else:
                dash_direction = pygame.math.Vector2(1, 0)
        
        if dash_direction.x < 0: cls.apple_node.flipX = True
        elif dash_direction.x > 0: cls.apple_node.flipX = False

        cls.apple_node.velocity = dash_direction * power
        cls.apple_node.stun = 0.5
        cls.apple_node.invincibility = 0.5
        cls.dash_timer = cls.DASH_DURATION
        cls.dash_cooldown = cls.DASH_COOLDOWN_TIME
        
        ParticleManager.get_instance().spawn(pos=cls.apple_node.position, count=15, color=(255, 255, 255), alpha=150, size_range=(4, 10), speed_range=(50, 300), lifetime=0.4, gravity=0.0)

    @classmethod
    def GetPosition(cls):
        return cls.apple_node.position if cls.apple_node else pygame.math.Vector2(0,0)
