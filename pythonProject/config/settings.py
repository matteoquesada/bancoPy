"""
Configuration settings for SINPE Banking System
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Database settings
DATABASE_URL = f"sqlite:///{BASE_DIR}/database/banking.db"

# Security settings
SECRET_KEY = "supersecreta123"
HMAC_SECRET = "supersecreta123"

# Bank settings
LOCAL_BANK_CODE = "152"
COUNTRY_CODE = "CR"

# API settings
API_HOST = "127.0.0.1"
API_PORT = 5000
API_DEBUG = False

# CORS settings
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS = ["Content-Type", "Authorization"]

# External bank endpoints (from original config)
EXTERNAL_BANKS = {
    "152": "http://192.168.1.10:3001",
    "CB": "http://192.168.2.10:3001",
    "CR": "http://192.168.1.30:3001"
}

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Terminal UI settings
TERMINAL_REFRESH_RATE = 10  # Hz
TERMINAL_THEME = "dark"

# Pagination settings
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Transaction settings
DEFAULT_CURRENCY = "CRC"
MAX_TRANSFER_AMOUNT = 1000000.00  # 1 million CRC
MIN_TRANSFER_AMOUNT = 1.00

# Phone number validation
PHONE_NUMBER_LENGTH = 8
PHONE_NUMBER_PREFIX = ["8", "6", "7"]  # Valid Costa Rican prefixes

# Account number settings
ACCOUNT_NUMBER_LENGTH = 15
IBAN_LENGTH = 22

# Session settings
SESSION_TIMEOUT = 3600  # 1 hour in seconds