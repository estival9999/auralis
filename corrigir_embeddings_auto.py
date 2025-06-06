#!/usr/bin/env python3
"""
Script automático para corrigir embeddings com dimensões incorretas
"""

import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configurar OpenAI
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Configurar Supabase
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("🔧 Corrigindo embeddings...")
print("-" * 60)

# Buscar todos os registros
resultado = supabase.table('reunioes_embbed').select("*").execute()
registros = resultado.data

total = len(registros)
corrigidos = 0
erros = 0

for i, registro in enumerate(registros):
    try:
        print(f"\r⏳ Processando {i+1}/{total}...", end='', flush=True)
        
        # Verificar embedding atual
        embedding_atual = registro.get('embedding', [])
        if len(embedding_atual) == 1536:
            print(f"\r✅ {i+1}/{total} - Já está correto", end='', flush=True)
            continue
        
        # Gerar novo embedding
        texto = registro.get('chunk_texto', '')
        if not texto:
            continue
        
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=texto
        )
        
        novo_embedding = response.data[0].embedding
        
        # Verificar dimensões
        if len(novo_embedding) != 1536:
            print(f"\n❌ Erro: embedding gerado com {len(novo_embedding)} dimensões!")
            continue
        
        # Atualizar no banco
        supabase.table('reunioes_embbed').update({
            'embedding': novo_embedding
        }).eq('id', registro['id']).execute()
        
        corrigidos += 1
        
    except Exception as e:
        print(f"\n❌ Erro ao processar {registro['id']}: {e}")
        erros += 1

print(f"\n\n✅ Embeddings corrigidos: {corrigidos}")
print(f"❌ Erros: {erros}")
print(f"📊 Taxa de sucesso: {(corrigidos/total)*100:.1f}%")

# Verificar resultado
print("\n🔍 Verificando resultado...")
resultado = supabase.table('reunioes_embbed').select("id, embedding").execute()
embeddings = resultado.data

corretos = sum(1 for e in embeddings if len(e.get('embedding', [])) == 1536)
incorretos = sum(1 for e in embeddings if len(e.get('embedding', [])) != 1536)

print(f"✅ Embeddings corretos: {corretos}")
print(f"❌ Embeddings incorretos: {incorretos}")

if incorretos == 0:
    print("\n🎉 Todos os embeddings foram corrigidos com sucesso!")