# Sistema AURALIS - Busca Semântica em Reuniões

## Visão Geral
Sistema completo de processamento e busca semântica em transcrições de reuniões, com:
- Processamento de embeddings usando OpenAI
- Armazenamento vetorial no Supabase
- Busca semântica inteligente
- Interface gráfica integrada

## Arquitetura

### Componentes Principais

1. **ProcessadorEmbeddings** (`src/embeddings_processor.py`)
   - Lê arquivos .txt de transcrições
   - Cria chunks inteligentes preservando contexto
   - Gera embeddings usando OpenAI Ada-002
   - Armazena no Supabase com metadados

2. **AgenteBuscaReunioes** (`src/agente_busca_reunioes.py`)
   - Interpreta perguntas do usuário
   - Busca chunks relevantes por similaridade
   - Conecta informações entre reuniões
   - Gera respostas contextualizadas

3. **Backend AURALIS** (`main.py`)
   - Gerencia autenticação de usuários
   - Integra processador e agente
   - Interface com FRONT.py

## Configuração

### 1. Instalar Dependências
```bash
pip install openai supabase numpy customtkinter python-dotenv
```

### 2. Configurar Variáveis de Ambiente
Crie um arquivo `.env`:
```
OPENAI_API_KEY=sua-chave-openai
SUPABASE_URL=sua-url-supabase
SUPABASE_ANON_KEY=sua-chave-anon
SUPABASE_SERVICE_ROLE_KEY=sua-chave-service
```

### 3. Configurar Banco de Dados
Execute o SQL em `create_tables.sql` no Supabase:
- Tabela `reunioes_embbed` para embeddings
- Tabela `login_user` para usuários
- Função de busca por similaridade

### 4. Ativar Extensão Vector
No Supabase SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Uso

### 1. Processar Reuniões
```bash
python main.py
```
Isso irá:
- Criar usuários padrão (admin/admin123)
- Processar arquivos em `teste_reuniao/`
- Gerar e salvar embeddings

### 2. Iniciar Interface
```bash
python FRONT.py
```

### 3. Fazer Perguntas
No assistente IA, pergunte coisas como:
- "Quais foram as principais decisões tomadas?"
- "Quem é responsável pelo projeto Beta?"
- "Quais problemas de infraestrutura foram discutidos?"
- "Existe conexão entre as reuniões sobre orçamento?"

## Formato dos Arquivos de Reunião

Coloque arquivos .txt em `teste_reuniao/` com:
- Nome: `reuniao_DD_MM_AAAA.txt`
- Conteúdo: Transcrição contínua sem identificação de falantes

## Funcionalidades do Agente

### Busca Específica
- Definições e conceitos
- Responsáveis e atribuições
- Decisões tomadas
- Problemas levantados
- Prazos e datas

### Análise Cruzada
- Conexões entre reuniões
- Evolução de temas
- Padrões e tendências
- Contradições ou mudanças

### Resposta Inteligente
- Cita trechos relevantes
- Indica quando não encontra informação
- Conecta informações dispersas
- Mantém contexto da conversa

## Usuários Padrão

1. **Admin**
   - Login: admin
   - Senha: admin123
   - Cargo: Administrador
   - Área: TI

2. **Usuário**
   - Login: usuario
   - Senha: senha123
   - Cargo: Analista
   - Área: Operações

## Troubleshooting

### Erro de Extensão Vector
Se receber erro sobre tipo 'vector':
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Erro de Embeddings
Verifique:
- OPENAI_API_KEY está correta
- Créditos disponíveis na OpenAI
- Tamanho dos chunks (máx 8191 tokens)

### Busca sem Resultados
- Verifique se os embeddings foram gerados
- Ajuste o threshold de similaridade
- Verifique se a tabela tem dados

## Estrutura de Dados

### Tabela reunioes_embbed
- `id`: UUID único
- `arquivo_origem`: Nome do arquivo
- `data_reuniao`: Data extraída
- `chunk_numero`: Ordem do chunk
- `chunk_texto`: Texto do chunk
- `embedding`: Vector 1536 dimensões
- `metadados`: JSON com participantes, temas, etc

### Tabela login_user
- `id`: UUID único
- `username`: Nome de usuário
- `password_hash`: Hash SHA-256
- `cargo`: Cargo do usuário
- `area`: Área/departamento