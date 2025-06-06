-- Criação da extensão vector se ainda não existir
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabela principal para armazenar chunks da base de conhecimento
CREATE TABLE IF NOT EXISTS base_conhecimento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Conteúdo e embedding
    conteudo TEXT NOT NULL,
    embedding vector(1536), -- Dimensão padrão do OpenAI text-embedding-ada-002
    
    -- Metadados do chunk
    chunk_index INTEGER NOT NULL, -- Posição do chunk no documento original
    chunk_size INTEGER NOT NULL, -- Tamanho do chunk em caracteres
    
    -- Informações do documento
    documento_origem TEXT NOT NULL, -- Nome do arquivo original
    tipo_documento TEXT NOT NULL, -- manual, estatuto, procedimento, etc.
    categoria TEXT, -- Categoria específica do documento
    tags TEXT[], -- Array de tags para facilitar busca
    
    -- Metadados adicionais
    versao_documento TEXT DEFAULT '1.0',
    hash_documento TEXT, -- Hash do documento completo para controle de versão
    
    -- Timestamps
    data_processamento TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_atualizacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Controle
    ativo BOOLEAN DEFAULT true,
    
    -- Índices para metadados estruturados
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Índices para otimizar performance
CREATE INDEX idx_base_conhecimento_embedding ON base_conhecimento 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_base_conhecimento_tipo_documento ON base_conhecimento(tipo_documento);
CREATE INDEX idx_base_conhecimento_categoria ON base_conhecimento(categoria);
CREATE INDEX idx_base_conhecimento_tags ON base_conhecimento USING GIN(tags);
CREATE INDEX idx_base_conhecimento_documento_origem ON base_conhecimento(documento_origem);
CREATE INDEX idx_base_conhecimento_ativo ON base_conhecimento(ativo);
CREATE INDEX idx_base_conhecimento_metadata ON base_conhecimento USING GIN(metadata);

-- Função para busca semântica por similaridade
CREATE OR REPLACE FUNCTION buscar_conhecimento_similar(
    query_embedding vector(1536),
    limite INTEGER DEFAULT 10,
    tipo_doc TEXT DEFAULT NULL,
    categoria_filtro TEXT DEFAULT NULL,
    tags_filtro TEXT[] DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    conteudo TEXT,
    tipo_documento TEXT,
    categoria TEXT,
    tags TEXT[],
    documento_origem TEXT,
    similaridade FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bc.id,
        bc.conteudo,
        bc.tipo_documento,
        bc.categoria,
        bc.tags,
        bc.documento_origem,
        1 - (bc.embedding <=> query_embedding) AS similaridade,
        bc.metadata
    FROM base_conhecimento bc
    WHERE 
        bc.ativo = true
        AND (tipo_doc IS NULL OR bc.tipo_documento = tipo_doc)
        AND (categoria_filtro IS NULL OR bc.categoria = categoria_filtro)
        AND (tags_filtro IS NULL OR bc.tags && tags_filtro)
    ORDER BY bc.embedding <=> query_embedding
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- Função para obter contexto completo de um documento
CREATE OR REPLACE FUNCTION obter_contexto_documento(
    doc_origem TEXT,
    chunk_central INTEGER,
    chunks_antes INTEGER DEFAULT 2,
    chunks_depois INTEGER DEFAULT 2
)
RETURNS TABLE (
    conteudo TEXT,
    chunk_index INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bc.conteudo,
        bc.chunk_index
    FROM base_conhecimento bc
    WHERE 
        bc.documento_origem = doc_origem
        AND bc.ativo = true
        AND bc.chunk_index BETWEEN (chunk_central - chunks_antes) AND (chunk_central + chunks_depois)
    ORDER BY bc.chunk_index;
END;
$$ LANGUAGE plpgsql;

-- Tabela para controle de versões de documentos
CREATE TABLE IF NOT EXISTS base_conhecimento_versoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_origem TEXT NOT NULL,
    versao TEXT NOT NULL,
    hash_documento TEXT NOT NULL,
    data_upload TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    usuario_upload TEXT,
    notas_versao TEXT,
    ativo BOOLEAN DEFAULT true,
    UNIQUE(documento_origem, versao)
);

-- Trigger para atualizar data_atualizacao
CREATE OR REPLACE FUNCTION atualizar_data_atualizacao()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_atualizacao = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_atualizar_data_base_conhecimento
BEFORE UPDATE ON base_conhecimento
FOR EACH ROW
EXECUTE FUNCTION atualizar_data_atualizacao();

-- View para estatísticas da base de conhecimento
CREATE OR REPLACE VIEW estatisticas_base_conhecimento AS
SELECT 
    tipo_documento,
    COUNT(DISTINCT documento_origem) as total_documentos,
    COUNT(*) as total_chunks,
    AVG(chunk_size) as tamanho_medio_chunk,
    MAX(data_processamento) as ultimo_processamento
FROM base_conhecimento
WHERE ativo = true
GROUP BY tipo_documento;

-- Comentários explicativos
COMMENT ON TABLE base_conhecimento IS 'Tabela principal para armazenar chunks de documentos da base de conhecimento com embeddings para busca semântica';
COMMENT ON COLUMN base_conhecimento.embedding IS 'Vetor de embedding gerado pelo OpenAI para busca semântica';
COMMENT ON COLUMN base_conhecimento.chunk_index IS 'Índice sequencial do chunk dentro do documento original';
COMMENT ON COLUMN base_conhecimento.tipo_documento IS 'Tipo do documento: manual, estatuto, procedimento, politica, etc.';
COMMENT ON COLUMN base_conhecimento.tags IS 'Tags para categorização e busca adicional';
COMMENT ON COLUMN base_conhecimento.metadata IS 'Metadados adicionais em formato JSON para extensibilidade';