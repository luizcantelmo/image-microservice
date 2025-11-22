#!/usr/bin/env python3
"""
Script de desenvolvimento e testes
"""
import os
import sys
import requests
import json
import time
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:5001"

def print_section(title):
    """Imprime uma seção formatada"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_health_check():
    """Testa health check"""
    print_section("Test: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_process_image():
    """Testa processamento de imagem"""
    print_section("Test: Process Image")
    
    payload = {
        "products": [
            {
                "Referencia": "TEST-001",
                "DescricaoFinal": "Camiseta de Teste",
                "Preco": 99.90,
                "PrecoPromocional": 79.90,
                "PrecoPromocionalAVista": 75.90,
                "TamanhosDisponiveis": "P, M, G, GG",
                "NumeracaoUtilizada": "M",
                "Esgotado": False
            }
        ],
        "original_image_url": "https://via.placeholder.com/1200x800",
        "watermark_url": None
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/process-image", json=payload)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(json.dumps(data, indent=2))
        
        if response.status_code == 202:
            return data.get('task_id')
        return None
    except Exception as e:
        print(f"Erro: {e}")
        return None

def test_status_check(task_id, max_retries=30):
    """Testa consulta de status"""
    print_section(f"Test: Status Check (Task ID: {task_id})")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/api/v1/status/{task_id}")
            data = response.json()
            status = data.get('status')
            
            print(f"Attempt {attempt + 1}/{max_retries}: {status}")
            
            if status == "COMPLETED":
                print("\n✓ Imagem pronta para download!")
                print(json.dumps(data, indent=2))
                return True
            elif status == "FAILED":
                print("\n✗ Processamento falhou!")
                print(json.dumps(data, indent=2))
                return False
            
            time.sleep(2)
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(2)
    
    print(f"\n✗ Timeout após {max_retries} tentativas")
    return False

def test_download_image(task_id, output_file="test_output.jpg"):
    """Testa download da imagem"""
    print_section(f"Test: Download Image (Task ID: {task_id})")
    
    try:
        response = requests.get(f"{BASE_URL}/processed_images/{task_id}.jpg")
        
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(output_file)
            print(f"✓ Imagem salva: {output_file}")
            print(f"  Tamanho: {file_size} bytes")
            return True
        else:
            print(f"✗ Erro ao baixar imagem: {response.status_code}")
            print(response.json())
            return False
    except Exception as e:
        print(f"Erro: {e}")
        return False

def run_full_test():
    """Executa teste completo"""
    print("\n" + "="*60)
    print("  TESTE COMPLETO DO MICROSERVIÇO")
    print("="*60)
    
    # 1. Health Check
    if not test_health_check():
        print("\n✗ Servidor não respondeu ao health check")
        print(f"Certifique-se de que o servidor está rodando em {BASE_URL}")
        return
    
    # 2. Process Image
    task_id = test_process_image()
    if not task_id:
        print("\n✗ Falha ao enviar requisição de processamento")
        return
    
    # 3. Status Check
    if not test_status_check(task_id):
        print("\n✗ Imagem não foi processada com sucesso")
        return
    
    # 4. Download
    if not test_download_image(task_id):
        print("\n✗ Falha ao baixar imagem")
        return
    
    print("\n" + "="*60)
    print("  ✓ TESTE CONCLUÍDO COM SUCESSO!")
    print("="*60 + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        run_full_test()
    else:
        print("Uso:")
        print("  python dev_test.py --full    # Executar teste completo")
        print("\nExemplo:")
        print("  1. Inicie o servidor: python -m app.main")
        print("  2. Em outro terminal: python dev_test.py --full")
