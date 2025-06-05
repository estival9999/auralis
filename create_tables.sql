-- Tabela para armazenar embeddings das reuniões
CREATE TABLE IF NOT EXISTS reunioes_embbed (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    arquivo_origem TEXT NOT NULL,
    data_reuniao DATE,
    chunk_numero INTEGER NOT NULL,
    chunk_texto TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 usa 1536 dimensões
    metadados JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice para busca por similaridade
CREATE INDEX IF NOT EXISTS reunioes_embbed_embedding_idx ON reunioes_embbed 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Tabela de usuários para login
CREATE TABLE IF NOT EXISTS login_user (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    cargo TEXT,
    area TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Função para buscar chunks similares
CREATE OR REPLACE FUNCTION buscar_chunks_similares(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    chunk_texto TEXT,
    arquivo_origem TEXT,
    data_reuniao DATE,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.chunk_texto,
        r.arquivo_origem,
        r.data_reuniao,
        1 - (r.embedding <=> query_embedding) as similarity
    FROM reunioes_embbed r
    WHERE 1 - (r.embedding <=> query_embedding) > similarity_threshold
    ORDER BY r.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_reunioes_embbed_updated_at BEFORE UPDATE ON reunioes_embbed
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_login_user_updated_at BEFORE UPDATE ON login_user
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();