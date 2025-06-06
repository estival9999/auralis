-- Script para verificar e corrigir formato dos embeddings
-- Execute este script no Supabase SQL Editor

-- 1. Verificar o tipo atual da coluna
SELECT 
    column_name,
    data_type,
    udt_name
FROM information_schema.columns 
WHERE table_name = 'reunioes_embbed' 
AND column_name = 'embedding';

-- 2. Verificar se há registros e como estão armazenados
SELECT 
    id,
    arquivo_origem,
    titulo,
    pg_typeof(embedding) as tipo_embedding,
    CASE 
        WHEN embedding IS NULL THEN 'NULL'
        WHEN pg_typeof(embedding)::text = 'vector' THEN 'VECTOR'
        ELSE 'OUTRO'
    END as formato
FROM reunioes_embbed
ORDER BY created_at DESC
LIMIT 5;

-- 3. Se necessário, adicionar extensão vector (provavelmente já está ativa)
CREATE EXTENSION IF NOT EXISTS vector;

-- 4. Função para converter string JSON para vector
-- Esta função pode ser útil se os embeddings estão sendo salvos como texto JSON
CREATE OR REPLACE FUNCTION json_to_vector(json_text TEXT)
RETURNS vector(1536)
LANGUAGE plpgsql
AS $$
DECLARE
    float_array FLOAT[];
BEGIN
    -- Converter JSON array string para array PostgreSQL
    SELECT array_agg(value::FLOAT)
    INTO float_array
    FROM json_array_elements_text(json_text::json);
    
    -- Converter array para vector
    RETURN float_array::vector(1536);
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Erro ao converter: %', SQLERRM;
        RETURN NULL;
END;
$$;

-- 5. Comentários para debug
COMMENT ON FUNCTION json_to_vector IS 'Converte string JSON de array para tipo vector(1536) do PostgreSQL';