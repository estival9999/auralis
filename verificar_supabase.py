#!/usr/bin/env python3
"""
Verifica configuração do Supabase e testa busca de chunks
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv()

def verificar_supabase():
    print("=== VERIFICAÇÃO DO SUPABASE ===\n")
    
    # Conectar ao Supabase
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    supabase = create_client(url, key)
    
    # 1. Verificar se há dados na tabela
    print("1. Verificando dados na tabela reunioes_embbed...")
    try:
        result = supabase.table('reunioes_embbed').select('*').limit(5).execute()
        print(f"   ✅ Encontrados {len(result.data)} registros")
        
        if result.data:
            print("\n   Exemplo de registro:")
            primeiro = result.data[0]
            print(f"   - ID: {primeiro.get('id')}")
            print(f"   - Arquivo: {primeiro.get('arquivo_origem')}")
            print(f"   - Chunk: {primeiro.get('chunk_numero')}")
            print(f"   - Texto (50 chars): {primeiro.get('chunk_texto', '')[:50]}...")
            print(f"   - Embedding length: {len(primeiro.get('embedding', []))}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 2. Verificar estrutura da tabela
    print("\n2. Verificando estrutura da tabela...")
    try:
        # Pegar um registro para ver os campos
        result = supabase.table('reunioes_embbed').select('*').limit(1).execute()
        if result.data:
            campos = list(result.data[0].keys())
            print(f"   Campos encontrados: {', '.join(campos)}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 3. Tentar busca manual de similaridade
    print("\n3. Testando busca manual...")
    try:
        # Buscar todos os chunks
        result = supabase.table('reunioes_embbed').select('*').execute()
        print(f"   Total de chunks no banco: {len(result.data)}")
        
        # Verificar se embeddings estão sendo salvos corretamente
        if result.data:
            chunk = result.data[0]
            embedding = chunk.get('embedding')
            if embedding:
                print(f"   ✅ Embeddings estão sendo salvos (dimensão: {len(embedding)})")
            else:
                print(f"   ❌ Embeddings não encontrados!")
                
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 4. Verificar se existe a função RPC
    print("\n4. Verificando função RPC 'buscar_chunks_similares'...")
    print("   ⚠️  Não é possível listar funções RPC via API")
    print("   Você precisa verificar no dashboard do Supabase se a função existe")
    
    print("\n" + "="*60)
    print("DIAGNÓSTICO:")
    print("="*60)
    print("\n⚠️  A função RPC 'buscar_chunks_similares' provavelmente não existe no banco")
    print("   Isso explica por que a busca semântica não funciona")
    print("\n📝 SOLUÇÃO: Criar a função no Supabase ou implementar busca local")

if __name__ == "__main__":
    verificar_supabase()