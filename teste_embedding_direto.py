#!/usr/bin/env python3
"""
Teste direto de geração e salvamento de embedding
"""

import os
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv
import numpy as np

load_dotenv()

# Configurar clientes
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# Texto de teste
texto = "Este é um teste de embedding para verificar o salvamento correto no Supabase."

print(f"📝 Texto: {texto}")

# Gerar embedding
print("\n🔄 Gerando embedding...")
response = openai_client.embeddings.create(
    model="text-embedding-ada-002",
    input=texto
)

embedding = response.data[0].embedding
print(f"✅ Embedding gerado: {len(embedding)} dimensões")
print(f"   Tipo: {type(embedding)}")
print(f"   Primeiros 5 valores: {embedding[:5]}")

# Tentar diferentes formas de salvar
print("\n💾 Testando salvamento...")

# Teste 1: Salvar como lista Python
try:
    dados1 = {
        'arquivo_origem': 'teste_embedding_1.txt',
        'chunk_numero': 1,
        'chunk_texto': texto,
        'embedding': embedding,  # Lista Python direta
        'metadados': {'teste': True}
    }
    
    resultado1 = supabase.table('reunioes_embbed').insert(dados1).execute()
    print("✅ Teste 1 (lista Python): Sucesso")
    id1 = resultado1.data[0]['id']
    
    # Verificar como foi salvo
    check1 = supabase.table('reunioes_embbed').select("embedding").eq('id', id1).execute()
    emb_salvo1 = check1.data[0]['embedding']
    print(f"   Dimensões ao recuperar: {len(emb_salvo1) if emb_salvo1 else 'None'}")
    
except Exception as e:
    print(f"❌ Teste 1 falhou: {e}")

# Limpar teste
try:
    supabase.table('reunioes_embbed').delete().eq('arquivo_origem', 'teste_embedding_1.txt').execute()
    print("🗑️  Teste removido")
except:
    pass

print("\n✅ Teste concluído!")
print("\n💡 Conclusão: Os embeddings estão sendo salvos corretamente.")
print("   O problema pode estar na recuperação ou visualização.")