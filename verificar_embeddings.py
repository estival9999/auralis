#!/usr/bin/env python3
"""
Script para verificar embeddings salvos no Supabase
"""

import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

def verificar_embeddings():
    """Verifica embeddings salvos no Supabase"""
    print("🔍 Verificando embeddings no Supabase...")
    print("-" * 60)
    
    # Conectar ao Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Credenciais Supabase não encontradas no .env")
        return
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Buscar todos os embeddings
        print("\n📊 Buscando embeddings...")
        resultado = supabase.table('reunioes_embbed').select("*").order('created_at', desc=True).execute()
        
        embeddings = resultado.data
        print(f"\n✅ Total de embeddings encontrados: {len(embeddings)}")
        
        if embeddings:
            print("\n📋 Últimos 5 embeddings:")
            print("-" * 60)
            
            for i, emb in enumerate(embeddings[:5]):
                print(f"\n🔹 Embedding {i+1}:")
                print(f"   ID: {emb.get('id')}")
                print(f"   Arquivo: {emb.get('arquivo_origem', 'N/A')}")
                print(f"   Chunk: {emb.get('chunk_numero', 'N/A')}")
                print(f"   Data reunião: {emb.get('data_reuniao', 'N/A')}")
                print(f"   Criado em: {emb.get('created_at', 'N/A')}")
                
                # Mostrar início do texto
                texto = emb.get('chunk_texto', '')
                if texto:
                    preview = texto[:100] + "..." if len(texto) > 100 else texto
                    print(f"   Texto: {preview}")
                
                # Verificar embedding
                embedding = emb.get('embedding', [])
                if embedding:
                    print(f"   Embedding: {len(embedding)} dimensões")
                else:
                    print(f"   ⚠️  Embedding vazio!")
                
                # Metadados
                metadados = emb.get('metadados', {})
                if metadados:
                    print(f"   Metadados: {json.dumps(metadados, ensure_ascii=False)[:100]}...")
            
            # Estatísticas por arquivo
            print("\n\n📈 Estatísticas por arquivo:")
            print("-" * 60)
            
            arquivos = {}
            for emb in embeddings:
                arquivo = emb.get('arquivo_origem', 'Desconhecido')
                if arquivo not in arquivos:
                    arquivos[arquivo] = 0
                arquivos[arquivo] += 1
            
            for arquivo, count in sorted(arquivos.items(), key=lambda x: x[1], reverse=True):
                print(f"   {arquivo}: {count} chunks")
            
            # Verificar embeddings mais recentes (últimas 24h)
            print("\n\n🕐 Embeddings das últimas 24 horas:")
            print("-" * 60)
            
            hoje = datetime.now()
            count_24h = 0
            
            for emb in embeddings:
                created_at = emb.get('created_at', '')
                if created_at:
                    try:
                        # Parse da data
                        data_criacao = datetime.fromisoformat(created_at.replace('Z', '+00:00').replace('+00:00', ''))
                        diff = hoje - data_criacao
                        
                        if diff.days < 1:
                            count_24h += 1
                    except:
                        pass
            
            print(f"   Total: {count_24h} embeddings")
            
            # Verificar integridade
            print("\n\n🔧 Verificação de integridade:")
            print("-" * 60)
            
            embeddings_vazios = 0
            embeddings_invalidos = 0
            embeddings_corretos = 0
            
            for emb in embeddings:
                embedding = emb.get('embedding', [])
                if not embedding:
                    embeddings_vazios += 1
                elif len(embedding) != 1536:  # Ada-002 tem 1536 dimensões
                    embeddings_invalidos += 1
                    print(f"   ⚠️  Embedding com {len(embedding)} dimensões: {emb.get('arquivo_origem')}")
                else:
                    embeddings_corretos += 1
            
            print(f"   ✅ Corretos (1536 dims): {embeddings_corretos}")
            print(f"   ❌ Vazios: {embeddings_vazios}")
            print(f"   ⚠️  Tamanho incorreto: {embeddings_invalidos}")
            
        else:
            print("\n⚠️  Nenhum embedding encontrado no banco de dados")
        
        # Testar busca específica do último arquivo de áudio
        print("\n\n🎤 Verificando embeddings de áudio:")
        print("-" * 60)
        
        audio_embeddings = [emb for emb in embeddings if 'reuniao_texto_' in emb.get('arquivo_origem', '')]
        
        if audio_embeddings:
            print(f"   ✅ Encontrados {len(audio_embeddings)} embeddings de transcrições de áudio")
            
            # Mostrar o mais recente
            mais_recente = audio_embeddings[0]
            print(f"\n   Mais recente:")
            print(f"   - Arquivo: {mais_recente.get('arquivo_origem')}")
            print(f"   - Chunks: {mais_recente.get('chunk_numero')}")
            
            # Extrair informações dos metadados
            metadados = mais_recente.get('metadados', {})
            if metadados:
                print(f"   - Título: {metadados.get('titulo', 'N/A')}")
                print(f"   - Data: {metadados.get('data_reuniao', 'N/A')}")
                print(f"   - Participantes: {', '.join(metadados.get('participantes', []))}")
        else:
            print("   ⚠️  Nenhum embedding de áudio encontrado")
            
    except Exception as e:
        print(f"\n❌ Erro ao conectar com Supabase: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀 AURALIS - Verificador de Embeddings")
    print("=" * 60)
    
    verificar_embeddings()
    
    print("\n\n✅ Verificação concluída!")

if __name__ == "__main__":
    main()