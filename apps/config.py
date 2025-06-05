# -*- encoding: utf-8 -*-
"""
Project Configuration - MySQL ONLY (No SQLite fallback)
"""

import os
from pathlib import Path
from decouple import config  # Đọc biến từ .env cho an toàn và dễ chỉnh sửa

class Config(object):

    # ------------------------------
    # Các biến cấu hình chung
    # ------------------------------
    BASE_DIR = Path(__file__).resolve().parent

    # Phân quyền User (Role và Status)
    USERS_ROLES  = {'ADMIN': 1, 'USER': 2}
    USERS_STATUS = {'ACTIVE': 1, 'SUSPENDED': 2}

    # ------------------------------
    # Cấu hình Celery (nếu dùng)
    # ------------------------------
    CELERY_BROKER_URL     = "redis://localhost:6379"
    CELERY_RESULT_BACKEND = "redis://localhost:6379"
    CELERY_HOSTMACHINE    = "celery@app-generator"

    # ------------------------------
    # Secret Key (bảo mật session, CSRF)
    # ------------------------------
    SECRET_KEY = config('SECRET_KEY', default='abc123')

    # ------------------------------
    # Social Login (Github, Google)
    # ------------------------------
    SOCIAL_AUTH_GITHUB = False
    GITHUB_ID          = config('GITHUB_ID', default=None)
    GITHUB_SECRET      = config('GITHUB_SECRET', default=None)
    if GITHUB_ID and GITHUB_SECRET:
        SOCIAL_AUTH_GITHUB = True

    SOCIAL_AUTH_GOOGLE = False
    GOOGLE_ID          = config('GOOGLE_ID', default=None)
    GOOGLE_SECRET      = config('GOOGLE_SECRET', default=None)
    if GOOGLE_ID and GOOGLE_SECRET:
        SOCIAL_AUTH_GOOGLE = True

    # ------------------------------
    # Kết nối MySQL (KHÔNG có SQLite)
    # ------------------------------
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
        config('DB_ENGINE'),
        config('DB_USERNAME'),
        config('DB_PASS'),
        config('DB_HOST'),
        config('DB_PORT'),
        config('DB_NAME')
    )

    # Cấu hình thư mục lưu trữ file
    # ------------------------------
    UPLOAD_FOLDER = r"E:\ĐHBKĐN\BKĐN-Năm 4, Học kì 2\PBL7\PBL7_Main\static\uploads"  # Đường dẫn tuyệt đối

    # Các loại file cho phép tải lên
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}


    # ------------------------------
    # ------------------------------
    # Dynamic DataTable (nếu có dùng)
    # ------------------------------
    DYNAMIC_DATATB = {
        "products": "apps.models.Product"
    }

    # ------------------------------
    # CDN (nếu có dùng)
    # ------------------------------
    CDN_DOMAIN = config('CDN_DOMAIN', default=None)
    CDN_HTTPS  = config('CDN_HTTPS', default=True)

# ------------------------------
# Cấu hình cho từng môi trường (Debug / Production)
# ------------------------------
class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

class DebugConfig(Config):
    DEBUG = True

# ------------------------------
# Tạo dictionary để chọn cấu hình dễ dàng
# ------------------------------
config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}
