# 🐍 Rắn Săn Mồi

> **Đồ án IT003.Q21.TTNT** — Game hành động sinh tồn được xây dựng bằng Python & Pygame.

---

## 👤 Thông Tin Sinh Viên

| Thông tin | Chi tiết |
|-----------|----------|
| **Mã sinh viên** | 25520109 |
| **Họ và tên** | Đặng Xuân Bách |
| **Môn học** | IT003.Q21.TTNT |
| **Tên đề tài** | Rắn Săn Mồi |

---

## 🎮 Giới Thiệu Game

**Rắn Săn Mồi** là game hành động sinh tồn nhìn từ trên xuống (top-down), nơi người chơi điều khiển nhân vật **Táo** đối đầu với các bầy Rắn ngày càng mạnh hơn theo từng làn sóng (Wave). Tiêu diệt rắn để thu thập EXP và Apple Coin, lên cấp, nâng chỉ số và chinh phục những làn sóng kẻ thù nguy hiểm hơn.

---

## 🛠️ Công Nghệ Sử Dụng

- **Ngôn ngữ:** Python 3.x
- **Thư viện chính:** [Pygame](https://www.pygame.org/)
- **Thuật toán nổi bật:**
  - Grid Hash — Tối ưu hóa va chạm từ O(N²) xuống gần O(N)
  - Noise Function — Sinh địa hình vô tận ngẫu nhiên có logic
  - BFS + A* (Grid-based) — AI dò đường cho rắn

---

## 📁 Cấu Trúc Thư Mục

```
Python Project/
├── assets/                    # Tài nguyên game
│   ├── sound/                 # Âm thanh (sfx, music)
│   └── sprite/                # Hình ảnh, nhân vật, vũ khí
│       ├── aim.png
│       ├── apple.png
│       ├── flame_thrower.png
│       ├── pistol.png
│       ├── snake.png
│       └── ... (các sprite khác)
├── main.py                    # File chạy chính của Game
├── apple.py                   # Logic thực thể Táo (người chơi)
├── snake_entity.py            # Logic thực thể Rắn (kẻ thù)
├── entity.py                  # Class base Node cho các thực thể
├── weapon.py                  # Hệ thống vũ khí
├── projectile.py              # Logic đạn bay
├── particle.py                # Hệ thống hạt hiệu ứng
├── GUI.py                     # Giao diện người dùng (HUD)
├── screens.py                 # Quản lý các màn hình (Menu, Playing)
├── tile.py                    # Hệ thống bản đồ vô tận
├── config.py                  # Cấu hình và định nghĩa NodeConfig
├── resources.py               # Quản lý và cache tài nguyên
├── effects.py                 # Camera Shake, HitStop, Damage Numbers
├── vfx.py                     # Post-processing (Vignette, Chromatic Aberration)
├── fps.py                     # Bộ đếm và giới hạn khung hình
├── drawhitbox.py              # Công cụ debug va chạm
├── save_system.py             # Hệ thống lưu/tải game (JSON)
├── upgrade.py                 # Quản lý điểm nâng cấp chỉ số
├── stage.py                   # Quản lý Wave, EXP Orb, Coin Orb
├── grid.py                    # AI Grid: BFS Scent Map + A* Pathfinding
└── README.md                  # File này
```

---

## 🕹️ Hướng Dẫn Chơi

### Điều Khiển

| Phím | Hành động |
|------|-----------|
| `W` `A` `S` `D` | Di chuyển nhân vật |
| `Chuột Trái` | Tấn công / Giữ để gồng chiêu |
| `Chuột Phải` | Dash (lướt tốc độ cao, tốn Stamina) |
| `1` – `8` | Chuyển đổi vũ khí trực tiếp |
| `Q` / `E` | Cuộn vũ khí lên/xuống |
| `I` | Mở màn hình Status & Nâng Cấp |
| `P` / `ESC` | Tạm dừng game |
| `F3` | Bật/Tắt chế độ Debug (Hitbox, AI Grid) |

### Thu Thập & Tiến Triển

- **EXP Orbs** (màu xanh ngọc): Rơi ra khi tiêu diệt rắn, tự động hút về khi đủ gần.
- **Coin Orbs** (màu vàng): Có 30% tỉ lệ rơi ra từ rắn (1–3 đồng/lần).
- **Lên cấp**: Nhận thêm **Status Point** để phân bổ vào HP, Stamina hoặc Sát Thương.
- **Màn hình Status** (`I`): Khi có điểm thừa, thanh EXP sẽ hiện dấu `!` và gợi ý `Press "I" to upgrade`.

---

## ⚔️ Hệ Thống Vũ Khí

| # | Tên | Mô tả |
|---|-----|-------|
| 1 | **Pistol** | Bắn đạn đơn, tốc độ cao, tiêu chuẩn |
| 2 | **SMG** | Bắn tự động liên tục, tốn Stamina |
| 3 | **AirSword** | Kiếm gồng lực — giữ chuột để tích năng lượng, thả để tung đòn |
| 4 | **FlameThrower** | Phun lửa liên tục, gây sát thương theo thời gian |
| 5 | **StarPlatinum** | Đặt Stand triệu hồi bóng ma, đấm liên tiếp về phía chuột |
| 6 | **FlameExtinguisher** | Phun bọt đông lạnh, gây stun kẻ địch |
| 7 | **RealitySlash** | Vẽ đường cắt thực tế — click giữ 2 điểm để tạo nhát chém cực rộng |
| 8 | **TarotCard** | Ném bài Tarot bay về phía chuột, nổ ra các hiệu ứng ngẫu nhiên (Tấn công, Băng, Độc, Dịch chuyển...) |

---

## 📊 Hệ Thống Chỉ Số (Status)

Mỗi lần lên cấp, người chơi nhận **1 Status Point** để phân bổ vào:

| Chỉ số | Hiệu ứng |
|--------|----------|
| ❤️ **HP** | Tăng máu tối đa |
| ⚡ **Stamina** | Tăng thể lực tối đa (Dash, tấn công) |
| ⚔️ **Damage** | Tăng hệ số sát thương toàn bộ vũ khí |

> 💡 **Reset Stats**: Tốn **1000 Apple Coin** để hoàn trả toàn bộ Status Point đã phân bổ.

---

## 🏗️ Kiến Trúc Code Chi Tiết

### `main.py` — GameManager
Lớp quản lý vòng lặp game chính.

- `__init__`: Khởi tạo màn hình Pygame, biến trạng thái và các manager.
- `setup`: Reset thông số khi bắt đầu ván mới (seed bản đồ, vị trí nhân vật).
- `handle_events`: Xử lý input bàn phím (1–8 đổi vũ khí, I mở Status) và chuột.
- `spawning`: Logic sinh rắn ngẫu nhiên xung quanh người chơi theo tốc độ của từng Wave.
- `processing`: Cập nhật vật lý, AI rắn và kiểm tra va chạm qua Grid Hash.
- `drawing`: Y-Sorting và render các thực thể lên màn hình theo đúng thứ tự lớp.

---

### `entity.py` — Node (Base Entity)
Class nền tảng cho **mọi** vật thể trong game.

- `apply_config`: Áp dụng `NodeConfig` (sát thương, máu, knockback, mask...).
- `deal_damage_to`: Trừ máu, kích hoạt Flash, rung màn hình và số sát thương bay lên.
- `apply_knockback_to`: Đẩy bắn vật thể, kích hoạt **HitStop** (đứng hình) nếu lực đẩy đủ mạnh (>1500).
- `draw_sprite` / `draw_shadow`: Vẽ sprite và bóng đổ của thực thể.
- `process_physics_and_collisions` *(hàm trung tâm)*: Tính toán di chuyển, ma sát và kiểm tra va chạm giữa các thực thể bằng **Grid Hash** (tối ưu hiệu năng).

---

### `apple.py` — AppleManager (Người Chơi)
Quản lý toàn bộ trạng thái và tương tác của nhân vật Táo.

- `Process`: Di chuyển WASD, hồi Stamina tự nhiên, cập nhật animation.
- `Dash`: Lướt nhanh (tốn Stamina, tăng tốc đột ngột).
- `add_exp` / `add_coin`: Thu thập EXP/tiền và xử lý lên cấp, cấp phát Status Point.

---

### `snake_entity.py` — Snake (Kẻ Địch)
Quản lý một con rắn nhiều đốt với AI săn mồi thông minh.

- `attract`: Điều khiển đầu rắn bám theo mục tiêu, kết hợp BFS Scent Map và A*.
- `_update_body_trailing`: Các đốt sau bám theo đốt trước một cách tự nhiên, tạo chuyển động uốn lượn.

---

### `weapon.py` — WeaponManager & Weapon Classes
Hệ thống vũ khí mở rộng dễ dàng.

- `WeaponManager`: Quản lý đổi vũ khí, truyền góc ngắm và vị trí người chơi.
- Class `Weapon` (base) và các lớp kế thừa: `Gun`, `Sword`, `StandWeapon`, `FlameExtinguisher`, `RealitySlash`, `TarotCardWeapon`.
  - `attack`: Thực hiện đòn đánh tương ứng.
  - `draw_special`: Vẽ hiệu ứng riêng biệt của vũ khí (đường aim, bóng ma, đường chém...).

---

### `tile.py` — TileManager & EnvironmentalManager
Hệ thống bản đồ vô tận và vật thể môi trường.

- `TileManager`: Render bản đồ vô tận (Infinite Scrolling) bằng cách dịch ô gạch khi người chơi di chuyển.
- `EnvironmentalManager`: Quản lý Cây và Đá, sinh ra dựa trên Noise Function.
  - `spawn_at`: Xác định vị trí sinh vật thể qua thuật toán Noise.
  - `process`: Xử lý phá hủy vật thể và rơi ra EXP/Apple Coin.

---

### `projectile.py` — ProjectileManager
Quản lý toàn bộ đạn và vùng sát thương.

- `Spawn`: Tạo đạn/nhát chém tại vị trí chỉ định với đầy đủ thông số (sát thương, knockback, stun, lifetime) có thể override.

---

### `particle.py` — ParticleManager
Hệ thống hạt hiệu ứng.

- `spawn`: Sinh cụm hạt vụ nổ theo mọi hướng.
- `spawn_directional`: Sinh hạt theo hướng chỉ định (dùng cho đòn kiếm, lửa, v.v.).

---

### `GUI.py` — Giao Diện HUD
- `ProgressBar`: Thanh trạng thái với hiệu ứng tụt mượt mà (HP, Stamina, EXP, Wave).
- `PlayerGUI`: Tổng hợp HUD — thanh máu, stamina, EXP, hiển thị Apple Coin và thông báo Status Point.
- `CustomCursor`: Tâm ngắm chuột tùy biến có hiệu ứng xoay và co giãn khi nhấn.

---

### `screens.py` — Quản Lý Màn Hình
- `MenuButton`: Nút bấm có hiệu ứng phóng to khi hover.
- `MainMenu`: Màn hình chính với Slot Lưu Game, chọn Wave và điều hướng.
- `LevelUpMenu`: Màn hình Status & Upgrade — phân bổ điểm HP/Stamina/Damage, reset stats.

---

### `effects.py` — Hiệu Ứng Chiến Đấu
- `CameraShake`: Rung màn hình tỉ lệ với độ trauma.
- `EffectManager`:
  - `add_damage_number`: Số sát thương bay lên tại điểm va chạm.
  - `trigger_hitstop`: Đứng hình tích tắc để tăng cảm giác uy lực của đòn nặng.

---

### `vfx.py` — Post-Processing
- `VFXManager`:
  - `apply_post_processing`: Áp dụng bộ lọc **Vignette** (viền tối) và **Chromatic Aberration** (nhòe màu) lên toàn màn hình sau khi render.

---

### `resources.py` — Quản Lý Tài Nguyên
- `ResourceManager`:
  - `load_all_sprites`: Tự động quét và nạp tất cả ảnh từ thư mục `assets/`.
  - `get_surfaces`: Cache hình ảnh đã xoay góc và tự tạo viền outline — giúp duy trì FPS cao.

---

### `stage.py` — Quản Lý Wave & Orbs
- `StageManager`: Điều phối Wave, đếm số rắn đã hạ, kích hoạt Huge Wave qua Flags.
- `ExpOrb` / `CoinOrb`: Vật phẩm rơi ra, tự hút về người chơi khi đủ gần hoặc sau thời gian nhất định.
- `on_snake_killed`: Xử lý rơi EXP (tỉ lệ MaxHp) và tiền (30% cơ hội, 1–3 đồng).

---

### `grid.py` — AI Grid
- Chia bản đồ thành lưới 10×10 ô.
- **BFS Scent Map**: Tỏa "mùi táo" từ người chơi ra xung quanh để rắn có thể cảm nhận và truy đuổi hiệu quả.
- **A\* Pathfinding**: Rắn tìm đường thông minh, tránh chướng ngại vật và đạn bay.
- **Debug F3**: Hiển thị lưới, scent map và đường đi A* trực tiếp trên màn hình.

---

## ✅ Đã Thực Hiện

- [x] Game loop hoàn chỉnh với Wave System, spawn rắn động theo độ khó
- [x] Hệ thống EXP, Level Up và Status Point (HP / Stamina / Damage)
- [x] Apple Coin: thu thập từ rắn, cây, đá — dùng để Reset Stats
- [x] Hệ thống vũ khí linh hoạt, dễ mở rộng (8 vũ khí đa dạng)
- [x] Địa hình vô tận sinh bằng Noise + Hash Function
- [x] Texture chi tiết cho từng loại rắn
- [x] Hiệu ứng Particle / VFX (khói, lửa, bụi, Chromatic Aberration)
- [x] Hệ thống va chạm tối ưu bằng Grid Hash
- [x] AI rắn thông minh với BFS Scent Map + A*
- [x] Lưu/Tải game với 3 Slot (JSON)
- [x] Công cụ Debug mạnh (F3): Hitbox, AI Grid, Scent Map

## ⏳ Chưa Thực Hiện / Dự Kiến Tương Lai

- [ ] Hệ thống âm thanh (SFX, nhạc nền)
- [ ] Re-texture toàn bộ game cho đồng nhất về phong cách
- [ ] Cài đặt đồ họa chi tiết cho người chơi (chất lượng, FPS cap)
- [ ] Mã hóa file lưu game (thay thế JSON thô)
- [ ] Shop vật phẩm, trang bị và giáp
- [ ] Tổng quát hóa sâu hơn hành vi AI của rắn

---

## 🚀 Cách Chạy

```bash
# Cài đặt thư viện
pip install pygame

# Chạy game
python main.py
```

> **Yêu cầu:** Python 3.10+ và Pygame 2.x

---

*Đồ án IT003.Q21.TTNT — Đặng Xuân Bách (25520109)*