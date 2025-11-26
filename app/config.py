"""
Configurações centralizadas da aplicação
"""
import os
from datetime import timedelta

# ============== Variáveis de Ambiente ==============
# Em produção, use variáveis de ambiente do sistema ou arquivo .env

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # 'development', 'staging', 'production'

# ============== Configuração Flask ==============
FLASK_PORT = int(os.getenv('FLASK_PORT', 5001))
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')

# ============== Armazenamento de Imagens ==============
TEMP_IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'temp_processed_images')
os.makedirs(TEMP_IMAGES_DIR, exist_ok=True)

BASE_IMAGE_URL = '/processed_images'
MAX_TEMP_IMAGE_AGE = timedelta(hours=24)  # Imagens expiram após 24h

# ============== Redis/RQ (Para Fila de Tarefas) ==============
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

USE_REDIS = os.getenv('USE_REDIS', 'False').lower() == 'true'

# ============== Fontes TrueType ==============
# Coloque arquivos .ttf no diretório fonts/ ou especifique o caminho completo
FONTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'fonts')
os.makedirs(FONTS_DIR, exist_ok=True)

DEFAULT_FONT_PATH = os.path.join(FONTS_DIR, 'arial.ttf')
FONT_DESCRIPTION_SIZE = int(os.getenv('FONT_DESCRIPTION_SIZE', 17))  # Reduzido de 28 para 17 (60%)
FONT_REF_SIZE_PROMO = int(os.getenv('FONT_REF_SIZE_PROMO', 13))  # Reduzido de 22 para 13 (60%)
FONT_PRICE_SIZE = int(os.getenv('FONT_PRICE_SIZE', 18))  # Reduzido de 30 para 18 (60%)
FONT_ESGOTADO_SIZE = int(os.getenv('FONT_ESGOTADO_SIZE', 24))  # Reduzido de 40 para 24 (60%)

# ============== Layout da Imagem ==============
PADDING_X = int(os.getenv('PADDING_X', 12))  # Reduzido de 20 para 12 (60%)
PADDING_Y = int(os.getenv('PADDING_Y', 80))  # Mantém afastado da borda
LINE_HEIGHT_MULTIPLIER = float(os.getenv('LINE_HEIGHT_MULTIPLIER', 1.3))
PRODUCT_BLOCK_WIDTH_PERCENT = float(os.getenv('PRODUCT_BLOCK_WIDTH_PERCENT', 0.23))  # Reduzido de 0.38 para 0.23 (60%)

# ============== Cores ==============
# Formato RGB ou RGBA (R, G, B) ou (R, G, B, A)
COLOR_PROMO_BACKGROUND = (255, 0, 0, 200)  # Vermelho semi-transparente
COLOR_NORMAL_BACKGROUND = (0, 0, 0, 150)   # Preto semi-transparente
COLOR_TEXT_WHITE = (255, 255, 255)         # Branco
COLOR_ESGOTADO_BACKGROUND = (255, 0, 0, 180)  # Vermelho para faixa de esgotado

# ============== Qualidade de Imagem ==============
OUTPUT_IMAGE_QUALITY = int(os.getenv('OUTPUT_IMAGE_QUALITY', 90))
OUTPUT_IMAGE_FORMAT = 'JPEG'

# ============== Watermark ==============
WATERMARK_WIDTH_PERCENT = float(os.getenv('WATERMARK_WIDTH_PERCENT', 0.2))
WATERMARK_MARGIN_BOTTOM = int(os.getenv('WATERMARK_MARGIN_BOTTOM', 20))
WATERMARK_POSITION = 'bottom_center'  # Pode ser 'bottom_center', 'top_left', etc.

# ============== Logging ==============
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.path.join(LOGS_DIR, 'app.log')

# ============== Limpeza Automática ==============
CLEANUP_ENABLED = os.getenv('CLEANUP_ENABLED', 'True').lower() == 'true'
CLEANUP_INTERVAL_MINUTES = int(os.getenv('CLEANUP_INTERVAL_MINUTES', 60))

# ============== Limites e Timeouts ==============
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))  # segundos para download
TASK_TIMEOUT = int(os.getenv('TASK_TIMEOUT', 300))  # 5 minutos para processar a imagem
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))

# ============== CORS ==============
ALLOW_CORS = os.getenv('ALLOW_CORS', 'True').lower() == 'true'
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

# ============== API ==============
API_VERSION = '1.0.0'
MAX_PRODUCTS_PER_REQUEST = int(os.getenv('MAX_PRODUCTS_PER_REQUEST', 10))

def get_config_summary():
    """Retorna um resumo das configurações"""
    return {
        'environment': ENVIRONMENT,
        'debug': DEBUG,
        'flask_port': FLASK_PORT,
        'redis_enabled': USE_REDIS,
        'temp_images_dir': TEMP_IMAGES_DIR,
        'fonts_dir': FONTS_DIR,
        'logs_dir': LOGS_DIR,
        'api_version': API_VERSION,
    }
