"""
Pacote de aplicação para microserviço de processamento de imagens
"""
from app import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

__version__ = config.API_VERSION
__author__ = "Image Processing Microservice"
__all__ = ['config', 'logger']
