-- SQL para configurar banco de dados AURALIS
-- Execute este script no Supabase Dashboard > SQL Editor

-- 1. Criar tabela login_user
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

-- 2. Criar tabela base_conhecimento
CREATE TABLE IF NOT EXISTS base_conhecimento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo_arquivo TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    categoria TEXT,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Criar tabela historico_reunioes
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

-- 4. Inserir usuários de teste
INSERT INTO login_user (username, password, nome_completo, cargo, area) VALUES 
('admin', 'admin123', 'Administrador', 'Administrador', 'TI'),
('joao.silva', 'admin123', 'João Silva', 'Gerente de Projetos', 'Desenvolvimento'),
('maria.santos', 'admin123', 'Maria Santos', 'Analista de Negócios', 'Comercial'),
('pedro.costa', 'admin123', 'Pedro Costa', 'Desenvolvedor Senior', 'Desenvolvimento');

-- 5. Inserir dados de exemplo na base_conhecimento
INSERT INTO base_conhecimento (titulo_arquivo, conteudo, categoria, tags) VALUES 
('Política de Home Office', 
'Política de Trabalho Remoto

1. Elegibilidade
- Funcionários com mais de 6 meses na empresa
- Aprovação do gestor direto
- Atividades compatíveis com trabalho remoto

2. Horários
- Manter horário comercial padrão
- Disponibilidade para reuniões
- Comunicação prévia de ausências

3. Equipamentos
- Notebook fornecido pela empresa
- Acesso VPN obrigatório
- Responsabilidade pela segurança

4. Produtividade
- Metas mantidas ou superadas
- Relatórios semanais
- Avaliação trimestral',
'politica', 
ARRAY['home office', 'trabalho remoto', 'rh', 'política']);

-- 6. Inserir dados de exemplo no historico_reunioes
INSERT INTO historico_reunioes (
    titulo, responsavel, area, participantes, duracao, 
    transcricao_completa, resumo_executivo, decisoes, acoes, pendencias, insights
) VALUES (
    'Alinhamento de Projeto Alpha',
    'João Silva',
    'Desenvolvimento',
    ARRAY['João Silva', 'Maria Santos', 'Pedro Costa'],
    45,
    'João: Boa tarde pessoal, vamos começar nossa reunião sobre o Projeto Alpha.
Maria: Oi João, estou aqui. Podemos começar.
Pedro: Oi pessoal, pronto para discutir os próximos passos.

João: Primeiro ponto da pauta: revisão do cronograma atual.
Maria: Estamos no prazo com o desenvolvimento da API.
Pedro: Frontend está 80% concluído, faltam apenas os testes.

João: Ótimo progresso. Algum bloqueio?
Maria: Precisamos definir a estrutura do banco para o módulo de relatórios.
Pedro: Concordo, isso está impactando a finalização da tela de dashboards.

João: Ok, vou agendar uma reunião técnica para amanhã.
Maria: Perfeito, assim conseguimos desbloquear.
Pedro: Excelente, obrigado João.',
    'Reunião de alinhamento do Projeto Alpha com boa evolução. API no prazo, frontend 80% concluído. Identificado bloqueio na estrutura do banco para relatórios.',
    '[{"decisao": "Agendar reunião técnica para definir estrutura do banco", "responsavel": "João Silva", "prazo": "2025-06-01"}]'::jsonb,
    '[{"acao": "Finalizar testes do frontend", "responsavel": "Pedro Costa", "prazo": "2025-06-03"}, {"acao": "Preparar proposta de estrutura do banco", "responsavel": "Maria Santos", "prazo": "2025-06-01"}]'::jsonb,
    '[{"pendencia": "Definição da estrutura do banco para módulo de relatórios"}]'::jsonb,
    '[{"insight": "Equipe bem alinhada e proativa na identificação de bloqueios"}]'::jsonb
);

-- 7. Verificar se as tabelas foram criadas
SELECT 'login_user' as tabela, COUNT(*) as registros FROM login_user
UNION ALL
SELECT 'base_conhecimento' as tabela, COUNT(*) as registros FROM base_conhecimento
UNION ALL
SELECT 'historico_reunioes' as tabela, COUNT(*) as registros FROM historico_reunioes;