# Galaxy-based IBD Diagnosis System

Hệ thống hỗ trợ chẩn đoán bệnh viêm ruột (IBD) sử dụng Machine Learning và nền tảng Galaxy.

---

# Requirements

Trước khi chạy dự án, cần cài đặt:

- Docker Desktop
- Git
- PowerShell hoặc terminal trên IDE (VSCode, PyCharm,...)

---

# 1. Install Docker

Tải Docker Desktop tại:

https://www.docker.com/products/docker-desktop/

Sau khi cài đặt:

1. Mở Docker Desktop
2. Chờ Docker khởi động hoàn tất
3. Kiểm tra Docker bằng lệnh:

```bash
docker --version
```

---

# 2. Clone Project

```bash
git clone https://github.com/doanlinh25/galaxy-based-ibd-diagnosis
```
# 3. Run Docker Environment

Mở:

- PowerShell
- Hoặc terminal trên VSCode/PyCharm

Chạy file:

```powershell
./run_all.ps1
```

Script này sẽ:

- Build Docker image
- Tải toàn bộ thư viện cần thiết
- Khởi động môi trường chạy dự án

---

# 5. Output

Sau khi chạy:

- Model Machine Learning sẽ được tải từ Cloudfare
- Dữ liệu được xử lý
- Accuracy sẽ hiển thị trên terminal

Ví dụ:

```bash
Accuracy: 0.95
```

# Technologies Used

- Python
- Docker
- Scikit-learn
- Pandas
- Cloudflare R2
- Galaxy Platform
- Random Forest Classifier
