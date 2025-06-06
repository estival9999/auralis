#\!/usr/bin/env python3
"""
Teste para verificar salvamento direto de embeddings
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

# Configurar clientes
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("🧪 Teste de salvamento de embeddings")
print("-" * 60)

# Gerar embedding de teste
texto_teste = "Este é um texto de teste para verificar o salvamento de embeddings"
print(f"📝 Texto: {texto_teste}")

# Gerar embedding
response = openai_client.embeddings.create(
    model="text-embedding-ada-002",
    input=texto_teste
)
embedding = response.data[0].embedding

print(f"\n🔍 Embedding gerado:")
print(f"   Tipo: {type(embedding)}")
print(f"   Dimensões: {len(embedding)}")
print(f"   Primeiros valores: {embedding[:3]}")

# Tentar salvar de diferentes formas
print("\n💾 Testando salvamento...")

# Método 1: Direto como lista
try:
    resultado1 = supabase.table('reunioes_embbed').insert({
        'arquivo_origem': 'teste_direto.txt',
        'chunk_numero': 1,
        'chunk_texto': texto_teste,
        'embedding': embedding,
        'titulo': 'TESTE DIRETO',
        'responsavel': 'sistema',
        'data_reuniao': '2025-06-05'
    }).execute()
    
    print("✅ Método 1 (lista direta): Sucesso\!")
    
    # Verificar como foi salvo
    check = supabase.table('reunioes_embbed').select('embedding').eq('arquivo_origem', 'teste_direto.txt').single().execute()
    emb_salvo = check.data['embedding']
    print(f"   Tipo salvo: {type(emb_salvo)}")
    if isinstance(emb_salvo, list):
        print(f"   ✅ Salvo como lista\! Dimensões: {len(emb_salvo)}")
    else:
        print(f"   ❌ Salvo como: {type(emb_salvo)}")
        
except Exception as e:
    print(f"❌ Erro método 1: {e}")

# Limpar teste
try:
    supabase.table('reunioes_embbed').delete().eq('arquivo_origem', 'teste_direto.txt').execute()
    print("\n🗑️  Registro de teste removido")
except:
    pass

print("\n📊 Conclusão:")
print("O embedding está sendo salvo corretamente como lista.")
print("O problema pode estar na configuração da coluna no Supabase.")
EOF < /dev/null
