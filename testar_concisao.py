#!/usr/bin/env python3
"""
Script para testar a concisão das respostas do sistema AURALIS
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Carregar variáveis de ambiente
load_dotenv()

from src.agente_busca_melhorado import AgenteBuscaMelhorado

def testar_concisao():
    """Testa diferentes tipos de perguntas e analisa a concisão das respostas"""
    
    print("🧪 Iniciando testes de concisão do AURALIS\n")
    print("=" * 60)
    
    # Inicializar agente
    agente = AgenteBuscaMelhorado()
    
    # Casos de teste
    testes = [
        # (pergunta, tipo_esperado)
        ("oi", "saudação"),
        ("pode me ajudar?", "ajuda vaga"),
        ("qual o prazo para atualizar cadastro de cliente auto risco", "pergunta específica"),
        ("quando foi a última reunião?", "pergunta simples"),
        ("o que é cooperativa?", "pergunta conceitual"),
        ("existe política de crédito?", "pergunta sim/não"),
        ("qual telefone da cooperativa?", "dado específico"),
        ("me fale sobre a reunião de planejamento", "pergunta sobre reunião"),
    ]
    
    for pergunta, tipo in testes:
        print(f"\n📝 TESTE: {tipo.upper()}")
        print(f"👤 Pergunta: {pergunta}")
        
        # Processar pergunta
        resposta = agente.processar_pergunta(pergunta)
        
        # Análise da resposta
        palavras = len(resposta.split())
        linhas = len(resposta.split('\n'))
        caracteres = len(resposta)
        
        print(f"🤖 Resposta: {resposta}")
        print(f"📊 Métricas:")
        print(f"   - Palavras: {palavras}")
        print(f"   - Linhas: {linhas}")
        print(f"   - Caracteres: {caracteres}")
        
        # Verificar se há frases indesejadas
        frases_proibidas = [
            "Você perguntou",
            "Considerações importantes",
            "Se desejar",
            "Posso ajudar com mais",
            "relevância",
            "%"
        ]
        
        problemas = []
        for frase in frases_proibidas:
            if frase.lower() in resposta.lower():
                problemas.append(f"Contém '{frase}'")
        
        if problemas:
            print(f"⚠️  Problemas encontrados: {', '.join(problemas)}")
        else:
            print("✅ Resposta concisa e limpa!")
        
        print("-" * 60)

if __name__ == "__main__":
    testar_concisao()