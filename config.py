class NodeConfig:
    def __init__(self, textureName="", mask=0, maskOut=0, hitbox_radius=30.0, 
                 MaxHp=100.0, knockback=10.0, damage=10.0, MinFrame=0, MaxFrame=0, 
                 textureWidth=32.0, textureHeight=32.0, scaleMultiplier=1.0, hasOutline=False, 
                 canShakeCamera=True, canApplyFlash=True, lifetime=-1.0, stun_on_hit=0.1, 
                 has_trail_particles=True, hasShadow=True):
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

# --- SNAKE CONFIGS ---
def GetSnakeHeadConfig():
    return NodeConfig(textureName="snake", mask=1, maskOut=2, hitbox_radius=30.0, MaxHp=100.0, knockback=700.0, damage=17.0, scaleMultiplier=0.5, hasOutline=True, canShakeCamera=False, stun_on_hit=0.3, hasShadow=True)
def GetSnakeBodyConfig():
    return NodeConfig(textureName="snake", mask=1, maskOut=3, hitbox_radius=30.0, MaxHp=100.0, knockback=10.0, damage=17.0, MinFrame=1, MaxFrame=1, scaleMultiplier=0.5, hasOutline=True, canShakeCamera=False, stun_on_hit=0.1, hasShadow=True)

# --- PLAYER CONFIGS ---
def GetAppleConfig():
    return NodeConfig(textureName="apple", mask=2, maskOut=[1, 5], hitbox_radius=30.0, MaxHp=100.0, knockback= 10, MaxFrame=5, scaleMultiplier=0.6, hasOutline=False, canShakeCamera=False, stun_on_hit=0.2, canApplyFlash=False, hasShadow=True)

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
    return NodeConfig(textureName="rock", mask=5, maskOut=[1, 2, 3], hitbox_radius=26.0, MaxHp=50.0, knockback=500.0, damage=0.01, scaleMultiplier=1.2, hasShadow=True, canShakeCamera = False, stun_on_hit=False, canApplyFlash=False, has_trail_particles=False)

def GetTreeConfig():
    return NodeConfig(textureName="tree", mask=5, maskOut=[1, 2, 3], hitbox_radius=21.0, MaxHp=30.0, knockback=500.0, damage=0.01, scaleMultiplier=1.5, hasShadow=True, canShakeCamera = False, stun_on_hit=False, canApplyFlash=False, has_trail_particles=False)
# --- STAND CONFIGS ---
def GetGhostPunchConfig():
    return NodeConfig(
        textureName     = "apple_ghost_punch",
        mask            = 2,
        maskOut         = [1, 5],
        hitbox_radius   = 40.0,
        knockback       = 100.0,
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
                 headConfig=None, bodyConfig=None, **kwargs):
        self.size = size
        self.velocity = velocity
        self.length = length
        self.headSize = headSize
        self.headConfig = headConfig if headConfig else GetSnakeHeadConfig()
        self.bodyConfig = bodyConfig if bodyConfig else GetSnakeBodyConfig()
        # Custom properties
        for key, value in kwargs.items():
            setattr(self, key, value)

class DefaultSnakeConfig(SnakeConfig):
    def __init__(self):
        super().__init__()

def GetNormalSnakeConfig():
    return SnakeConfig(size=12, velocity=300.0, length=16.0, headSize=0.5)

def GetFastSnakeConfig():
    return SnakeConfig(size=8, velocity=450.0, length=12.0, headSize=0.4, 
                       head_particle_color=(200, 200, 50), # Yellowish particles
                       push_force=80.0)

def GetTankSnakeConfig():
    return SnakeConfig(size=14, velocity=350.0, length=20.0, headSize=0.6,
                       death_damage=800.0,
                       head_particle_color=(100, 50, 50)) # Dark red particles