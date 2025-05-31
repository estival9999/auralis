-- PASSO 1: Criar tabelas principais
-- Execute no Supabase Dashboard > SQL Editor

-- Criar tabela login_user
CREATE TABLE IF NOT EXISTS login_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nome_completo TEXT,
    cpf TEXT,
    cargo TEXT,
    area TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);