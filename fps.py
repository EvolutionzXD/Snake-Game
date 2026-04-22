import pygame

class FPSCounter:
    def __init__(self, font_size=20, color=(255, 255, 255), position=(10, 10)):
        self.font = pygame.font.SysFont("Arial", font_size, bold=True)
        self.color = color
        self.position = position
        
    def draw(self, screen, clock, node_count, snake_count=0, static_count=0):
        fps = str(int(clock.get_fps()))
        fps_text = self.font.render(f"FPS: {fps}", True, (0, 255, 0))
        node_text = self.font.render(f"Nodes: {node_count}", True, (200, 200, 255))
        snake_text = self.font.render(f"Snakes: {snake_count}", True, (255, 100, 100))
        static_text = self.font.render(f"Static: {static_count}", True, (0, 200, 255))
        
        screen_w = screen.get_width()
        
        fps_rect = fps_text.get_rect(topright=(screen_w - 15, 10))
        node_rect = node_text.get_rect(topright=(screen_w - 15, 32))
        snake_rect = snake_text.get_rect(topright=(screen_w - 15, 54))
        static_rect = static_text.get_rect(topright=(screen_w - 15, 76))
        
        # Nền cho chữ (bao quát cả 4 dòng)
        max_w = max(fps_rect.width, node_rect.width, snake_rect.width, static_rect.width)
        bg_rect = pygame.Rect(0, 0, max_w + 20, 100)
        bg_rect.topright = (screen_w - 10, 8)
        
        # Box nền bo góc trong suốt
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (0, 0, 0, 150), (0, 0, bg_rect.width, bg_rect.height), border_radius=10)
        screen.blit(bg_surface, bg_rect)
        
        screen.blit(fps_text, fps_rect)
        screen.blit(node_text, node_rect)
        screen.blit(snake_text, snake_rect)
        screen.blit(static_text, static_rect)
