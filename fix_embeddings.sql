-- Script para corrigir embeddings e criar função de busca semântica

-- 1. Criar extensão vector se não existir
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Alterar tipo da coluna embedding para vector(1536)
ALTER TABLE reunioes_embbed 
ALTER COLUMN embedding TYPE vector(1536) 
USING embedding::vector(1536);

-- 3. Criar índice para busca eficiente
CREATE INDEX IF NOT EXISTS reunioes_embbed_embedding_idx 
ON reunioes_embbed 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 4. Criar função de busca por similaridade
CREATE OR REPLACE FUNCTION buscar_chunks_similares(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    arquivo_origem text,
    data_reuniao date,
    chunk_numero int,
    chunk_texto text,
    metadados jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.arquivo_origem,
        r.data_reuniao,
        r.chunk_numero,
        r.chunk_texto,
        r.metadados,
        1 - (r.embedding <=> query_embedding) as similarity
    FROM reunioes_embbed r
    WHERE 1 - (r.embedding <=> query_embedding) > similarity_threshold
    ORDER BY r.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 5. Deletar registros com embeddings incorretos
DELETE FROM reunioes_embbed WHERE array_length(embedding::float[], 1) != 1536;

-- 6. Criar função alternativa que aceita array
CREATE OR REPLACE FUNCTION buscar_chunks_similares_array(
    query_embedding float[],
    similarity_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    arquivo_origem text,
    data_reuniao date,
    chunk_numero int,
    chunk_texto text,
    metadados jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.arquivo_origem,
        r.data_reuniao,
        r.chunk_numero,
        r.chunk_texto,
        r.metadados,
        1 - (r.embedding <=> query_embedding::vector(1536)) as similarity
    FROM reunioes_embbed r
    WHERE 1 - (r.embedding <=> query_embedding::vector(1536)) > similarity_threshold
    ORDER BY r.embedding <=> query_embedding::vector(1536)
    LIMIT match_count;
END;
$$;