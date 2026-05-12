# BÁO CÁO ĐỒ ÁN IT003.Q21.TTNT

## THÔNG TIN SINH VIÊN THỰC HIỆN
- **Mã sinh viên:** 25520109
- **Họ và tên:** Đặng Xuân Bách
- **Tên đề tài:** Rắn săn mồi

---

## 1. Thông tin cơ bản
- **Ngôn ngữ sử dụng:** Python
- **Thư viện:** Pygame

### Cấu trúc thư mục:
```text
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
├── apple.py                   # Logic thực thể Táo
├── snake_entity.py            # Logic thực thể Rắn
├── entity.py                  # Class base cho các thực thể
├── weapon.py                  # Hệ thống vũ khí (Pistol, FlameThrower...)
├── projectile.py              # Logic đạn bay
├── particle.py                # Hệ thống hạt (khói, lửa)
├── GUI.py                     # Giao diện người dùng
├── screens.py                 # Quản lý các màn hình (Menu, Playing)
├── tile.py                    # Hệ thống bản đồ/gạch
├── config.py                  # Cấu hình cài đặt game
├── resources.py               # Quản lý load tài nguyên
├── effects.py                 # Các hiệu ứng kỹ năng
├── vfx.py                     # Hiệu ứng hình ảnh (Visual Effects)
├── fps.py                     # Bộ đếm khung hình
├── drawhitbox.py              # Công cụ hỗ trợ debug va chạm
├── save_system.py             # Hệ thống lưu/tải game
├── upgrade.py                 # Quản lý nâng cấp chỉ số
├── stage.py                   # Quản lý luồng level, wave và exp/coin orbs
├── grid.py                    # Hệ thống lưới và AI chỉ đường
└── README.md                  # Bản tóm tắt báo cáo
```

---

## 2. Những nội dung đã thực hiện được
- Xây dựng game loop nơi mà người chơi điều khiển nhân vật tiêu diệt kẻ thù. 
  - *Đã phát triển:* Cơ chế thu thập kinh nghiệm (EXP) và tiền tệ (Apple Coin) cho nhân vật để lên cấp.
- Xây dựng được hệ thống vũ khí linh hoạt để có thể cập nhật thêm vũ khí bất kỳ lúc nào.
  - *Đã phát triển:* Thêm bộ vũ khí phong phú, đa dạng (RealitySlash, Pistol, AirSword...).
- Sử dụng thuật toán Noise để sinh địa hình, sinh cây cối, chướng ngại vật.
  - *Kết hợp:* Dùng hàm Hash để địa hình đa dạng và có logic ổn định hơn.
- Đã thêm texture chi tiết cho từng loại rắn.
- Gameplay tương quan đã có đủ các tính năng cơ bản (Cửa hàng/Nâng cấp qua Level Up).
- Thêm Effect/Particle (hạt bụi, khói, tia lửa) để game đẹp hơn, tăng tính "Juice".
- Đã tổng quát hóa lớp sinh vật (`Node`) để code và thêm mới thực thể dễ dàng hơn.
- Cập nhật công cụ Debug mạnh mẽ (Nhấn phím F3) để theo dõi hitbox và AI Grid.

---

## 3. Chưa thực hiện được / Dự tính làm trong tương lai
- Chưa có cơ chế cài đặt đồ họa chi tiết để người chơi sử dụng. *(Đã có khung Settings cơ bản)*
- Cần re-texture lại toàn bộ game cho đồng nhất.
- Chưa có âm thanh.
- Cần làm tổng quát hóa logic của rắn sâu hơn nữa. *(Gần đây đã tích hợp thành công thuật toán dò đường Grid-based BFS / A*)*
- Cần nâng cấp hệ thống lưu game (Mã hóa, giải mã bảo mật). *(Hiện tại đang lưu trữ dưới định dạng chuỗi JSON thô)*
- Cần thêm vật phẩm trang bị, giáp và shop bán đồ.

---

## 4. Tổng quan chi tiết Code Python

1. **`main.py`**
   - **Class GameManager:** Lớp quản lý chính.
   - `__init__`: Khởi tạo màn hình, biến môi trường và trạng thái game.
   - `setup`: Reset lại các thông số khi bắt đầu ván mới (Seed map, vị trí người chơi).
   - `handle_events`: Xử lý input từ phím (đổi vũ khí 1-7) và chuột.
   - `spawning`: Logic sinh quái (Snake) ngẫu nhiên xung quanh người chơi theo thời gian.
   - `processing`: Cập nhật logic vật lý, AI của rắn và kiểm tra va chạm.
   - `drawing`: Thực hiện Y-Sorting và vẽ các thực thể lên màn hình theo đúng thứ tự lớp.

2. **`entity.py`**
   - **Class Node:** Thực thể cơ bản nhất trong game.
   - `apply_config`: Áp dụng các thông số từ file cấu hình.
   - `deal_damage_to`: Xử lý trừ máu và kích hoạt hiệu ứng khi tấn công.
   - `draw_sprite` / `draw_shadow`: Vẽ hình ảnh và bóng đổ của thực thể.
   - Hàm `process_physics_and_collisions`: Hàm quan trọng nhất để tính toán di chuyển, ma sát và kiểm tra va chạm giữa các thực thể dựa trên hệ thống Grid Hash (tối ưu hiệu năng thay vì O(N^2)).

3. **`apple.py`**
   - **Class AppleManager:** Quản lý người chơi (nhân vật Táo).
   - `Process`: Xử lý di chuyển (WASD), hồi phục thể lực và hiệu ứng hoạt ảnh di chuyển.
   - `Dash`: Logic lướt nhanh khi nhấn chuột phải (tiêu tốn stamina, tăng tốc độ đột ngột).
   - Quản lý logic lên cấp, thu thập EXP, tiền xu.

4. **`snake_entity.py`**
   - **Class Snake:** Quản lý một con rắn gồm nhiều đốt.
   - `attract`: Điều khiển đầu rắn hướng về phía mục tiêu (AI săn mồi kết hợp thuật toán lưới).
   - `_update_body_trailing`: Logic các đốt phía sau di chuyển bám theo đốt phía trước (tạo cảm giác uốn lượn tự nhiên).

5. **`weapon.py`**
   - **Class WeaponManager:** Quản lý việc chuyển đổi và sử dụng vũ khí của người chơi.
   - Class `Weapon` (Base) và các con kế thừa (`Gun`, `Sword`, `StandWeapon`, `RealitySlash`...):
     - `attack`: Hàm thực hiện đòn đánh (bắn đạn, vung kiếm, hoặc tạo vết cắt không gian ảo).
     - `draw_special`: Vẽ các hiệu ứng riêng biệt của vũ khí (đường aim, bóng ma linh hồn).

6. **`tile.py`**
   - **Class Tile:** Một ô gạch nền.
   - **Class EnvironmentalManager:** Quản lý thực thể tĩnh (Cây, Đá).
   - `spawn_at`: Sinh vật thể dựa trên kết quả của thuật toán Noise.
   - `process`: Xử lý khi vật thể bị phá hủy (vỡ vụn) và rơi ra EXP hoặc Apple Coins / Mồi Nhử.
   - **Class TileManager:** Xử lý cơ bản đồ vô tận (Infinite Scrolling) bằng cách dịch chuyển các ô gạch khi người chơi di chuyển.

7. **`projectile.py`**
   - **Class ProjectileManager:** Quản lý đường đạn.
   - `Spawn`: Hàm tạo ra đạn/nhát chém tại một vị trí, hướng về mục tiêu với các thông số sát thương, tốc độ tùy biến.

8. **`particle.py`**
   - **Class ParticleManager:** Quản lý các hạt hiệu ứng nhỏ (`SquareParticle`, `TexturedParticle`).
   - `spawn` / `spawn_directional`: Sinh ra một cụm hạt hiệu ứng (vụ nổ, tia lửa) theo hướng chỉ định để game đẹp mắt hơn.

9. **`GUI.py`**
   - **Class ProgressBar:** Vẽ các thanh trạng thái (Máu, Stamina) với hiệu ứng tụt thanh trượt mượt mà.
   - **Class PlayerGUI:** Tổng hợp các thành phần giao diện lên góc màn hình (Thanh trạng thái, Số dư Táo vàng).
   - **Class CustomCursor:** Vẽ tâm ngắm chuột tùy biến, có hiệu ứng xoay và co giãn khi nhấn.

10. **`screens.py`**
    - **Class MenuButton:** Logic nút bấm trong menu (hiệu ứng phóng to khi di chuột qua).
    - **Class MainMenu:** Quản lý giao diện, các Slot Lưu Game (Saves) và tương tác tại màn hình khởi đầu game.

11. **`effects.py`**
    - **Class CameraShake:** Quản lý độ rung chấn của màn hình.
    - **Class EffectManager:**
      - `add_damage_number`: Hiển thị số sát thương bay lên tại vị trí va chạm.
      - `trigger_hitstop`: Tạo hiệu ứng "khựng" thời gian để tăng cảm giác uy lực.

12. **`vfx.py`**
    - **Class VFXManager:** 
      - `apply_post_processing`: Áp dụng các bộ lọc hình ảnh (Shader-like) như Vignette (viền tối) và Chromatic Aberration (nhòe màu) lên màn hình sau khi render 2D.

13. **`resources.py`**
    - **Class ResourceManager:** 
      - `load_all_sprites`: Tự động quét và nạp tất cả ảnh từ thư mục assets.
      - Hàm `get_surfaces`: Hàm tối ưu hóa (Caching) hình ảnh, giúp render ảnh xoay góc và tự tạo viền outline mà không làm giảm tốc độ khung hình (FPS).