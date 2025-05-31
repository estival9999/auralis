-- PASSO 4: Inserir usuários de teste
-- Execute no Supabase Dashboard > SQL Editor

INSERT INTO login_user (username, password, nome_completo, cargo, area) VALUES 
('admin', 'admin123', 'Administrador', 'Administrador', 'TI'),
('joao.silva', 'admin123', 'João Silva', 'Gerente de Projetos', 'Desenvolvimento'),
('maria.santos', 'admin123', 'Maria Santos', 'Analista de Negócios', 'Comercial'),
('pedro.costa', 'admin123', 'Pedro Costa', 'Desenvolvedor Senior', 'Desenvolvimento')
ON CONFLICT (username) DO NOTHING;