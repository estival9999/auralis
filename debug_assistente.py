"""
Script de debug para rastrear problema do assistente de IA
"""

import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

print("=== DEBUG ASSISTENTE IA ===\n")

# 1. Testar importações
try:
    from src.agente_busca_reunioes import AgenteBuscaReunioes
    print("✅ Importação do AgenteBuscaReunioes OK")
except Exception as e:
    print(f"❌ Erro ao importar AgenteBuscaReunioes: {e}")
    sys.exit(1)

# 2. Criar instância do agente
try:
    agente = AgenteBuscaReunioes()
    print("✅ Criação do agente OK")
except Exception as e:
    print(f"❌ Erro ao criar agente: {e}")
    sys.exit(1)

# 3. Testar geração de embedding
print("\n=== TESTE 1: Geração de Embedding ===")
pergunta_teste = "Quais foram as principais decisões tomadas?"
try:
    embedding = agente.gerar_embedding_pergunta(pergunta_teste)
    print(f"✅ Embedding gerado com sucesso")
    print(f"   Tamanho do embedding: {len(embedding)}")
    print(f"   Primeiros valores: {embedding[:5]}")
except Exception as e:
    print(f"❌ Erro ao gerar embedding: {e}")
    print(f"   Tipo do erro: {type(e).__name__}")

# 4. Testar busca de chunks
print("\n=== TESTE 2: Busca de Chunks Relevantes ===")
try:
    # Verificar se temos embeddings no banco
    from supabase import create_client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase = create_client(supabase_url, supabase_key)
    
    # Contar registros na tabela
    result = supabase.table('reunioes_embbed').select('count', count='exact').execute()
    total_registros = result.count
    print(f"✅ Total de registros na tabela reunioes_embbed: {total_registros}")
    
    if total_registros > 0:
        # Pegar um registro de exemplo
        exemplo = supabase.table('reunioes_embbed').select('arquivo_origem, chunk_numero, data_reuniao').limit(1).execute()
        if exemplo.data:
            print(f"   Exemplo de registro: {exemplo.data[0]}")
    
except Exception as e:
    print(f"❌ Erro ao verificar registros: {e}")

# 5. Testar busca semântica
print("\n=== TESTE 3: Busca Semântica ===")
try:
    if embedding:
        chunks = agente.buscar_chunks_relevantes(embedding, num_resultados=3)
        print(f"✅ Busca executada")
        print(f"   Chunks encontrados: {len(chunks)}")
        
        if chunks:
            print("\n   Chunks retornados:")
            for i, chunk in enumerate(chunks):
                print(f"\n   Chunk {i+1}:")
                print(f"   - Arquivo: {chunk.get('arquivo_origem', 'N/A')}")
                print(f"   - Similaridade: {chunk.get('similarity', 'N/A')}")
                print(f"   - Texto (primeiros 100 chars): {chunk.get('chunk_texto', '')[:100]}...")
        else:
            print("   ⚠️  Nenhum chunk encontrado!")
            
            # Verificar se a função SQL existe
            print("\n   Verificando função SQL 'buscar_chunks_similares'...")
            try:
                # Tentar chamar com dados fake para ver se existe
                test_result = supabase.rpc(
                    'buscar_chunks_similares',
                    {
                        'query_embedding': [0.0] * 1536,  # Embedding fake
                        'similarity_threshold': 0.0,
                        'match_count': 1
                    }
                ).execute()
                print("   ✅ Função SQL existe e foi executada")
            except Exception as sql_error:
                print(f"   ❌ Erro ao executar função SQL: {sql_error}")
                print("   💡 A função SQL pode não estar criada no Supabase!")
                
except Exception as e:
    print(f"❌ Erro na busca semântica: {e}")
    print(f"   Detalhes: {str(e)}")

# 6. Testar processamento completo
print("\n=== TESTE 4: Processamento Completo da Pergunta ===")
try:
    resposta = agente.processar_pergunta(pergunta_teste)
    print(f"✅ Processamento completo OK")
    print(f"\nResposta gerada:")
    print(f"'{resposta}'")
    
    # Verificar se é uma resposta padrão
    if "não encontrei informações" in resposta.lower():
        print("\n⚠️  ATENÇÃO: Resposta padrão detectada!")
        print("   Possíveis causas:")
        print("   1. Não há embeddings no banco de dados")
        print("   2. A função SQL de busca não está funcionando")
        print("   3. Os embeddings não estão sendo comparados corretamente")
    
except Exception as e:
    print(f"❌ Erro no processamento: {e}")
    print(f"   Stack trace completo:")
    import traceback
    traceback.print_exc()

# 7. Verificar conexão com OpenAI
print("\n=== TESTE 5: Conexão com OpenAI ===")
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Teste simples
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Diga apenas 'OK'"}],
        max_tokens=10
    )
    
    resposta_openai = response.choices[0].message.content
    print(f"✅ OpenAI respondeu: '{resposta_openai}'")
    
except Exception as e:
    print(f"❌ Erro ao conectar com OpenAI: {e}")

print("\n=== FIM DO DEBUG ===")