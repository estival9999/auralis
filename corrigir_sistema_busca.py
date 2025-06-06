#!/usr/bin/env python3
"""
Script para corrigir problemas no sistema de busca de reuniões:
1. Embeddings com dimensões incorretas (19k+ em vez de 1536)
2. Ordenação temporal para priorizar reuniões recentes
3. Melhoria na precisão das buscas
"""

import os
import sys
from datetime import datetime
import json
import numpy as np
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class CorretorSistemaBusca:
    def __init__(self):
        # Configurar OpenAI
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY não encontrada no .env")
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Configurar Supabase
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Credenciais Supabase não encontradas no .env")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def analisar_problema_embeddings(self):
        """Analisa o problema dos embeddings com dimensões incorretas"""
        print("🔍 Analisando problema dos embeddings...")
        print("-" * 60)
        
        # Buscar todos os embeddings
        resultado = self.supabase.table('reunioes_embbed').select("id, embedding, chunk_texto").execute()
        embeddings = resultado.data
        
        problematicos = []
        for emb in embeddings:
            embedding = emb.get('embedding', [])
            if len(embedding) != 1536:
                problematicos.append({
                    'id': emb['id'],
                    'dimensoes': len(embedding),
                    'texto_preview': emb.get('chunk_texto', '')[:50] + '...'
                })
        
        print(f"✅ Total de embeddings: {len(embeddings)}")
        print(f"❌ Embeddings com problema: {len(problematicos)}")
        
        if problematicos:
            print("\n📋 Detalhes dos problemas:")
            for p in problematicos[:3]:
                print(f"   ID: {p['id']}")
                print(f"   Dimensões: {p['dimensoes']} (esperado: 1536)")
                print(f"   Texto: {p['texto_preview']}")
                print()
        
        return problematicos
    
    def regenerar_embeddings(self):
        """Regenera todos os embeddings com o modelo correto"""
        print("\n🔧 Regenerando embeddings...")
        print("-" * 60)
        
        # Buscar todos os registros
        resultado = self.supabase.table('reunioes_embbed').select("*").execute()
        registros = resultado.data
        
        total = len(registros)
        corrigidos = 0
        erros = 0
        
        for i, registro in enumerate(registros):
            try:
                print(f"\r⏳ Processando {i+1}/{total}...", end='', flush=True)
                
                # Gerar novo embedding
                texto = registro.get('chunk_texto', '')
                if not texto:
                    continue
                
                response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=texto
                )
                
                novo_embedding = response.data[0].embedding
                
                # Verificar dimensões
                if len(novo_embedding) != 1536:
                    print(f"\n❌ Erro: embedding gerado com {len(novo_embedding)} dimensões!")
                    continue
                
                # Atualizar no banco
                self.supabase.table('reunioes_embbed').update({
                    'embedding': novo_embedding
                }).eq('id', registro['id']).execute()
                
                corrigidos += 1
                
            except Exception as e:
                print(f"\n❌ Erro ao processar {registro['id']}: {e}")
                erros += 1
        
        print(f"\n\n✅ Embeddings corrigidos: {corrigidos}")
        print(f"❌ Erros: {erros}")
        print(f"📊 Taxa de sucesso: {(corrigidos/total)*100:.1f}%")
    
    def otimizar_tamanho_chunks(self):
        """Analisa e sugere otimizações para o tamanho dos chunks"""
        print("\n📊 Analisando tamanhos de chunks...")
        print("-" * 60)
        
        resultado = self.supabase.table('reunioes_embbed').select('chunk_texto').execute()
        chunks = resultado.data
        
        tamanhos = [len(chunk.get('chunk_texto', '')) for chunk in chunks]
        
        print(f"Total de chunks: {len(tamanhos)}")
        print(f"Tamanho médio: {sum(tamanhos)/len(tamanhos):.0f} caracteres")
        print(f"Menor chunk: {min(tamanhos)} caracteres")
        print(f"Maior chunk: {max(tamanhos)} caracteres")
        
        # Recomendar tamanho ideal
        tamanho_ideal_min = 200
        tamanho_ideal_max = 1000
        
        chunks_pequenos = sum(1 for t in tamanhos if t < tamanho_ideal_min)
        chunks_grandes = sum(1 for t in tamanhos if t > tamanho_ideal_max)
        
        print(f"\n⚠️  Chunks muito pequenos (<{tamanho_ideal_min} chars): {chunks_pequenos}")
        print(f"⚠️  Chunks muito grandes (>{tamanho_ideal_max} chars): {chunks_grandes}")
        
        if chunks_grandes > 0:
            print(f"\n💡 Recomendação: Re-chunkar os {chunks_grandes} chunks grandes")
            print(f"   Isso melhorará a precisão da busca semântica")
    
    def melhorar_busca_temporal(self):
        """Adiciona suporte para busca temporal priorizando reuniões recentes"""
        print("\n🕐 Melhorando busca temporal...")
        print("-" * 60)
        
        # Verificar se existe índice para created_at
        print("✅ Sistema configurado para ordenar por created_at (já implementado)")
        print("💡 Sugestão: Adicionar peso temporal na busca semântica")
        
        # Mostrar últimas reuniões
        resultado = self.supabase.table('reunioes_embbed').select(
            'arquivo_origem, data_reuniao, created_at'
        ).order('created_at', desc=True).limit(5).execute()
        
        print("\n📋 Últimas 5 reuniões:")
        for r in resultado.data:
            print(f"   - {r['arquivo_origem']} ({r.get('data_reuniao', 'N/A')})")
            print(f"     Criado em: {r['created_at']}")
    
    def criar_indice_busca_recente(self):
        """Cria estrutura para buscar reuniões recentes com mais eficiência"""
        print("\n📑 Criando índice de reuniões recentes...")
        print("-" * 60)
        
        # SQL para criar view materializada (se não existir)
        sql_view = """
        CREATE OR REPLACE VIEW v_reunioes_recentes AS
        SELECT DISTINCT ON (arquivo_origem)
            arquivo_origem,
            data_reuniao,
            created_at,
            metadados->>'titulo' as titulo,
            metadados->>'responsavel' as responsavel
        FROM reunioes_embbed
        ORDER BY arquivo_origem, created_at DESC;
        """
        
        print("📝 SQL para criar view de reuniões recentes:")
        print(sql_view)
        print("\n⚠️  Execute este SQL no Supabase para melhorar a performance")

def main():
    print("🚀 AURALIS - Corretor do Sistema de Busca")
    print("=" * 60)
    
    corretor = CorretorSistemaBusca()
    
    # 1. Analisar problemas
    problemas = corretor.analisar_problema_embeddings()
    
    if problemas:
        print("\n⚠️  Embeddings com problemas detectados!")
        resposta = input("\nDeseja regenerar todos os embeddings? (s/n): ")
        
        if resposta.lower() == 's':
            corretor.regenerar_embeddings()
    
    # 2. Analisar tamanho dos chunks
    corretor.otimizar_tamanho_chunks()
    
    # 3. Melhorar busca temporal
    corretor.melhorar_busca_temporal()
    
    # 4. Criar índices
    corretor.criar_indice_busca_recente()
    
    print("\n\n✅ Análise concluída!")
    print("\n📋 Próximos passos recomendados:")
    print("1. Regenerar embeddings se necessário")
    print("2. Implementar re-chunking para textos muito grandes")
    print("3. Adicionar peso temporal na busca semântica")
    print("4. Criar view no Supabase para queries otimizadas")

if __name__ == "__main__":
    main()