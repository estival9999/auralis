-- SQL para atualizar estrutura da tabela de embeddings
-- Este script adiciona novas colunas e cria função para reconstruir reuniões

-- 1. Adicionar novas colunas para metadados completos
ALTER TABLE reunioes_embbed 
ADD COLUMN IF NOT EXISTS responsavel TEXT,
ADD COLUMN IF NOT EXISTS hora_inicio TIME,
ADD COLUMN IF NOT EXISTS titulo TEXT,
ADD COLUMN IF NOT EXISTS observacoes TEXT;

-- 2. Adicionar coluna para embeddings em JSONB (temporária para migração)
ALTER TABLE reunioes_embbed 
ADD COLUMN IF NOT EXISTS embedding_jsonb JSONB;

-- 3. Criar índice para ordem dos chunks
CREATE INDEX IF NOT EXISTS idx_reunioes_chunk_order 
ON reunioes_embbed (arquivo_origem, chunk_numero);

-- 4. Função para reconstruir reunião completa a partir dos chunks
CREATE OR REPLACE FUNCTION reconstruir_reuniao_completa(
    p_arquivo_origem TEXT
)
RETURNS TABLE (
    titulo TEXT,
    responsavel TEXT,
    data_reuniao DATE,
    hora_inicio TIME,
    observacoes TEXT,
    conteudo_completo TEXT,
    total_chunks INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_cabecalho RECORD;
    v_conteudo TEXT := '';
    v_chunk_count INTEGER := 0;
BEGIN
    -- Buscar metadados do primeiro chunk (contém o cabeçalho)
    SELECT 
        r.titulo,
        r.responsavel,
        r.data_reuniao,
        r.hora_inicio,
        r.observacoes
    INTO v_cabecalho
    FROM reunioes_embbed r
    WHERE r.arquivo_origem = p_arquivo_origem
    ORDER BY r.chunk_numero
    LIMIT 1;
    
    -- Se não encontrou, retornar vazio
    IF NOT FOUND THEN
        RETURN;
    END IF;
    
    -- Concatenar todos os chunks em ordem
    SELECT 
        string_agg(chunk_texto, E'\n' ORDER BY chunk_numero),
        COUNT(*)
    INTO v_conteudo, v_chunk_count
    FROM reunioes_embbed
    WHERE arquivo_origem = p_arquivo_origem;
    
    -- Retornar resultado
    RETURN QUERY
    SELECT 
        v_cabecalho.titulo,
        v_cabecalho.responsavel,
        v_cabecalho.data_reuniao,
        v_cabecalho.hora_inicio,
        v_cabecalho.observacoes,
        v_conteudo,
        v_chunk_count;
END;
$$;

-- 5. Função para buscar reuniões por responsável
CREATE OR REPLACE FUNCTION buscar_reunioes_por_responsavel(
    p_responsavel TEXT
)
RETURNS TABLE (
    arquivo_origem TEXT,
    titulo TEXT,
    data_reuniao DATE,
    hora_inicio TIME,
    total_chunks INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        r.arquivo_origem,
        r.titulo,
        r.data_reuniao,
        r.hora_inicio,
        COUNT(*) OVER (PARTITION BY r.arquivo_origem) as total_chunks
    FROM reunioes_embbed r
    WHERE r.responsavel = p_responsavel
    ORDER BY r.data_reuniao DESC, r.hora_inicio DESC;
END;
$$;

-- 6. Função melhorada para busca semântica com JSONB
CREATE OR REPLACE FUNCTION buscar_chunks_similares_jsonb(
    query_embedding JSONB,
    similarity_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    chunk_texto TEXT,
    arquivo_origem TEXT,
    titulo TEXT,
    responsavel TEXT,
    data_reuniao DATE,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
DECLARE
    query_array FLOAT[];
BEGIN
    -- Converter JSONB para array de float
    SELECT array_agg(value::FLOAT)
    INTO query_array
    FROM jsonb_array_elements_text(query_embedding);
    
    -- Buscar chunks similares usando cálculo manual de similaridade
    RETURN QUERY
    WITH chunk_similarities AS (
        SELECT 
            r.id,
            r.chunk_texto,
            r.arquivo_origem,
            r.titulo,
            r.responsavel,
            r.data_reuniao,
            -- Cálculo de similaridade de cosseno
            (
                SELECT SUM(a * b) / (SQRT(SUM(a * a)) * SQRT(SUM(b * b)))
                FROM (
                    SELECT 
                        unnest(query_array) as a,
                        unnest(array_agg(value::FLOAT)) as b
                    FROM jsonb_array_elements_text(r.embedding_jsonb)
                ) as vectors
            ) as similarity
        FROM reunioes_embbed r
        WHERE r.embedding_jsonb IS NOT NULL
    )
    SELECT * FROM chunk_similarities
    WHERE similarity > similarity_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- 7. View para listar todas as reuniões únicas
CREATE OR REPLACE VIEW v_reunioes_unicas AS
SELECT DISTINCT ON (arquivo_origem)
    arquivo_origem,
    titulo,
    responsavel,
    data_reuniao,
    hora_inicio,
    observacoes,
    created_at
FROM reunioes_embbed
ORDER BY arquivo_origem, chunk_numero;

-- 8. Comentários para documentação
COMMENT ON FUNCTION reconstruir_reuniao_completa IS 'Reconstrói o texto completo de uma reunião a partir de seus chunks';
COMMENT ON FUNCTION buscar_reunioes_por_responsavel IS 'Lista todas as reuniões de um responsável específico';
COMMENT ON FUNCTION buscar_chunks_similares_jsonb IS 'Busca semântica usando embeddings armazenados como JSONB';
COMMENT ON VIEW v_reunioes_unicas IS 'Lista todas as reuniões únicas (sem duplicação por chunks)';