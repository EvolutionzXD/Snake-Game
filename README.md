# 🐍 Snake Game

Dự án này là một **Custom Game Engine 2D** được viết bằng **Python & Pygame**, thiết kế theo cấu trúc module linh hoạt giúp dễ dàng đọc hiểu và mở rộng.

---

## 📂 Cấu Trúc Thư Mục (Project Structure)

```text
Python Project/
├── assets/             # Hình ảnh, âm thanh của game
├── main.py             # File khởi chạy chính và quản lý vòng lặp Game
├── entity.py           # Class base xử lý vật lý và va chạm cho mọi đối thủ
├── apple.py            # Logic điều khiển nhân vật người chơi (Player)
├── snake_entity.py     # Hệ thống AI và chuyển đổi của kẻ thù (Rắn)
├── weapon.py           # Hệ thống vũ khí đa dạng (Súng, Kiếm, Stand)
├── tile.py             # Sinh bản đồ ngẫu nhiên bằng Noise thuật toán
├── GUI.py              # Giao diện hiển thị (HP, Stamina, Cursor)
├── config.py           # Nơi cấu hình toàn bộ chỉ số của Game
└── resources.py        # Bộ quản lý nạp tài nguyên tập trung
```

---

## 🏗 Cấu Trúc Vòng Lặp Game (The Game Loop)

Trái tim của dự án nằm trong class `GameManager` (`main.py`), chia làm 4 giai đoạn rõ rệt mỗi khung hình:

1. **`handle_events()`**: Lắng nghe và điều phối Input (Bàn phím, chuột).
2. **`spawning()`**: Điều khiển kịch bản sinh vật thể (Spawn logic).
3. **`processing()`**: **"Bộ não"** xử lý logic di chuyển, AI và va chạm.
4. **`drawing()`**: **"Họa sĩ"** vẽ bóng đổ, viền, hình ảnh và hạt bụi (Particles) theo thứ tự Z-index.

---

## 🧱 Hệ Thống Thực Thể (Entity System)

### 1. Class `Node` (`entity.py`)
Mọi vật thể tương tác vật lý (Rắn, Người chơi, Đạn...) đều kế thừa từ `Node`.
- **Va chạm tự động**: Tối ưu qua hệ thống `mask` và `maskOut`.
- **Logic nội tại**: Chớp trắng khi trúng đòn, giật lùi (knockback), và máu (Hp).

### 2. Các Hệ Thống Quản Trị (Managers)
- **`EffectManager`**: Điều hành hiệu ứng "Juice" (như Hitstop - khựng màn hình).
- **`ParticleManager`**: Hệ thống hạt văng tóe (bụi, tia lửa) tối ưu hiệu năng.
- **`CameraShake`**: Hệ thống rung lắc màn hình tạo cảm giác lực.

---

## ⚙️ Hệ Thống Cấu Hình (Config Driven)

Mọi thiết lập chỉ số, cân bằng game đều quy tụ về **`config.py`**. Bạn có thể tạo ra một loài rắn mới chỉ bằng cách định nghĩa cấu hình mà không cần sửa code logic:

```python
def GetMyCustomSnakeConfig():
    return SnakeConfig(
        size=15,               # Độ dài
        velocity=400.0,        # Tốc độ
        head_particle_color=(255, 0, 0) # Màu hiệu ứng đặc trưng
    )
```

---

## 🚀 Cẩm Nang Mở Rộng

- **Đổi giao diện/Hiệu ứng đồ họa?** -> Sửa hàm `drawing()` trong `main.py`.
- **Thêm Vũ Khí mới?** -> Kế thừa class vũ khí trong `weapon.py`.
- **Sửa luật va chạm?** -> Sửa hàm `process_physics_and_collisions()` trong `entity.py`.

---
**Quy tắc Vàng**: Hãy luôn tính toán mọi thứ ở bước **Processing** trước, sau đó mới đẩy kết quả sang bước **Drawing** để hiển thị!