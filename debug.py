import pygame
from grid import GridManager
import drawhitbox

class DebugManager:
    show_debug = False
    
    @classmethod
    def draw(cls, screen, camera, active_nodes):
        from settings import SettingsManager
        settings = SettingsManager.get_instance()
        
        # Vẽ Grid AI (BFS và Danger Map)
        if settings.get("video", "show_grid"):
            GridManager.get_instance().draw_debug(screen, camera)
        
        # Vẽ Hitboxes
        if settings.get("video", "show_hitbox"):
            drawhitbox.draw_node_hitboxes(screen, camera, active_nodes)
