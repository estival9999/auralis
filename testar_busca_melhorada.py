#!/usr/bin/env python3
"""
Script para testar o sistema de busca melhorado
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agente_busca_melhorado import AgenteBuscaMelhorado
from dotenv import load_dotenv

load_dotenv()

def testar_sistema():
    print("🧪 Testando Sistema de Busca Melhorado")
    print("=" * 60)
    
    # Criar agente
    agente = AgenteBuscaMelhorado()
    
    # Testar busca da última reunião
    print("\n📋 Teste 1: Buscar última reunião")
    print("-" * 40)
    
    perguntas_teste = [
        "qual foi a última reunião?",
        "qual o título da última reunião?",
        "qual data da última reunião?",
        "qual data da última reunião e título dela?",
        "quem participou da última reunião?",
        "sobre o que foi a última reunião?"
    ]
    
    for pergunta in perguntas_teste:
        print(f"\n👤 Pergunta: {pergunta}")
        resposta = agente.processar_pergunta(pergunta)
        print(f"🤖 Resposta: {resposta}")
    
    # Testar busca por conteúdo
    print("\n\n📋 Teste 2: Buscar por conteúdo")
    print("-" * 40)
    
    perguntas_conteudo = [
        "o que foi discutido sobre crédito?",
        "quais foram as decisões tomadas?",
        "quem é responsável pelo quê?"
    ]
    
    for pergunta in perguntas_conteudo:
        print(f"\n👤 Pergunta: {pergunta}")
        resposta = agente.processar_pergunta(pergunta)
        print(f"🤖 Resposta: {resposta}")
    
    # Testar busca direta da última reunião
    print("\n\n📋 Teste 3: Busca direta no banco")
    print("-" * 40)
    
    reuniao_recente = agente.buscar_reuniao_mais_recente()
    if reuniao_recente:
        print(f"✅ Última reunião encontrada:")
        print(f"   - Arquivo: {reuniao_recente.get('arquivo_origem')}")
        print(f"   - Título: {reuniao_recente.get('titulo')}")
        print(f"   - Data: {reuniao_recente.get('data_reuniao')}")
        print(f"   - Hora: {reuniao_recente.get('hora_inicio')}")
        print(f"   - Responsável: {reuniao_recente.get('responsavel')}")
    else:
        print("❌ Nenhuma reunião encontrada")

if __name__ == "__main__":
    testar_sistema()