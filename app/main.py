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
    
    # Validar payload
    is_valid, error_message = validate_process_image_payload(data)
    if not is_valid:
        logger.warning(f"Payload inválido: {error_message}")
        return jsonify({"error": error_message}), 400
    
    products = data.get('products')
    original_image_url = data.get('original_image_url')
    theme_url = data.get('theme_url')
    
    # Gerar ID de tarefa
    task_id = str(uuid.uuid4())
    
    # Marcar como pendente
    task_manager.update_task_status(task_id, "PENDING")
    
    logger.info(f"Nova requisição de processamento: task_id={task_id}, produtos={len(products)}")
    
    # Iniciar processamento em background (thread)
    # Em produção, usar RQ ou Celery
    thread = threading.Thread(
        target=image_processor.process_image,
        args=(task_id, products, original_image_url, theme_url),
        daemon=True
    )
    thread.start()
    
    return jsonify({
        "status": "processing",
        "task_id": task_id,
        "status_url": f"/api/v1/status/{task_id}",
        "final_image_url": f"{config.BASE_IMAGE_URL}/{task_id}.jpg"
    }), 202

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
    
    task_id_from_filename = filename.replace('.jpg', '')
    status_data = task_manager.get_task_status(task_id_from_filename)
    
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
    
    file_path = status_data['final_path']
    
    # Verificar se arquivo existe
    if not os.path.exists(file_path):
        logger.error(f"Arquivo não encontrado no disco: {file_path}")
        task_manager.delete_task_status(task_id_from_filename)
        return jsonify({
            "error": "Arquivo não encontrado"
        }), 404
    
    logger.info(f"Servindo imagem: {filename}")
    
    @after_this_request
    def cleanup_after_serve(response):
        """Remove a imagem e limpa o status após servir"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Arquivo temporário removido: {file_path}")
            
            task_manager.delete_task_status(task_id_from_filename)
            logger.info(f"Status da tarefa removido: {task_id_from_filename}")
        except Exception as e:
            logger.error(f"Erro ao limpar arquivo/status {task_id_from_filename}: {e}")
        
        return response
    
    return send_from_directory(config.TEMP_IMAGES_DIR, filename, mimetype='image/jpeg')

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
