import pygame
import os
import sys
from config import GLOBAL_SCALE

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối đến tài nguyên, dùng cho cả dev và khi đóng gói .exe """
    try:
        # PyInstaller tạo ra một thư mục tạm và lưu đường dẫn trong _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ResourceManager:
    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None: cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.textures = {}
        self.fonts = {} # path -> {size -> Font}

    def load_all_sprites(self, directory):
        """Quét thư mục `directory` và nạp tất cả file PNG/JPG/BMP vào bộ nhớ theo dạng `{tên_file: Surface}`."""
        full_dir = resource_path(directory)
        if not os.path.exists(full_dir): return
        for file in os.listdir(full_dir):
            if file.endswith((".png", ".jpg", ".bmp")):
                name = os.path.splitext(file)[0]
                path = os.path.join(full_dir, file)
                try:
                    self.textures[name] = pygame.image.load(path).convert_alpha()
                except: continue

    def load_all_fonts(self, directory):
        """Quét thư mục `directory` và lưu lại đường dẫn của các file font (.ttf/.otf) để có thể nạp lát khi cần."""
        full_dir = resource_path(directory)
        if not os.path.exists(full_dir): return
        for file in os.listdir(full_dir):
            if file.endswith((".ttf", ".otf")):
                name = os.path.splitext(file)[0]
                path = os.path.join(full_dir, file)
                self.fonts[name] = path

    def get_texture(self, name):
        """Trả về Surface của texture theo tên, hoặc None nếu không tìm thấy."""
        return self.textures.get(name, None)

    def get_font(self, name, size):
        """Lấy font theo tên và kích cỡ, có cache bằng dict `{(name, size): Font}`
        để tránh tại lại file font mỗi lần gọi. Fallback về Arial nếu không tìm thấy font."""
        path = self.fonts.get(name)
        if not path:
            return pygame.font.SysFont("Arial", size)
        
        # Cache font objects by size to avoid reloading
        if not hasattr(self, '_font_cache'):
            self._font_cache = {}
        
        key = (name, size)
        if key not in self._font_cache:
            try:
                self._font_cache[key] = pygame.font.Font(path, size)
            except:
                return pygame.font.SysFont("Arial", size)
        return self._font_cache[key]

_RENDER_CACHE = {}

def get_surfaces(texture_name, frame, base_scale, scale_mult, angle, flash_effect, hasOutline):
    """Lấy cặp (outline_surf, sprite_surf) từ **Render Cache** (`dict` toàn cục `_RENDER_CACHE`).

    Thuật toán Cache (cơ chế tương tự LRU Cache nhưng không có límit):
    - **Quantization** (đơn giản hóa key):
      * Góc `angle` làm tròn theo bội4 (`int(angle/4)*4`) — giảm 90 giá trị angle khủ thành 90.
      * Scale làm tròn 1 chữ số thập phân (`round(scale, 1)`) — gom các giá trị gần nhau.
      * Flash lưu dưới dạng nhị phân (0/1).
    - Cache key: `(texture_name, frame, base_scale, q_scale, q_angle, q_flash, hasOutline, GLOBAL_SCALE)`.
    - Nếu **miss** (chưa có trong cache): tạo mới, đưa vào dict và trả về.

    Thuật toán tạo Outline bằng **Pixel Mask**:
    - Tạo `pygame.Mask` từ sprite, chuyển sang surface đen.
    - Blit 8 bản sao lệch theo 8 hướng (t, -t, 0) để tạo viền ngoài dày 2px mà không dùng shader."""
    tex = ResourceManager.get_instance().get_texture(texture_name)
    if not tex: return None, None

    q_angle = int((angle % 360) / 4) * 4   
    q_scale = round(scale_mult, 1)         
    q_flash = 1 if flash_effect > 0 else 0 
    
    key = (texture_name, frame, base_scale, q_scale, q_angle, q_flash, hasOutline, GLOBAL_SCALE)
    if key in _RENDER_CACHE:
        return _RENDER_CACHE[key]

    tex_w, tex_h = 32, 32  
    rect = pygame.Rect(int(tex_w * frame), 0, tex_w, tex_h)
    try: raw_surf = tex.subsurface(rect)
    except ValueError: raw_surf = tex

    final_scale = base_scale * q_scale * GLOBAL_SCALE
    
    # Xử lý xóa kẽ hở (Seams) cho Tile khi thu nhỏ ở tỷ lệ lẻ
    if texture_name in ["grass", "stone", "stone_border"]:
        final_scale *= 1.02 # Thêm 2% kích thước để các ô gạch gối đầu lên nhau
        
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
