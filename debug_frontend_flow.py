"""
Debug do fluxo Frontend -> Backend
"""

import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

print("=== DEBUG FLUXO FRONTEND -> BACKEND ===\n")

# 1. Testar o fluxo completo como o FRONT.py faz
try:
    from main import AURALISBackend, process_message_async
    print("✅ Importações do main.py OK")
except Exception as e:
    print(f"❌ Erro ao importar main.py: {e}")
    sys.exit(1)

# 2. Criar backend como no FRONT.py
try:
    backend = AURALISBackend()
    print("✅ Backend criado com sucesso")
except Exception as e:
    print(f"❌ Erro ao criar backend: {e}")
    print(f"   Detalhes: {str(e)}")
    sys.exit(1)

# 3. Testar busca direta
print("\n=== TESTE 1: Busca Direta (Síncrona) ===")
pergunta = "Quais foram as principais decisões tomadas?"
try:
    resposta = backend.buscar_informacao_reuniao(pergunta)
    print(f"✅ Busca executada com sucesso")
    print(f"\nResposta:")
    print(f"'{resposta[:200]}...'")
    
    # Verificar se é resposta padrão
    if "não encontrei" in resposta.lower() or "desculpe" in resposta.lower():
        print("\n⚠️  POSSÍVEL RESPOSTA PADRÃO DETECTADA!")
except Exception as e:
    print(f"❌ Erro na busca: {e}")
    import traceback
    traceback.print_exc()

# 4. Testar busca assíncrona (como o FRONT.py faz)
print("\n=== TESTE 2: Busca Assíncrona (Como no Frontend) ===")

import threading
import time

resposta_recebida = []
erro_recebido = []

def callback_sucesso(resposta):
    resposta_recebida.append(resposta)
    print(f"✅ Callback de sucesso chamado")

def callback_erro(erro):
    erro_recebido.append(erro)
    print(f"❌ Callback de erro chamado: {erro}")

try:
    process_message_async(
        backend,
        pergunta,
        callback_sucesso,
        callback_erro
    )
    
    # Aguardar resposta
    print("⏳ Aguardando resposta assíncrona...")
    tempo_max = 10  # segundos
    tempo_decorrido = 0
    
    while tempo_decorrido < tempo_max and not (resposta_recebida or erro_recebido):
        time.sleep(0.5)
        tempo_decorrido += 0.5
    
    if resposta_recebida:
        print(f"\nResposta assíncrona recebida:")
        print(f"'{resposta_recebida[0][:200]}...'")
    elif erro_recebido:
        print(f"\nErro recebido: {erro_recebido[0]}")
    else:
        print(f"\n⚠️  Timeout - nenhuma resposta em {tempo_max} segundos")
        
except Exception as e:
    print(f"❌ Erro no processamento assíncrono: {e}")

# 5. Verificar o assistente diretamente
print("\n=== TESTE 3: Assistente de Reuniões Direto ===")
try:
    assistente = backend.assistente_reunioes
    print(f"✅ Assistente acessível: {type(assistente).__name__}")
    
    # Verificar se o agente existe
    if hasattr(assistente, 'agente'):
        print(f"✅ Agente interno existe: {type(assistente.agente).__name__}")
    else:
        print("❌ Agente interno não encontrado!")
        
except Exception as e:
    print(f"❌ Erro ao acessar assistente: {e}")

# 6. Testar diferentes tipos de perguntas
print("\n=== TESTE 4: Diferentes Tipos de Perguntas ===")
perguntas_teste = [
    "Quem participou das reuniões?",
    "Qual o objetivo do projeto?", 
    "Quais problemas foram discutidos?",
    "teste123xyz"  # Pergunta sem sentido para ver resposta padrão
]

for pergunta in perguntas_teste:
    print(f"\nPergunta: '{pergunta}'")
    try:
        resposta = backend.buscar_informacao_reuniao(pergunta)
        print(f"Resposta (primeiros 150 chars): '{resposta[:150]}...'")
        
        # Detectar respostas padrão
        palavras_padrao = ["desculpe", "não encontrei", "erro", "ocorreu"]
        if any(palavra in resposta.lower() for palavra in palavras_padrao):
            print("   ⚠️  Possível resposta padrão!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

print("\n=== FIM DO DEBUG ===")