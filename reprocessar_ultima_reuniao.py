#!/usr/bin/env python3
"""
Script para reprocessar a última reunião com embeddings corretos
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
from dotenv import load_dotenv
from src.embeddings_processor import ProcessadorEmbeddings

load_dotenv()

# Conectar ao Supabase
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("🔍 Buscando última reunião...")

# Buscar última reunião
resultado = supabase.table('reunioes_embbed').select(
    'arquivo_origem'
).order('created_at', desc=True).limit(1).execute()

if resultado.data:
    arquivo = resultado.data[0]['arquivo_origem']
    print(f"✅ Última reunião: {arquivo}")
    
    # Deletar registros antigos dessa reunião
    print(f"\n🗑️  Removendo embeddings antigos...")
    delete_result = supabase.table('reunioes_embbed').delete().eq('arquivo_origem', arquivo).execute()
    print(f"✅ Removidos {len(delete_result.data)} registros")
    
    # Verificar se o arquivo existe em audio_temp
    arquivo_path = f"audio_temp/{arquivo.replace('reuniao_texto_', 'reuniao_').replace('.txt', '_transcricao.txt')}"
    
    if not os.path.exists(arquivo_path):
        # Tentar arquivo direto
        arquivo_path = arquivo
        
    if os.path.exists(arquivo_path):
        print(f"\n📄 Reprocessando arquivo: {arquivo_path}")
        
        # Reprocessar
        processador = ProcessadorEmbeddings()
        sucesso = processador.processar_arquivo(arquivo_path)
        
        if sucesso:
            print("✅ Arquivo reprocessado com sucesso!")
            
            # Verificar novo embedding
            novo_resultado = supabase.table('reunioes_embbed').select(
                'id, embedding'
            ).eq('arquivo_origem', os.path.basename(arquivo_path)).limit(1).execute()
            
            if novo_resultado.data:
                emb = novo_resultado.data[0]['embedding']
                print(f"\n🔍 Verificação do novo embedding:")
                print(f"   Tipo: {type(emb)}")
                if isinstance(emb, list):
                    print(f"   Dimensões: {len(emb)}")
                    print(f"   ✅ Embedding salvo corretamente!")
        else:
            print("❌ Erro ao reprocessar arquivo")
    else:
        print(f"❌ Arquivo não encontrado: {arquivo_path}")
else:
    print("❌ Nenhuma reunião encontrada")