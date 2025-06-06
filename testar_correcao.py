#!/usr/bin/env python3
"""
Script para testar correção do problema de respostas aleatórias
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Carregar variáveis de ambiente
load_dotenv()

from src.agente_busca_melhorado import AgenteBuscaMelhorado

def testar_correcao():
    """Testa as correções para o problema de respostas aleatórias"""
    
    print("🧪 Testando correções do sistema AURALIS\n")
    print("=" * 60)
    
    # Inicializar agente
    agente = AgenteBuscaMelhorado()
    
    # Casos problemáticos reportados
    testes = [
        "iae blz",
        "mas eu nem te perguntei isso",
        "?",
        "wtf",
        "ue",
        "pq?",
        "quando vai chover em São Paulo?",  # Pergunta totalmente fora do contexto
        "quem é o presidente do Brasil?",    # Outra pergunta sem relação
    ]
    
    for pergunta in testes:
        print(f"\n👤 Pergunta: {pergunta}")
        resposta = agente.processar_pergunta(pergunta)
        print(f"🤖 Resposta: {resposta}")
        
        # Verificar se a resposta é apropriada
        respostas_esperadas = [
            "Olá! Como posso ajudar?",
            "Não entendi",
            "Pode elaborar",
            "Não encontrei informações",
            "Sua pergunta está um pouco vaga",
            "Com certeza!",
            "Claro!",
            "Sim!"
        ]
        
        resposta_apropriada = any(esperada in resposta for esperada in respostas_esperadas)
        
        if resposta_apropriada:
            print("✅ Resposta apropriada")
        else:
            print("❌ PROBLEMA: Resposta não relacionada à pergunta!")
        
        print("-" * 60)

if __name__ == "__main__":
    testar_correcao()