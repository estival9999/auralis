-- PASSO 2: Criar tabela base_conhecimento
-- Execute no Supabase Dashboard > SQL Editor

CREATE TABLE IF NOT EXISTS base_conhecimento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo_arquivo TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    categoria TEXT,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);