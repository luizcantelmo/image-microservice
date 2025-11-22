"""
Gerenciador de tarefas de processamento
Suporta armazenamento em memória, arquivo JSON ou Redis
"""
import json
import os
from datetime import datetime
from app import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Dicionário em memória (fallback se Redis não estiver disponível)
_tasks_in_memory = {}

# Arquivo para persistência
TASKS_FILE = os.path.join(os.path.dirname(__file__), '../../tasks_db.json')

def _load_tasks_from_file():
    """Carrega tarefas do arquivo JSON"""
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Erro ao carregar tarefas do arquivo: {e}")
    return {}

def _save_tasks_to_file(tasks):
    """Salva tarefas em arquivo JSON"""
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f)
    except Exception as e:
        logger.error(f"Erro ao salvar tarefas no arquivo: {e}")

class TaskManager:
    """Gerenciador de tarefas com suporte a Redis, arquivo e memória"""
    
    def __init__(self):
        self.redis_client = None
        self.use_redis = False
        self.use_file = True
        
        # Carregar tarefas do arquivo na inicialização
        global _tasks_in_memory
        _tasks_in_memory = _load_tasks_from_file()
        
        if config.USE_REDIS:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host=config.REDIS_HOST,
                    port=config.REDIS_PORT,
                    db=config.REDIS_DB,
                    password=config.REDIS_PASSWORD,
                    decode_responses=True
                )
                # Testa a conexão
                self.redis_client.ping()
                self.use_redis = True
                self.use_file = False
                logger.info("Conectado ao Redis com sucesso")
            except Exception as e:
                logger.warning(f"Falha ao conectar ao Redis: {e}. Usando arquivo/memória como fallback.")
                self.use_redis = False
    
    def get_task_status(self, task_id):
        """Obtém o status de uma tarefa"""
        try:
            if self.use_redis:
                data = self.redis_client.get(f"task:{task_id}")
                if data:
                    return json.loads(data)
            else:
                if task_id in _tasks_in_memory:
                    return _tasks_in_memory[task_id]
        except Exception as e:
            logger.error(f"Erro ao obter status da tarefa {task_id}: {e}")
        
        return {"status": "NOT_FOUND"}
    
    def update_task_status(self, task_id, status, final_path=None, error_message=None):
        """Atualiza o status de uma tarefa"""
        try:
            data = {
                "status": status,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "final_path": final_path,
                "error": error_message
            }
            
            if self.use_redis:
                # Armazena com TTL de 24 horas
                self.redis_client.setex(
                    f"task:{task_id}",
                    86400,  # 24 horas em segundos
                    json.dumps(data)
                )
            else:
                global _tasks_in_memory
                _tasks_in_memory[task_id] = data
                # Salvar em arquivo para persistência
                _save_tasks_to_file(_tasks_in_memory)
            
            logger.info(f"Status da tarefa {task_id} atualizado para: {status}")
        except Exception as e:
            logger.error(f"Erro ao atualizar status da tarefa {task_id}: {e}")
    
    def delete_task_status(self, task_id):
        """Deleta o status de uma tarefa"""
        try:
            if self.use_redis:
                self.redis_client.delete(f"task:{task_id}")
            else:
                global _tasks_in_memory
                if task_id in _tasks_in_memory:
                    del _tasks_in_memory[task_id]
                    # Salvar em arquivo
                    _save_tasks_to_file(_tasks_in_memory)
            
            logger.info(f"Status da tarefa {task_id} deletado")
        except Exception as e:
            logger.error(f"Erro ao deletar status da tarefa {task_id}: {e}")
    
    def cleanup_old_tasks(self, max_age_hours=24):
        """Remove tarefas antigas (apenas em memória)"""
        if not self.use_redis:
            try:
                current_time = datetime.now()
                tasks_to_delete = []
                
                for task_id, data in _tasks_in_memory.items():
                    task_time = datetime.fromisoformat(data.get('timestamp', ''))
                    age = (current_time - task_time).total_seconds() / 3600
                    
                    if age > max_age_hours:
                        tasks_to_delete.append(task_id)
                
                for task_id in tasks_to_delete:
                    del _tasks_in_memory[task_id]
                    logger.info(f"Tarefa antiga {task_id} removida durante limpeza")
                
                if tasks_to_delete:
                    logger.info(f"Limpeza concluída: {len(tasks_to_delete)} tarefas removidas")
            except Exception as e:
                logger.error(f"Erro na limpeza de tarefas antigas: {e}")
    
    def get_all_tasks(self):
        """Retorna todas as tarefas (para monitoramento)"""
        try:
            if self.use_redis:
                keys = self.redis_client.keys("task:*")
                tasks = {}
                for key in keys:
                    task_id = key.replace("task:", "")
                    tasks[task_id] = json.loads(self.redis_client.get(key))
                return tasks
            else:
                return _tasks_in_memory.copy()
        except Exception as e:
            logger.error(f"Erro ao obter todas as tarefas: {e}")
            return {}

# Instância global
task_manager = TaskManager()
