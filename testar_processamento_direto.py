#!/usr/bin/env python3
"""
Script para testar processamento direto de transcrição
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embeddings_processor import ProcessadorEmbeddings
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

# Configurar Supabase
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("🧪 Teste de Processamento Direto")
print("=" * 60)

# Arquivo de transcrição
arquivo_transcricao = "audio_temp/reuniao_20250605_213344_transcricao.txt"

# Ler conteúdo da transcrição
print(f"\n📄 Lendo arquivo: {arquivo_transcricao}")
with open(arquivo_transcricao, 'r', encoding='utf-8') as f:
    conteudo = f.read()

print(f"📝 Conteúdo (primeiros 200 chars):")
print(conteudo[:200] + "...")

# Criar arquivo temporário com cabeçalho completo
arquivo_temp = "teste_processamento_temp.txt"
print(f"\n✍️  Criando arquivo temporário com cabeçalho...")

cabecalho = f"""Título: TESTE EMBEDDINGS
Responsável: sistema_teste
Data: 05/06/2025
Hora: 21:33
Observações: Teste de processamento direto

"""

with open(arquivo_temp, 'w', encoding='utf-8') as f:
    f.write(cabecalho + conteudo)

# Processar arquivo
print(f"\n🔧 Processando arquivo...")
processador = ProcessadorEmbeddings()

try:
    # Deletar registros antigos de teste
    supabase.table('reunioes_embbed').delete().eq('responsavel', 'sistema_teste').execute()
    
    # Processar
    sucesso = processador.processar_arquivo(arquivo_temp)
    
    if sucesso:
        print("✅ Arquivo processado com sucesso!")
        
        # Verificar como foi salvo
        print("\n🔍 Verificando embedding salvo...")
        resultado = supabase.table('reunioes_embbed').select('*').eq('responsavel', 'sistema_teste').execute()
        
        if resultado.data:
            registro = resultado.data[0]
            print(f"\n📊 Análise do registro:")
            print(f"   ID: {registro['id']}")
            print(f"   Título: {registro['titulo']}")
            print(f"   Chunks: {len(resultado.data)}")
            
            # Analisar embedding
            embedding = registro.get('embedding')
            print(f"\n🎯 Análise do embedding:")
            print(f"   Tipo no Python: {type(embedding)}")
            
            if isinstance(embedding, str):
                try:
                    # Tentar parsear como JSON
                    embedding_array = json.loads(embedding)
                    print(f"   ✅ É um JSON string válido")
                    print(f"   Dimensões após parse: {len(embedding_array)}")
                    print(f"   Tipo após parse: {type(embedding_array)}")
                    print(f"   Primeiros 3 valores: {embedding_array[:3]}")
                    
                    # Verificar se todos são floats
                    all_floats = all(isinstance(x, (int, float)) for x in embedding_array)
                    print(f"   Todos são números: {'✅ Sim' if all_floats else '❌ Não'}")
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ Erro ao parsear JSON: {e}")
            elif isinstance(embedding, list):
                print(f"   ✅ Já é uma lista!")
                print(f"   Dimensões: {len(embedding)}")
            else:
                print(f"   ❓ Tipo inesperado: {type(embedding)}")
        
        # Testar busca
        print("\n🔎 Testando busca semântica...")
        from src.agente_busca_melhorado import AgenteBuscaMelhorado
        
        agente = AgenteBuscaMelhorado()
        
        # Modificar temporariamente o método de busca para aceitar JSON string
        original_buscar = agente.buscar_chunks_relevantes
        
        def buscar_adaptado(pergunta, num_resultados=5):
            try:
                # Buscar todos os embeddings
                resultado = agente.supabase.table('reunioes_embbed').select('*').execute()
                
                if not resultado.data:
                    return []
                
                # Gerar embedding da pergunta
                embedding_pergunta = agente.gerar_embedding_pergunta(pergunta)
                
                # Calcular similaridades
                resultados_com_score = []
                for chunk in resultado.data:
                    try:
                        # Obter embedding
                        embedding_chunk = chunk.get('embedding', [])
                        
                        # Se for string, parsear
                        if isinstance(embedding_chunk, str):
                            embedding_chunk = json.loads(embedding_chunk)
                        
                        # Verificar dimensões
                        if not embedding_chunk or len(embedding_chunk) != 1536:
                            continue
                        
                        # Calcular similaridade
                        import numpy as np
                        emb1 = np.array(embedding_pergunta)
                        emb2 = np.array(embedding_chunk)
                        similaridade = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                        
                        chunk['similarity'] = float(similaridade)
                        resultados_com_score.append(chunk)
                        
                    except Exception as e:
                        print(f"   Erro ao processar chunk {chunk.get('id')}: {e}")
                        continue
                
                # Ordenar por similaridade
                resultados_com_score.sort(key=lambda x: x['similarity'], reverse=True)
                
                return resultados_com_score[:num_resultados]
                
            except Exception as e:
                print(f"Erro na busca: {e}")
                return []
        
        # Substituir temporariamente
        agente.buscar_chunks_relevantes = buscar_adaptado
        
        # Testar
        pergunta = "quem é responsável por fraudes?"
        print(f"\n👤 Pergunta: {pergunta}")
        resposta = agente.processar_pergunta(pergunta)
        print(f"🤖 Resposta: {resposta}")
        
    else:
        print("❌ Erro ao processar arquivo")
        
finally:
    # Limpar
    if os.path.exists(arquivo_temp):
        os.remove(arquivo_temp)
        print(f"\n🗑️  Arquivo temporário removido")
    
    # Limpar registros de teste
    supabase.table('reunioes_embbed').delete().eq('responsavel', 'sistema_teste').execute()
    print("🗑️  Registros de teste removidos")

print("\n✅ Teste concluído!")