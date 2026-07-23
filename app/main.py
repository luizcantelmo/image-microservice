"""
Aplicação Flask Principal
API REST para processamento de imagens com sobreescrita de dados
"""
import os
import uuid
import threading
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, after_this_request
from flask_cors import CORS

from app import config
from app.utils.logger import get_logger
from app.utils.validators import validate_process_image_payload, validate_product_data
from app.utils.task_manager import task_manager
from app.utils.image_processor import image_processor

logger = get_logger(__name__)

# Inicializar Flask
app = Flask(__name__)

# Configurar CORS
if config.ALLOW_CORS:
    CORS(app, resources={r"/api/*": {"origins": config.CORS_ORIGINS}})

# ==================== Middleware ====================

def error_handler(f):
    """Decorator para tratamento centralizado de erros"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro não tratado em {f.__name__}: {e}", exc_info=True)
            return jsonify({
                "error": "Erro interno do servidor",
                "message": str(e) if config.DEBUG else "Erro não identificado"
            }), 500
    return decorated_function

# ==================== Rotas de Saúde ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Verifica a saúde da aplicação"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": config.API_VERSION,
        "environment": config.ENVIRONMENT
    }), 200

@app.route('/config', methods=['GET'])
def get_config():
    """Retorna configurações (apenas em debug)"""
    if not config.DEBUG:
        return jsonify({"error": "Acesso negado"}), 403
    
    return jsonify(config.get_config_summary()), 200

# ==================== Rotas da API ====================

@app.route('/api/v1/process-image', methods=['POST'])
@error_handler
def process_image_request():
    """
    Endpoint para requisição de processamento de imagem
    
    Método: POST
    Content-Type: application/json
    
    Body:
    {
        "products": [
            {
                "DescricaoFinal": "Camiseta Premium",
                "Referencia": "REF-001",
                "Preco": 99.90,
                "PrecoPromocional": 79.90,
                "PrecoPromocionalAVista": 69.90,
                "TamanhosDisponiveis": "TAM 44 ao 56",
                "NumeracaoUtilizada": "G2",
                "Esgotado": false
            }
        ],
        "original_image_url": "https://...",
        "theme_url": "https://..." (opcional)
    }
    
    Response (202 Accepted):
    {
        "status": "processing",
        "task_id": "uuid",
        "status_url": "/api/v1/status/{task_id}",
        "final_image_url": "/processed_images/{task_id}.jpg"
    }
    """
    
    data = request.get_json()
    
    logger.info(f"📦 Payload RAW recebido: {list(data.keys())}")
    
    # Validar payload
    is_valid, error_message = validate_process_image_payload(data)
    if not is_valid:
        logger.warning(f"Payload inválido: {error_message}")
        return jsonify({"error": error_message}), 400
    
    products = data.get('products')
    original_image_url = data.get('original_image_url')
    
    # Buscar tema - aceita tanto theme_url quanto watermark_url
    theme_url = data.get('theme_url')
    watermark_url = data.get('watermark_url')
    
    # Buscar configurações dinâmicas (layout, cores, fonte, desconto)
    layout_config = data.get('layout_config')
    theme_config = data.get('theme_config')
    desconto_a_vista = data.get('desconto_a_vista', 5)  # Default 5%
    
    logger.info(f"🔍 DEBUG - theme_url no payload: {theme_url}")
    logger.info(f"🔍 DEBUG - watermark_url no payload: {watermark_url}")
    logger.info(f"🔍 DEBUG - layout_config: {layout_config}")
    logger.info(f"🔍 DEBUG - theme_config: {theme_config}")
    logger.info(f"🔍 DEBUG - desconto_a_vista: {desconto_a_vista}%")
    
    # Priorizar watermark_url se theme_url não existir
    if not theme_url:
        theme_url = watermark_url
        logger.info(f"💡 Usando watermark_url como theme_url: {theme_url}")
    
    # Gerar ID de tarefa
    task_id = str(uuid.uuid4())
    
    # Marcar como pendente
    task_manager.update_task_status(task_id, "PENDING")
    
    logger.info(f"========================================")
    logger.info(f"📥 NOVA REQUISIÇÃO DE PROCESSAMENTO")
    logger.info(f"   Task ID: {task_id}")
    logger.info(f"   Produtos: {len(products)}")
    logger.info(f"   URL Imagem Original: {original_image_url}")
    logger.info(f"   URL Tema/Watermark: {theme_url if theme_url else 'NENHUM'}")
    if layout_config:
        logger.info(f"   📐 Layout: blocoX={layout_config.get('blocoX')}, blocoY={layout_config.get('blocoY')}, fontePreco={layout_config.get('fontePreco')}")
        logger.info(f"   📐 Padding interno: paddingX={layout_config.get('blocoPaddingX')}, paddingY={layout_config.get('blocoPaddingY')}")
    if theme_config:
        logger.info(f"   🎨 Tema: fonte={theme_config.get('fonte')}")
    logger.info(f"   💰 Desconto à vista: {desconto_a_vista}%")
    
    # Verificar se há produtos promocionais
    has_promo = any(p.get('PrecoPromocional', 0) > 0 for p in products)
    logger.info(f"   🏷️ Produtos promocionais: {'SIM' if has_promo else 'NÃO'}")
    
    if theme_url:
        logger.info(f"   ✅ TEMA SERÁ APLICADO")
    else:
        logger.warning(f"   ⚠️ NENHUM TEMA - Verifique payload.theme_url ou payload.watermark_url")
    logger.info(f"========================================")
    
    # Iniciar processamento em background (thread)
    # Passar flag de processamento duplo se houver promoção + configs dinâmicas
    thread = threading.Thread(
        target=image_processor.process_image,
        args=(task_id, products, original_image_url, theme_url, has_promo, layout_config, theme_config, desconto_a_vista),
        daemon=True
    )
    thread.start()
    
    return jsonify({
        "status": "processing",
        "task_id": task_id,
        "status_url": f"/api/v1/status/{task_id}",
        "final_image_url": f"{config.BASE_IMAGE_URL}/{task_id}.jpg"
    }), 202

@app.route('/api/v1/legend-size', methods=['POST'])
@error_handler
def legend_size_request():
    """
    Calcula o tamanho EXATO (largura/altura em pixels) que a legenda vai ocupar pra
    uma lista de produtos, sem baixar nem renderizar imagem nenhuma — só mede texto
    com as mesmas fontes/métricas do PIL usadas no render de verdade. Síncrono
    (não usa a fila de tarefas) porque é rápido, só medição de texto.

    Body:
    {
        "products": [ ...mesmo formato de /api/v1/process-image... ],
        "layout_config": {...} (opcional, mesmo formato de /api/v1/process-image)
    }

    Response (200):
    { "width": 388, "height": 210, "temPromocao": false }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Payload JSON é necessário"}), 400

    products = data.get('products')
    if not products or not isinstance(products, list):
        return jsonify({"error": "Parâmetro 'products' é obrigatório e deve ser uma lista não vazia"}), 400
    if len(products) > config.MAX_PRODUCTS_PER_REQUEST:
        return jsonify({"error": f"Máximo de {config.MAX_PRODUCTS_PER_REQUEST} produtos por requisição"}), 400

    try:
        normalized_products = [validate_product_data(p) for p in products]
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    layout_config = data.get('layout_config')
    width, height, tem_promocao = image_processor.calculate_legend_size(normalized_products, layout_config)

    return jsonify({"width": width, "height": height, "temPromocao": tem_promocao}), 200

@app.route('/api/v1/status/<task_id>', methods=['GET'])
@error_handler
def get_status(task_id):
    """
    Endpoint para consultar status de uma tarefa
    
    Método: GET
    URL: /api/v1/status/{task_id}
    
    Response (200 OK):
    {
        "status": "COMPLETED|PROCESSING|PENDING|FAILED",
        "task_id": "uuid",
        "final_image_url": "/processed_images/{task_id}.jpg" (se COMPLETED),
        "error_message": "..." (se FAILED)
    }
    """
    
    status_data = task_manager.get_task_status(task_id)
    
    if status_data["status"] == "NOT_FOUND":
        logger.warning(f"Tarefa não encontrada: {task_id}")
        return jsonify({
            "error": "Tarefa não encontrada ou expirada",
            "task_id": task_id
        }), 404
    
    response = {
        "status": status_data["status"],
        "task_id": task_id,
        "timestamp": status_data.get("timestamp")
    }
    
    if status_data["status"] == "COMPLETED":
        response["final_image_url"] = f"{config.BASE_IMAGE_URL}/{task_id}.jpg"
        # Se houver versão normal (sem tema), incluir também
        if status_data.get("normal_path"):
            response["normal_image_url"] = f"{config.BASE_IMAGE_URL}/{task_id}_normal.jpg"
            logger.info(f"✅ Dupla versão disponível: promocional + normal")
    elif status_data["status"] == "FAILED":
        response["error_message"] = status_data.get("error")
    
    logger.info(f"Status consultado para tarefa {task_id}: {status_data['status']}")
    return jsonify(response), 200

@app.route('/processed_images/<filename>', methods=['GET'])
@error_handler
def serve_image(filename):
    """
    Endpoint para servir a imagem processada
    
    Método: GET
    URL: /processed_images/{filename}.jpg
    
    Behavior:
    - Verifica se a imagem está completa
    - Serve a imagem
    - Remove o arquivo após o download
    - Limpa o status da tarefa
    """
    
    # Extrair task_id do filename, removendo sufixos como _normal
    task_id_from_filename = filename.replace('.jpg', '').replace('_normal', '')
    is_normal_version = '_normal' in filename
    
    status_data = task_manager.get_task_status(task_id_from_filename)
    
    logger.info(f"[v2.2] Servindo arquivo: {filename}, task_id: {task_id_from_filename}, is_normal: {is_normal_version}")
    
    # Verificar status
    if status_data["status"] == "PROCESSING" or status_data["status"] == "PENDING":
        logger.info(f"Imagem ainda em processamento: {task_id_from_filename}")
        return jsonify({
            "status": "processing",
            "message": "Imagem ainda está sendo processada. Tente novamente em alguns segundos."
        }), 202
    
    if status_data["status"] != "COMPLETED" or not status_data.get("final_path"):
        logger.error(f"Imagem não pronta ou não existe: {task_id_from_filename}")
        return jsonify({
            "error": "Imagem não está pronta ou não existe"
        }), 404
    
    # Escolher o caminho correto baseado na versão solicitada
    if is_normal_version:
        # Versão normal solicitada
        file_path = status_data.get('normal_path')
        if not file_path:
            # Se não existe versão normal separada, usar o final_path principal
            file_path = status_data['final_path']
            logger.info(f"[v2.2] Versão normal não encontrada, usando final_path")
    else:
        # Versão promocional/padrão
        file_path = status_data['final_path']
    
    logger.info(f"[v2.2] Caminho escolhido: {file_path}")
    
    # Verificar se arquivo existe
    if not os.path.exists(file_path):
        logger.error(f"Arquivo não encontrado no disco: {file_path}")
        task_manager.delete_task_status(task_id_from_filename)
        return jsonify({
            "error": "Arquivo não encontrado"
        }), 404
    
    # Extrair nome do arquivo do caminho
    actual_filename = os.path.basename(file_path)
    logger.info(f"[v2.2] Servindo imagem: {actual_filename} (solicitado: {filename})")
    
    # Verificar se existe versão dual (normal + promo)
    has_dual_version = status_data.get('normal_path') is not None
    
    @after_this_request
    def cleanup_after_serve(response):
        """Remove a imagem e limpa o status após servir"""
        try:
            # Remover o arquivo que foi servido
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"[v2.2] Arquivo servido removido: {file_path}")
            
            # Se tem versão dual, não deletar o status ainda - aguardar segunda requisição
            if has_dual_version:
                # Verificar se ambos os arquivos foram servidos
                normal_exists = status_data.get('normal_path') and os.path.exists(status_data['normal_path'])
                promo_exists = status_data.get('final_path') and os.path.exists(status_data['final_path'])
                
                if not normal_exists and not promo_exists:
                    # Ambos foram servidos, pode limpar o status
                    task_manager.delete_task_status(task_id_from_filename)
                    logger.info(f"[v2.2] Status da tarefa removido (dual completo): {task_id_from_filename}")
                else:
                    logger.info(f"[v2.2] Aguardando segunda requisição (normal={normal_exists}, promo={promo_exists})")
            else:
                # Versão única, pode limpar o status
                task_manager.delete_task_status(task_id_from_filename)
                logger.info(f"[v2.2] Status da tarefa removido: {task_id_from_filename}")
        except Exception as e:
            logger.error(f"Erro ao limpar arquivo/status {task_id_from_filename}: {e}")
        
        return response
    
    return send_from_directory(config.TEMP_IMAGES_DIR, actual_filename, mimetype='image/jpeg')

@app.route('/api/v1/tasks', methods=['GET'])
@error_handler
def get_all_tasks():
    """
    Endpoint para listar todas as tarefas (apenas em debug)
    Útil para monitoramento
    """
    
    if not config.DEBUG:
        return jsonify({"error": "Acesso negado"}), 403
    
    tasks = task_manager.get_all_tasks()
    
    return jsonify({
        "total_tasks": len(tasks),
        "tasks": tasks
    }), 200

@app.route('/api/v1/cleanup', methods=['POST'])
@error_handler
def cleanup_old_tasks():
    """
    Endpoint para limpeza manual de tarefas antigas (apenas em debug)
    """
    
    if not config.DEBUG:
        return jsonify({"error": "Acesso negado"}), 403
    
    max_age_hours = request.args.get('max_age_hours', 24, type=int)
    task_manager.cleanup_old_tasks(max_age_hours)
    
    return jsonify({
        "message": f"Limpeza concluída (tarefas com mais de {max_age_hours}h removidas)"
    }), 200

# ==================== Tratamento de Erros ====================

@app.errorhandler(404)
def not_found(error):
    """Erro 404 - Não encontrado"""
    return jsonify({
        "error": "Recurso não encontrado",
        "path": request.path
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Erro 405 - Método não permitido"""
    return jsonify({
        "error": "Método não permitido",
        "method": request.method,
        "path": request.path
    }), 405

@app.errorhandler(500)
def internal_server_error(error):
    """Erro 500 - Erro interno do servidor"""
    logger.error(f"Erro interno do servidor: {error}", exc_info=True)
    return jsonify({
        "error": "Erro interno do servidor"
    }), 500

# ==================== Inicialização ====================

@app.before_request
def log_request():
    """Log das requisições recebidas"""
    if request.path not in ['/health', '/favicon.ico']:
        logger.info(f"{request.method} {request.path}")

@app.teardown_appcontext
def cleanup_context(error):
    """Limpeza ao final do contexto da aplicação"""
    if error:
        logger.error(f"Erro durante teardown: {error}")

def create_app():
    """Factory function para criar a aplicação"""
    logger.info("Iniciando aplicação Flask")
    logger.info(f"Configuração: {config.get_config_summary()}")
    return app

if __name__ == '__main__':
    logger.info(f"Servidor Flask iniciando em {config.FLASK_HOST}:{config.FLASK_PORT}")
    logger.info(f"Debug mode: {config.DEBUG}")
    logger.info(f"Ambiente: {config.ENVIRONMENT}")
    
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.DEBUG,
        threaded=True
    )
