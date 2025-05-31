-- PASSO 3: Criar tabela historico_reunioes
-- Execute no Supabase Dashboard > SQL Editor

CREATE TABLE IF NOT EXISTS historico_reunioes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo TEXT NOT NULL,
    data_reuniao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    responsavel TEXT,
    area TEXT,
    participantes TEXT[],
    duracao INTEGER DEFAULT 0,
    transcricao_completa TEXT,
    resumo_executivo TEXT,
    decisoes JSONB DEFAULT '[]'::jsonb,
    acoes JSONB DEFAULT '[]'::jsonb,
    pendencias JSONB DEFAULT '[]'::jsonb,
    insights JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);