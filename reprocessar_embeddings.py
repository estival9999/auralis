#!/usr/bin/env python3
"""
Reprocessa os embeddings com tamanho correto
"""

import os
from dotenv import load_dotenv
from src.embeddings_processor import ProcessadorEmbeddings
from supabase import create_client

load_dotenv()

def reprocessar_embeddings():
    print("=== REPROCESSANDO EMBEDDINGS ===\n")
    
    # Conectar ao Supabase
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase = create_client(url, key)
    
    # 1. Limpar tabela de embeddings incorretos
    print("1. Limpando embeddings antigos...")
    try:
        result = supabase.table('reunioes_embbed').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print("   ✅ Tabela limpa")
    except Exception as e:
        print(f"   ❌ Erro ao limpar: {e}")
    
    # 2. Reprocessar arquivos
    print("\n2. Reprocessando arquivos de reunião...")
    processador = ProcessadorEmbeddings()
    
    # Processar pasta de teste
    pasta_teste = "/home/mateus/Área de trabalho/DOZERO/teste_reuniao"
    processador.processar_pasta(pasta_teste)
    
    # 3. Verificar resultados
    print("\n3. Verificando resultados...")
    try:
        result = supabase.table('reunioes_embbed').select('id, chunk_numero, embedding').execute()
        
        print(f"   Total de chunks: {len(result.data)}")
        
        if result.data:
            # Verificar tamanho do primeiro embedding
            primeiro = result.data[0]
            embedding = primeiro.get('embedding', [])
            
            if isinstance(embedding, str):
                import json
                embedding = json.loads(embedding)
                
            print(f"   Tamanho do embedding: {len(embedding)}")
            
            if len(embedding) == 1536:
                print("   ✅ Embeddings com tamanho correto!")
            else:
                print(f"   ❌ Embeddings ainda com tamanho incorreto: {len(embedding)}")
                
    except Exception as e:
        print(f"   ❌ Erro ao verificar: {e}")
    
    print("\n✅ Reprocessamento concluído!")

if __name__ == "__main__":
    reprocessar_embeddings()