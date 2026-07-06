# Sử dụng Python slim image làm base
FROM python:3.11-slim

# Thiết lập biến môi trường tránh sinh file .pyc và buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép file requirements.txt
COPY requirements.txt .

# Cài đặt thêm các gói backend cần thiết (FastAPI, Uvicorn)
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Tạo User không phải root với UID 1000 (yêu cầu bắt buộc của Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

# Expose cổng mặc định của Hugging Face Spaces
EXPOSE 7860

# Lệnh khởi chạy FastAPI backend API (nạp ứng dụng từ file app.py)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
