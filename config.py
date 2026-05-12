GLOBAL_SCALE = 1
GRID_ROWS = 10
GRID_COLS = 10

class NodeConfig:
    def __init__(self, textureName="", mask=0, maskOut=0, hitbox_radius=30.0, 
                 MaxHp=100.0, knockback=10.0, damage=10.0, MinFrame=0, MaxFrame=0, 
                 textureWidth=32.0, textureHeight=32.0, scaleMultiplier=1.0, hasOutline=False, 
                 canShakeCamera=True, canApplyFlash=True, lifetime=-1.0, stun_on_hit=0.1, 
                 has_trail_particles=True, hasShadow=True, knockback_resistance=1.0, can_be_stunned=True,
                 trail_color=(200, 200, 200)):
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
        self.canShakeCamera = canShakeCamera
        self.canApplyFlash = canApplyFlash
        self.lifetime = lifetime
        self.stun_on_hit = stun_on_hit
        self.has_trail_particles = has_trail_particles
        self.hasShadow = hasShadow
        self.knockback_resistance = knockback_resistance
        self.trail_color = trail_color
        self.can_be_stunned = can_be_stunned

# --- SNAKE CONFIGS ---
def GetSnakeHeadConfig():
    return NodeConfig(textureName="snake", mask=1, maskOut=2, hitbox_radius=30.0, MaxHp=100.0, knockback=700.0, damage=17.0, scaleMultiplier=0.5, hasOutline=True, canShakeCamera=False, stun_on_hit=0.3, hasShadow=True)
def GetSnakeBodyConfig():
    return NodeConfig(textureName="snake", mask=1, maskOut=3, hitbox_radius=30.0, MaxHp=100.0, knockback=10.0, damage=17.0, MinFrame=1, MaxFrame=1, scaleMultiplier=0.5, hasOutline=True, canShakeCamera=False, stun_on_hit=0.1, hasShadow=True)

# --- PLAYER CONFIGS ---
def GetAppleConfig():
    return NodeConfig(textureName="apple", mask=2, maskOut=[1, 5], hitbox_radius=30.0, MaxHp=100.0, knockback= 10, damage=0, MaxFrame=5, scaleMultiplier=0.6, hasOutline=False, canShakeCamera=False, stun_on_hit=0.2, canApplyFlash=False, hasShadow=True)

# --- PROJECTILE CONFIGS ---
def GetProjectileConfig():
    return NodeConfig(textureName="projectile", mask=3, maskOut=[1, 5], MaxHp=0.01, hitbox_radius=30.0, knockback=700.0, damage=17.0, scaleMultiplier=0.5, hasOutline=True, canShakeCamera=False, lifetime=0.3, stun_on_hit=0.2, hasShadow=False)
def GetFlameConfig():
    return NodeConfig(textureName="flame", mask=3, maskOut=[1, 5], hitbox_radius=20.0, MaxHp=1.0, knockback=0.0, damage=5.0, MaxFrame=4, scaleMultiplier=0.3, hasOutline=False, canShakeCamera=False, lifetime=0.5, stun_on_hit=0.01, has_trail_particles=False, hasShadow=False)
def GetFoamConfig():
    return NodeConfig(textureName="foam", mask=3, maskOut=[1, 5], hitbox_radius=20.0, MaxHp=1.0, knockback=0.0, damage=0.0, MaxFrame=2, scaleMultiplier=0.3, hasOutline=False, canShakeCamera=False, lifetime=0.5, stun_on_hit=5, has_trail_particles=False, hasShadow=False)
def GetSlashConfig():
    return NodeConfig(textureName="projectile", mask=4, maskOut=[1, 5], hitbox_radius=20.0, MaxHp=1.0, knockback=0.0, damage=999.0, MaxFrame=2, scaleMultiplier=0.3, hasOutline=False, canShakeCamera=False, lifetime=0.5, stun_on_hit=5, has_trail_particles=False, hasShadow=False)

# --- ENVIRONMENTAL CONFIGS ---
def GetRockConfig():
    return NodeConfig(textureName="rock", mask=5, maskOut=[1, 2, 3], hitbox_radius=26.0, MaxHp=500.0, knockback=500.0, damage=0.01, MaxFrame=3, scaleMultiplier=1.2, hasShadow=True, canShakeCamera = False, stun_on_hit=False, canApplyFlash=False, has_trail_particles=False, hasOutline=True, knockback_resistance=0.01)

def GetTreeConfig():
    return NodeConfig(textureName="bush", mask=5, maskOut=[1, 2, 3], hitbox_radius=20.0, MaxHp=20.0, knockback=300.0, damage=0.01, MaxFrame=2, scaleMultiplier=0.8, hasShadow=True, canShakeCamera = False, stun_on_hit=False, canApplyFlash=False, has_trail_particles=False, hasOutline=True)
# --- STAND CONFIGS ---
def GetGhostPunchConfig():
    return NodeConfig(
        textureName     = "apple_ghost_punch",
        mask            = 3,
        maskOut         = [1, 5],
        hitbox_radius   = 40.0,
        knockback       = 300.0,
        damage          = 25.0,
        MaxFrame        = 1,      # 2 frame đấm (trái - phải)
        scaleMultiplier = 0.7,
        hasOutline      = True,
        canShakeCamera  = True,
        lifetime        = 0.15,
        stun_on_hit     = 0.4,
        hasShadow       = False
    )

# --- SPECIAL WEAPON CONFIGS ---
def GetSwordAirDashConfig():
    return NodeConfig(textureName="sword air dash", mask=4, maskOut=[1, 5], hitbox_radius=50.0, knockback=700.0, damage=17.0, scaleMultiplier=0.7, hasOutline=True, canShakeCamera=False, lifetime=0.3, stun_on_hit=0.5, hasShadow=False)
def GetArrowConfig():
    return NodeConfig(textureName="arrow", mask=4, maskOut=[1, 5], hitbox_radius=30.0, knockback=700.0, damage=17.0, scaleMultiplier=0.5, hasOutline=True, canShakeCamera=False, lifetime=2.0, stun_on_hit=0.4, hasShadow=False)

# --- SNAKE SYSTEM CONFIGS ---
class SnakeConfig:
    def __init__(self, size=10, velocity=350.0, length=15.0, headSize=0.5, 
                 headConfig=None, bodyConfig=None, has_bullet_awareness=False, **kwargs):
        self.size = size
        self.velocity = velocity
        self.length = length
        self.headSize = headSize
        self.headConfig = headConfig if headConfig else GetSnakeHeadConfig()
        self.bodyConfig = bodyConfig if bodyConfig else GetSnakeBodyConfig()
        self.has_bullet_awareness = has_bullet_awareness
        # Custom properties
        for key, value in kwargs.items():
            setattr(self, key, value)

class DefaultSnakeConfig(SnakeConfig):
    def __init__(self):
        super().__init__()

def GetNormalSnakeConfig():
    return SnakeConfig(size=12, velocity=300.0, length=16.0, headSize=0.5, has_bullet_awareness=True)

def GetFastSnakeConfig():
    return SnakeConfig(size=8, velocity=450.0, length=12.0, headSize=0.4, 
                       has_bullet_awareness=True,
                       head_particle_color=(200, 200, 50), # Yellowish particles
                       push_force=80.0)

def GetTankSnakeConfig():
    return SnakeConfig(size=14, velocity=350.0, length=20.0, headSize=0.6,
                       death_damage=800.0,
                       has_bullet_awareness=True,
                       head_particle_color=(100, 50, 50)) # Dark red particles

def GetStoneSnakeHeadConfig():
    return NodeConfig(textureName="snake_stone", mask=1, maskOut=2, hitbox_radius=35.0, MaxHp=1500.0, knockback=800.0, damage=50.0, MinFrame=0, MaxFrame=0, scaleMultiplier=0.7, hasOutline=True, canShakeCamera=False, stun_on_hit=0.5, hasShadow=True, knockback_resistance=0.01, can_be_stunned=False)

def GetStoneSnakeBodyConfig():
    return NodeConfig(textureName="snake_stone", mask=1, maskOut=3, hitbox_radius=35.0, MaxHp=1500.0, knockback=20.0, damage=50.0, MinFrame=1, MaxFrame=1, scaleMultiplier=0.7, hasOutline=True, canShakeCamera=False, stun_on_hit=0.2, hasShadow=True, knockback_resistance=0.01, can_be_stunned=False)

def GetStoneSnakeConfig():
    return SnakeConfig(size=15, velocity=300.0, length=22.0, headSize=1,
                       headConfig=GetStoneSnakeHeadConfig(),
                       bodyConfig=GetStoneSnakeBodyConfig(),
                       death_damage=200.0,
                       has_bullet_awareness=False,
                       head_particle_color=(150, 150, 150)) # Greyish particles

def GetVenomSnakeConfig():
    return SnakeConfig(size=8, velocity=700.0, length=14.0, headSize=0.4,
                       behavior="ranged",
                       shoot_interval=0.5,
                       ranged_damage=12.0,
                       death_damage=300.0,
                       has_bullet_awareness=True,
                       head_particle_color=(50, 255, 50)) # Venom Green particles

def GetSniperSnakeHeadConfig():
    return NodeConfig(textureName="snake_snipper", mask=1, maskOut=2, hitbox_radius=30.0, MaxHp=100.0, knockback=700.0, damage=17.0, scaleMultiplier=0.5, hasOutline=True, canShakeCamera=False, stun_on_hit=0.3, hasShadow=True)

def GetSniperSnakeConfig():
    return SnakeConfig(size=10, velocity=200.0, length=12.0, headSize=0.5,
                       behavior="sniper",
                       headConfig=GetSniperSnakeHeadConfig(),
                       shoot_interval=4.0,
                       ranged_damage=50.0, # Tăng sát thương mạnh hơn
                       death_damage=300.0,
                       has_bullet_awareness=True,
                       head_particle_color=(255, 100, 0)) # Orange particles

# --- STAGE / WAVE DATA ---
# total: Tổng số rắn cần giết để qua màn (chưa tính huge wave)
# difficulty: Hệ số nhân HP và Damage của rắn
# weights: Tỉ lệ spawn [Normal, Fast, Tank, Stone, Venom, Sniper]
# flags: Các mốc % (0.0 - 1.0) sẽ kích hoạt Huge Wave
# max_on_screen: Số lượng rắn tối đa xuất hiện cùng lúc trên map
WAVES_DATA = [    
    
    {"total": 5, "difficulty": 1.0, "weights": [80, 10, 10, 0, 0, 0], "flags": [0.5], "max_on_screen": 1},
    {"total": 10, "difficulty": 1.0, "weights": [60, 20, 20, 0, 0, 0], "flags": [0.5, 0.9], "max_on_screen": 2},
    {"total": 12, "difficulty": 1.0, "weights": [40, 30, 20, 10, 0, 0], "flags": [0.3, 0.6, 0.9], "max_on_screen": 1},
    {"total": 6, "difficulty": 1.0, "weights": [0, 0, 0, 100, 0, 0], "flags": [0.5, 0.8], "max_on_screen": 5},
    {"total": 10, "difficulty": 1.2, "weights": [0, 0, 0, 0 ,0 ,100 ], "flags": [0.3, 0.6, 0.9], "max_on_screen": 2},
    
    {"total": 15, "difficulty": 1.0, "weights": [60, 20, 10, 0, 10, 0], "flags": [0.5], "max_on_screen": 1},
    {"total": 10, "difficulty": 1.0, "weights": [0, 0, 0, 0, 0, 100], "flags": [0.5], "max_on_screen": 3},
    {"total": 30, "difficulty": 1.2, "weights": [60, 20, 20, 0, 0, 0], "flags": [0.5, 0.9], "max_on_screen": 7},
    {"total": 20, "difficulty": 1.2, "weights": [0, 0, 0, 0, 100, 0], "flags": [0.3, 0.6, 0.9], "max_on_screen": 3},
    {"total": 10, "difficulty": 1.2, "weights": [0, 0, 0, 70, 10, 20], "flags": [0.5, 0.8], "max_on_screen": 6},
    
    {"total": 20, "difficulty": 1.2, "weights": [30, 20, 10, 10, 20, 10], "flags": [0.3, 0.6, 0.9], "max_on_screen": 5},
    {"total": 10, "difficulty": 1.2, "weights": [0, 0, 0, 100, 0, 0], "flags": [0.5, 0.9], "max_on_screen": 7},
    {"total": 5, "difficulty":  5.0, "weights": [0, 0, 0, 0, 0, 100], "flags": [0.3, 0.6, 0.9], "max_on_screen": 1},
    {"total": 10, "difficulty": 1.2, "weights": [0, 0, 0, 80, 0, 20], "flags": [0.5, 0.8], "max_on_screen": 4},
    {"total": 10, "difficulty": 1.0, "weights": [0, 0, 0, 0, 80, 20], "flags": [0.5], "max_on_screen": 3},
    
    {"total": 30, "difficulty": 1.2, "weights": [30, 20, 10, 10, 20, 10], "flags": [0.5, 0.8], "max_on_screen": 4},
    {"total": 30, "difficulty": 1.2, "weights": [30, 20, 10, 10, 20, 10], "flags": [0.5, 0.8], "max_on_screen": 6},
    {"total": 30, "difficulty": 1.2, "weights": [30, 20, 10, 10, 20, 10], "flags": [0.5, 0.8], "max_on_screen": 8},
    {"total": 30, "difficulty": 1.2, "weights": [30, 20, 10, 10, 20, 10], "flags": [0.5, 0.8], "max_on_screen": 10},
    {"total": 30, "difficulty": 1.2, "weights": [30, 20, 10, 10, 20, 10], "flags": [0.5, 0.8], "max_on_screen": 12},
]