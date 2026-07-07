# FastAPI settings
import os

APP_NAME = 'CardForge'
APP_VERSION = '1.0.0'
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'

# Server
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8000'))

# CORS
CORS_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Card generation
CARD_WIDTH = 1200
CARD_HEIGHT = 630
DEFAULT_BG_COLOR = '#1a1a2e'
DEFAULT_TEXT_COLOR = '#ffffff'
DEFAULT_ACCENT_COLOR = '#e94560'

# Rate limiting (simple)
RATE_LIMIT_PER_MINUTE = 30

# API Key for premium features (placeholder)
API_KEY_HEADER = 'X-API-Key'
