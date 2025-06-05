#!/usr/bin/env python3
"""
Script para corrigir embeddings com dimensões incorretas
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

def corrigir_embeddings():
    """Corrige embeddings com dimensões incorretas"""
    print("🔧 Corrigindo embeddings no Supabase...")
    print("-" * 60)
    
    # Conectar ao Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not supabase_url or not supabase_key or not openai_api_key:
        print("❌ Credenciais não encontradas no .env")
        return
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        openai_client = OpenAI(api_key=openai_api_key)
        
        # Buscar embeddings com problema
        print("\n📊 Buscando embeddings com problemas...")
        resultado = supabase.table('reunioes_embbed').select("*").execute()
        
        embeddings = resultado.data
        embeddings_corrigir = []
        
        for emb in embeddings:
            embedding = emb.get('embedding', [])
            if embedding and len(embedding) != 1536:
                embeddings_corrigir.append(emb)
        
        print(f"✅ Encontrados {len(embeddings_corrigir)} embeddings para corrigir")
        
        if embeddings_corrigir:
            print("\n🔄 Corrigindo embeddings...")
            
            for i, emb in enumerate(embeddings_corrigir):
                print(f"\n   Processando {i+1}/{len(embeddings_corrigir)}: {emb.get('arquivo_origem')}")
                
                try:
                    # Gerar novo embedding
                    texto = emb.get('chunk_texto', '')
                    if texto:
                        response = openai_client.embeddings.create(
                            model="text-embedding-ada-002",
                            input=texto
                        )
                        novo_embedding = response.data[0].embedding
                        
                        print(f"   ✅ Novo embedding gerado: {len(novo_embedding)} dimensões")
                        
                        # Atualizar no banco
                        supabase.table('reunioes_embbed').update({
                            'embedding': novo_embedding
                        }).eq('id', emb['id']).execute()
                        
                        print(f"   ✅ Atualizado no banco!")
                    else:
                        print(f"   ⚠️  Sem texto para gerar embedding")
                        
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
            
            print("\n\n✅ Correção concluída!")
            
            # Verificar novamente
            print("\n📊 Verificando correções...")
            resultado = supabase.table('reunioes_embbed').select("id, arquivo_origem, embedding").execute()
            
            corretos = 0
            incorretos = 0
            
            for emb in resultado.data:
                embedding = emb.get('embedding', [])
                if embedding and len(embedding) == 1536:
                    corretos += 1
                else:
                    incorretos += 1
            
            print(f"   ✅ Corretos: {corretos}")
            print(f"   ❌ Incorretos: {incorretos}")
            
        else:
            print("\n✅ Todos os embeddings estão corretos!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀 AURALIS - Corretor de Embeddings")
    print("=" * 60)
    
    resposta = input("\n⚠️  Este script irá reprocessar todos os embeddings incorretos. Continuar? (s/n): ")
    
    if resposta.lower() == 's':
        corrigir_embeddings()
    else:
        print("\n❌ Operação cancelada")

if __name__ == "__main__":
    main()