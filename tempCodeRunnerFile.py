                        laze_alpha = 0 # Tắt tạm thời
                
                laze_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                pygame.draw.line(laze_surf, (255, 0, 0, laze_alpha), screen_start, screen_target, 3)
                self.screen.blit(laze_surf, (0, 0))

        def get_render_priority(node):
            # Các layer đặc biệt luôn nằm trên cùng
            if node.textureName == "projectile":  return 2000000
            if node.textureName == "sword air dash": return 2100000
            if node is apple_node_ref: return node.position.y + 100000 # Táo (Player) luôn ưu tiên cao hơn chút trong cùng mức Y
            
            # Lấy Y gốc
            if node.snake_head:
                return node.snake_head.position.y - (node.snake_depth * 0.01)
                
            return node.position.y

        render_nodes = sorted(
            (n for n in active_nodes if n.mask != -1),
