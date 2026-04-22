import pygame

SHOW_HITBOXES = True

def draw_node_hitboxes(screen, camera, active_nodes):
    """
    Hàm tĩnh hỗ trợ vẽ đường viền (Hitbox) của các Entity để kiểm tra va chạm.
    """
    if not SHOW_HITBOXES: return

    for node in active_nodes:
        if node.is_dead or node.is_dummy:
            continue
            
        # Không vẽ hitbox cho lớp cỏ Tile (do maskOut = -2)
        target_masks = node.maskOut if isinstance(node.maskOut, (list, tuple)) else [node.maskOut]
        if -2 in target_masks:
            continue

        radius = int(node.hitbox_radius * node.scaleMultiplier)
        if radius <= 0: continue
            
        draw_pos = node.position - camera
        
        # Tạo vòng tròn viền thể hiện hitbox
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        
        # Phân biệt màu dựa trên mask hoặc tên
        color = (255, 50, 50, 200)   # Đỏ: Enemy/Snake
        if node.textureName == "apple":
            color = (50, 255, 50, 200) # Xanh: Apple
        elif node.textureName == "projectile":
            color = (255, 255, 50, 200) # Vàng: Projectile
            
        # Độ dày của viền là 2 px
        pygame.draw.circle(surface, color, (radius, radius), radius, 2) 
        
        rect = surface.get_rect(center=(draw_pos.x, draw_pos.y))
        screen.blit(surface, rect)
