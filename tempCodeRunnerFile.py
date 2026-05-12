        super().__init__(name, config_func, **kwargs)
        self.swing_progress = 0.0
        self.sword_spawns_done = 0
        self.charge_values = {"kb": 0, "stun": 0, "dmg": 0}

    def attack(self, manager, pos, target_pos, is_holding):
        current_time = time.time()
        
        if is_holding:
            if not self.is_charging and current_time - self.last_fire_time >= self.fire_rate:
                # Ngăn gồng kiếm nếu không còn thể lực
                if AppleManager.stamina < self.stamina_cost: return False
                
                self.is_charging = True
                self.charge_start_time = current_time 
                self.swing_progress = 1.0 
                self.sword_spawns_done = 0
            return False
        else:
            if self.is_charging:
                charge_dur = current_time - self.charge_start_time
                self.charge_values["kb"] = min(400 + (charge_dur * 2300), 3000)
                self.charge_values["stun"] = min(0.5 + (charge_dur * 0.5), 1.5)
                self.charge_values["dmg"] = min(10 + (charge_dur * 30), 90)
                self.is_charging = False
                self.last_fire_time = current_time
                self.swing_progress = 0.89 
                
