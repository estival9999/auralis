#!/usr/bin/env python3
"""
Script de debug para testar o agente de busca de reuniões
"""

import sys
from src.agente_busca_reunioes import AgenteBuscaReunioes

def testar_agente():
    print("=== TESTE DO AGENTE DE BUSCA ===\n")
    
    try:
        # Inicializar agente
        print("1. Inicializando agente...")
        agente = AgenteBuscaReunioes()
        print("✅ Agente inicializado com sucesso\n")
        
        # Perguntas de teste
        perguntas = [
            "Quais foram as principais decisões tomadas?",
            "Quem participou das reuniões?",
            "Quais problemas foram discutidos?",
            "O que foi decidido sobre o sistema de cache?",
            "Fale sobre o projeto mencionado nas reuniões",
            "Resuma o conteúdo das reuniões disponíveis"
        ]
        
        for i, pergunta in enumerate(perguntas, 1):
            print(f"\n{'='*60}")
            print(f"PERGUNTA {i}: {pergunta}")
            print(f"{'='*60}")
            
            try:
                # Processar pergunta
                resposta = agente.processar_pergunta(pergunta)
                
                print(f"\nRESPOSTA:")
                print("-" * 60)
                print(resposta)
                print("-" * 60)
                
                # Verificar se é resposta genérica
                respostas_genericas = [
                    "não encontrei informações",
                    "não há informações",
                    "desculpe",
                    "não foi possível"
                ]
                
                eh_generica = any(gen in resposta.lower() for gen in respostas_genericas)
                
                if eh_generica:
                    print("⚠️  ALERTA: Resposta parece ser genérica!")
                else:
                    print("✅ Resposta parece usar contexto das reuniões")
                    
            except Exception as e:
                print(f"❌ Erro ao processar pergunta: {e}")
                import traceback
                traceback.print_exc()
        
        # Teste direto de busca
        print(f"\n\n{'='*60}")
        print("TESTE DIRETO DE BUSCA DE CHUNKS")
        print(f"{'='*60}")
        
        # Gerar embedding de teste
        embedding_teste = agente.gerar_embedding_pergunta("reunião sobre decisões importantes")
        
        # Buscar chunks
        chunks = agente.buscar_chunks_relevantes(embedding_teste, 5)
        
        print(f"\nChunks encontrados: {len(chunks)}")
        for i, chunk in enumerate(chunks, 1):
            print(f"\n--- Chunk {i} ---")
            print(f"Arquivo: {chunk.get('arquivo_origem', 'N/A')}")
            print(f"Similaridade: {chunk.get('similarity', 'N/A')}")
            print(f"Texto (primeiros 200 chars): {chunk.get('chunk_texto', '')[:200]}...")
            
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_agente()