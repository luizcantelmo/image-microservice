"""
Validadores de entrada e dados
"""
from app import config

def validate_process_image_payload(data):
    """
    Valida o payload da requisição POST /process-image
    
    Args:
        data (dict): Dados JSON da requisição
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not data:
        return False, "Payload JSON é necessário"
    
    # Validar produtos
    products = data.get('products')
    if not products:
        return False, "Parâmetro 'products' é obrigatório"
    
    if not isinstance(products, list):
        return False, "'products' deve ser uma lista"
    
    if len(products) == 0:
        return False, "'products' não pode estar vazia"
    
    if len(products) > config.MAX_PRODUCTS_PER_REQUEST:
        return False, f"Máximo de {config.MAX_PRODUCTS_PER_REQUEST} produtos por requisição"
    
    for idx, product in enumerate(products):
        if not isinstance(product, dict):
            return False, f"Produto no índice {idx} deve ser um objeto"
        
        # Validar campos obrigatórios do produto
        required_fields = ['Referencia', 'DescricaoFinal', 'Preco', 'TamanhosDisponiveis']
        for field in required_fields:
            if field not in product:
                return False, f"Produto {idx}: campo obrigatório '{field}' ausente"
    
    # Validar URL da imagem original
    original_image_url = data.get('original_image_url')
    if not original_image_url:
        return False, "Parâmetro 'original_image_url' é obrigatório"
    
    if not isinstance(original_image_url, str):
        return False, "'original_image_url' deve ser uma string"
    
    if not (original_image_url.startswith('http://') or original_image_url.startswith('https://')):
        return False, "'original_image_url' deve ser uma URL válida (http/https)"
    
    # Validar URL da marca d'água (opcional)
    watermark_url = data.get('watermark_url')
    if watermark_url and isinstance(watermark_url, str):
        if not (watermark_url.startswith('http://') or watermark_url.startswith('https://')):
            return False, "'watermark_url' deve ser uma URL válida (http/https) ou vazia"
    
    return True, None

def validate_product_data(product):
    """
    Valida e retorna dados normalizados de um produto
    
    Args:
        product (dict): Dados do produto
    
    Returns:
        dict: Produto com dados normalizados
    """
    try:
        return {
            'Referencia': str(product.get('Referencia', 'N/A')),
            'DescricaoFinal': str(product.get('DescricaoFinal', 'N/A')),
            'Preco': float(product.get('Preco', 0)),
            'PrecoPromocional': float(product.get('PrecoPromocional', 0)),
            'PrecoPromocionalAVista': float(product.get('PrecoPromocionalAVista', 0)),
            'TamanhosDisponiveis': str(product.get('TamanhosDisponiveis', 'N/A')),
            'NumeracaoUtilizada': str(product.get('NumeracaoUtilizada', 'Único')),
            'Esgotado': bool(product.get('Esgotado', False)),
        }
    except (ValueError, TypeError) as e:
        raise ValueError(f"Erro ao normalizar dados do produto: {e}")
