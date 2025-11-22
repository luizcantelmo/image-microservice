"""
Sistema de logging centralizado
"""
import logging
import logging.handlers
from app import config

def get_logger(name):
    """
    Retorna um logger configurado
    
    Args:
        name (str): Nome do logger (tipicamente __name__)
    
    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evita adicionar handlers múltiplas vezes
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Formatter
    formatter = logging.Formatter(config.LOG_FORMAT)
    
    # Handler para arquivo
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Erro ao configurar file handler: {e}")
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
