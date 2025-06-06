#!/usr/bin/env python3
"""
Script para testar o sistema de clarificação de perguntas ambíguas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import AURALISBackend
from src.clarificador_intencao import ClarificadorIntencao

def testar_clarificacao_direta():
    """Testa o clarificador diretamente"""
    print("=== TESTE DIRETO DO CLARIFICADOR ===\n")
    
    clarificador = ClarificadorIntencao()
    
    perguntas_teste = [
        # Perguntas ambíguas que devem solicitar clarificação
        "Me ajude",
        "Status",
        "Informações",
        "Resumo",
        "Novidades",
        "???",
        "",
        
        # Perguntas claras que NÃO devem solicitar clarificação
        "Qual foi o tema da última reunião?",
        "O que é compliance?",
        "Compare as duas últimas reuniões",
        "Liste os participantes da reunião de ontem",
        
        # Saudações
        "Oi",
        "Bom dia",
    ]
    
    for pergunta in perguntas_teste:
        print(f"Pergunta: '{pergunta}'")
        precisa, mensagem = clarificador.processar_pergunta(pergunta)
        
        if precisa:
            print("✅ PRECISA CLARIFICAÇÃO:")
            print(f"{mensagem}\n")
        else:
            print("❌ Pergunta clara - processaria normalmente\n")
        
        print("-" * 70 + "\n")


def testar_sistema_completo():
    """Testa o sistema completo com clarificação integrada"""
    print("\n=== TESTE DO SISTEMA COMPLETO ===\n")
    
    # Inicializar backend
    backend = AURALISBackend()
    
    # Perguntas para testar
    perguntas = [
        "Me ajude",
        "Status atual",
        "Preciso de informações",
        "O que aconteceu?",
        "Resumo geral",
        "Qual foi o tema da última reunião?",
        "Novidades?",
    ]
    
    print("Testando perguntas no sistema completo:\n")
    
    for pergunta in perguntas:
        print(f"👤 Pergunta: '{pergunta}'")
        resposta = backend.buscar_informacao_reuniao(pergunta)
        print(f"🤖 Resposta: {resposta}\n")
        print("-" * 70 + "\n")


def demonstracao_interativa():
    """Demonstração interativa do sistema"""
    print("\n=== DEMONSTRAÇÃO INTERATIVA ===\n")
    print("Digite suas perguntas (ou 'sair' para terminar):\n")
    
    backend = AURALISBackend()
    
    while True:
        pergunta = input("👤 Você: ").strip()
        
        if pergunta.lower() in ['sair', 'exit', 'quit']:
            print("Até logo!")
            break
        
        if not pergunta:
            continue
        
        resposta = backend.buscar_informacao_reuniao(pergunta)
        print(f"\n🤖 Assistente: {resposta}\n")


if __name__ == "__main__":
    print("TESTE DO SISTEMA DE CLARIFICAÇÃO DE PERGUNTAS AMBÍGUAS")
    print("=" * 70 + "\n")
    
    # Executar testes
    testar_clarificacao_direta()
    
    print("\n" + "=" * 70 + "\n")
    print("Deseja testar o sistema completo? (s/n): ", end="")
    
    resposta = input().strip().lower()
    
    if resposta == 's':
        testar_sistema_completo()
        
        print("\nDeseja testar interativamente? (s/n): ", end="")
        if input().strip().lower() == 's':
            demonstracao_interativa()
    
    print("\nTeste concluído!")