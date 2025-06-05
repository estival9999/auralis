"""
Debug detalhado da busca de chunks
"""

import os
from dotenv import load_dotenv
from src.agente_busca_reunioes import AgenteBuscaReunioes

load_dotenv()

print("=== DEBUG DETALHADO DA BUSCA ===\n")

# Criar agente
agente = AgenteBuscaReunioes()

# Testar perguntas que falharam
perguntas_problema = [
    "Quem participou das reuniões?",
    "Qual o objetivo do projeto?"
]

for pergunta in perguntas_problema:
    print(f"\n{'='*60}")
    print(f"PERGUNTA: '{pergunta}'")
    print('='*60)
    
    # 1. Gerar embedding
    print("\n1. GERANDO EMBEDDING DA PERGUNTA...")
    try:
        embedding = agente.gerar_embedding_pergunta(pergunta)
        print(f"✅ Embedding gerado: {len(embedding)} dimensões")
    except Exception as e:
        print(f"❌ Erro: {e}")
        continue
    
    # 2. Buscar chunks manualmente
    print("\n2. BUSCANDO CHUNKS...")
    try:
        chunks = agente.buscar_chunks_relevantes(embedding, num_resultados=5)
        print(f"✅ Chunks encontrados: {len(chunks)}")
        
        if chunks:
            print("\nCHUNKS RETORNADOS:")
            for i, chunk in enumerate(chunks):
                print(f"\n--- Chunk {i+1} ---")
                print(f"Arquivo: {chunk.get('arquivo_origem', 'N/A')}")
                print(f"Similaridade: {chunk.get('similarity', 0):.4f}")
                print(f"Texto: {chunk.get('chunk_texto', '')[:200]}...")
        else:
            print("⚠️  NENHUM CHUNK ENCONTRADO!")
            
            # Verificar threshold
            print("\n3. TESTANDO COM THRESHOLD MENOR...")
            # Tentar buscar com threshold mais baixo diretamente no Supabase
            from supabase import create_client
            supabase = create_client(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            )
            
            # Buscar com threshold 0.5 ao invés de 0.7
            resultado_baixo = supabase.rpc(
                'buscar_chunks_similares',
                {
                    'query_embedding': embedding,
                    'similarity_threshold': 0.5,  # Threshold mais baixo
                    'match_count': 5
                }
            ).execute()
            
            if resultado_baixo.data:
                print(f"✅ Com threshold 0.5, encontrou {len(resultado_baixo.data)} chunks!")
                print(f"   Maior similaridade: {resultado_baixo.data[0].get('similarity', 0):.4f}")
            else:
                print("❌ Mesmo com threshold 0.5, nenhum chunk encontrado")
                
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
        import traceback
        traceback.print_exc()

# Verificar conteúdo dos chunks no banco
print("\n\n=== VERIFICANDO CONTEÚDO DOS CHUNKS NO BANCO ===")
try:
    from supabase import create_client
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )
    
    # Pegar alguns chunks para ver o conteúdo
    chunks_exemplo = supabase.table('reunioes_embbed').select('chunk_texto').limit(3).execute()
    
    if chunks_exemplo.data:
        print(f"\nEXEMPLOS DE CHUNKS NO BANCO:")
        for i, chunk in enumerate(chunks_exemplo.data):
            print(f"\n--- Chunk Exemplo {i+1} ---")
            texto = chunk['chunk_texto'][:300]
            print(f"{texto}...")
            
            # Verificar se contém palavras-chave
            if any(palavra in texto.lower() for palavra in ['participou', 'participante', 'presente']):
                print("   ✅ Contém informações sobre participantes")
            if any(palavra in texto.lower() for palavra in ['objetivo', 'meta', 'propósito']):
                print("   ✅ Contém informações sobre objetivos")
                
except Exception as e:
    print(f"❌ Erro ao verificar chunks: {e}")