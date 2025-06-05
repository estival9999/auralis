"""
Sistema de busca local por similaridade
Implementa busca semântica sem depender de funções RPC do Supabase
"""

import numpy as np
from typing import List, Dict, Tuple
from supabase import Client

class BuscaSemanticaLocal:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self._cache_chunks = None
        self._cache_embeddings = None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade de cosseno entre dois vetores"""
        # Converter para numpy arrays
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        # Calcular similaridade
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
            
        return float(dot_product / (norm_v1 * norm_v2))
    
    def _load_all_chunks(self) -> Tuple[List[Dict], List[List[float]]]:
        """Carrega todos os chunks e embeddings do banco"""
        if self._cache_chunks is not None:
            return self._cache_chunks, self._cache_embeddings
            
        print("Carregando chunks do banco de dados...")
        result = self.supabase.table('reunioes_embbed').select('*').execute()
        
        chunks = []
        embeddings = []
        
        for item in result.data:
            # Verificar se embedding existe e tem tamanho correto
            embedding = item.get('embedding', [])
            
            # Se embedding for string JSON, converter
            if isinstance(embedding, str):
                import json
                try:
                    embedding = json.loads(embedding)
                except:
                    continue
                    
            # Verificar tamanho - esperamos 1536 para ada-002
            if len(embedding) == 1536:
                chunks.append(item)
                embeddings.append(embedding)
            else:
                print(f"⚠️  Chunk {item.get('id')} tem embedding com tamanho {len(embedding)}")
        
        print(f"✅ Carregados {len(chunks)} chunks válidos")
        
        # Cachear para próximas buscas
        self._cache_chunks = chunks
        self._cache_embeddings = embeddings
        
        return chunks, embeddings
    
    def buscar_similares(self, 
                        query_embedding: List[float], 
                        threshold: float = 0.7,
                        limit: int = 5) -> List[Dict]:
        """Busca chunks similares usando cálculo local"""
        
        # Verificar tamanho do embedding de consulta
        if len(query_embedding) != 1536:
            print(f"⚠️  Query embedding tem tamanho {len(query_embedding)}, esperado 1536")
            return []
        
        # Carregar todos os chunks
        chunks, embeddings = self._load_all_chunks()
        
        if not chunks:
            print("Nenhum chunk válido encontrado no banco")
            return []
        
        # Calcular similaridades
        similarities = []
        for i, chunk_embedding in enumerate(embeddings):
            sim = self._cosine_similarity(query_embedding, chunk_embedding)
            if sim > threshold:
                similarities.append((i, sim))
        
        # Ordenar por similaridade decrescente
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar top N resultados
        results = []
        for idx, sim in similarities[:limit]:
            chunk = chunks[idx].copy()
            chunk['similarity'] = sim
            results.append(chunk)
        
        print(f"Encontrados {len(results)} chunks com similaridade > {threshold}")
        
        return results
    
    def limpar_cache(self):
        """Limpa o cache de chunks"""
        self._cache_chunks = None
        self._cache_embeddings = None