import pygame
import os

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

_RENDER_CACHE = {}

def get_surfaces(texture_name, frame, base_scale, scale_mult, angle, flash_effect, hasOutline):
    tex = ResourceManager.get_instance().get_texture(texture_name)
    if not tex: return None, None

    q_angle = int((angle % 360) / 4) * 4   
    q_scale = round(scale_mult, 1)         
    q_flash = 1 if flash_effect > 0 else 0 
    
    key = (texture_name, frame, base_scale, q_scale, q_angle, q_flash, hasOutline)
    if key in _RENDER_CACHE:
        return _RENDER_CACHE[key]

    tex_w, tex_h = 32, 32  
    rect = pygame.Rect(int(tex_w * frame), 0, tex_w, tex_h)
    try: raw_surf = tex.subsurface(rect)
    except ValueError: raw_surf = tex

    final_scale = base_scale * q_scale
    if final_scale != 1.0:
        main_surf = pygame.transform.scale(raw_surf, (int(tex_w * final_scale), int(tex_h * final_scale)))
    else:
        main_surf = raw_surf.copy()

    sprite_surf = main_surf.copy()
    if q_flash > 0:
        glow = sprite_surf.copy()
        glow.fill((255, 255, 255, int(255 * 0.8)), special_flags=pygame.BLEND_RGBA_MULT)
        sprite_surf.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    outline_surf = None
    if hasOutline:
        mask = pygame.mask.from_surface(main_surf)
        outline_base = mask.to_surface(setcolor=(0,0,0,255), unsetcolor=(0,0,0,0))
        t = 2
        new_w, new_h = main_surf.get_width() + t*2, main_surf.get_height() + t*2
        outline_surf = pygame.Surface((new_w, new_h), pygame.SRCALPHA)
        offsets = [(-t,0), (t,0), (0,-t), (0,t), (-t,-t), (-t,t), (t,-t), (t,t)]
        for dx, dy in offsets:
            outline_surf.blit(outline_base, (dx + t, dy + t))

    if q_angle != 0:
        sprite_surf = pygame.transform.rotate(sprite_surf, -q_angle)
        if outline_surf:
            outline_surf = pygame.transform.rotate(outline_surf, -q_angle)

    _RENDER_CACHE[key] = (outline_surf, sprite_surf)
    return outline_surf, sprite_surf
