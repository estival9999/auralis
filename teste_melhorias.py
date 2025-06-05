"""
Teste das melhorias implementadas no agente
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=== TESTE DAS MELHORIAS NO AGENTE ===\n")

# Importar e testar
from src.agente_busca_reunioes import AgenteBuscaReunioes, IntegracaoAssistenteReunioes

# Criar agente
agente = AgenteBuscaReunioes()
integracao = IntegracaoAssistenteReunioes()

# Testar perguntas que estavam falhando
perguntas_teste = [
    "Quem participou das reuniões?",
    "Qual o objetivo do projeto?",
    "Quais foram as principais decisões?",
    "Que problemas foram identificados?",
    "O que foi discutido sobre crédito?"
]

print("Testando com o agente melhorado...\n")

for i, pergunta in enumerate(perguntas_teste):
    print(f"\n{'='*60}")
    print(f"PERGUNTA {i+1}: {pergunta}")
    print('='*60)
    
    try:
        # Usar a integração como o FRONT.py faz
        resposta = integracao.processar_mensagem_usuario(pergunta)
        
        print("\nRESPOSTA:")
        print(resposta[:500] + "..." if len(resposta) > 500 else resposta)
        
        # Analisar a resposta
        palavras_genericas = ["desculpe", "não encontrei", "não há informações"]
        eh_generica = any(palavra in resposta.lower() for palavra in palavras_genericas)
        
        if eh_generica:
            print("\n⚠️  Resposta ainda parece genérica")
        else:
            print("\n✅ Resposta com conteúdo específico!")
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

print("\n\n=== FIM DO TESTE ===")