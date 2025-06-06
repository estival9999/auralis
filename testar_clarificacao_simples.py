#!/usr/bin/env python3
"""
Teste simplificado do sistema de clarificação
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import AURALISBackend

def testar_clarificacao():
    """Testa o sistema de clarificação integrado"""
    print("=== TESTE DO SISTEMA DE CLARIFICAÇÃO ===\n")
    
    # Inicializar backend
    backend = AURALISBackend()
    
    # Perguntas ambíguas que devem gerar clarificação
    perguntas_ambiguas = [
        "Me ajude",
        "Status",
        "Informações",
        "Resumo",
        "Novidades?",
        "O que você pode fazer?",
        "Preciso de ajuda"
    ]
    
    # Perguntas claras que devem ser processadas normalmente
    perguntas_claras = [
        "Qual foi o tema da última reunião?",
        "O que é compliance?",
        "Quem participou da reunião de ontem?"
    ]
    
    print("📌 TESTANDO PERGUNTAS AMBÍGUAS (devem solicitar clarificação):\n")
    
    for pergunta in perguntas_ambiguas:
        print(f"👤 Pergunta: '{pergunta}'")
        resposta = backend.buscar_informacao_reuniao(pergunta)
        print(f"🤖 Resposta:\n{resposta}\n")
        print("-" * 70 + "\n")
    
    print("\n📌 TESTANDO PERGUNTAS CLARAS (devem ser processadas normalmente):\n")
    
    for pergunta in perguntas_claras:
        print(f"👤 Pergunta: '{pergunta}'")
        resposta = backend.buscar_informacao_reuniao(pergunta)
        # Mostrar apenas os primeiros 200 caracteres para não poluir a saída
        resposta_truncada = resposta[:200] + "..." if len(resposta) > 200 else resposta
        print(f"🤖 Resposta: {resposta_truncada}\n")
        print("-" * 70 + "\n")
    
    print("✅ Teste concluído!")


if __name__ == "__main__":
    testar_clarificacao()