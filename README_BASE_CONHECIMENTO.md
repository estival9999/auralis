# 📚 Sistema de Base de Conhecimento AURALIS

## 🎯 Visão Geral

O Sistema de Base de Conhecimento AURALIS processa documentos empresariais (manuais, estatutos, procedimentos) e os prepara para busca semântica inteligente, similar ao processamento de reuniões já existente no sistema.

## 🚀 Como Usar

### 1️⃣ Configuração Inicial do Banco de Dados

Execute o SQL fornecido no arquivo `base_conhecimento_schema.sql` no seu Supabase:

```sql
-- Execute todo o conteúdo do arquivo base_conhecimento_schema.sql
-- Isso criará:
-- - Tabela base_conhecimento
-- - Tabela base_conhecimento_versoes
-- - Índices otimizados
-- - Funções de busca semântica
```

### 2️⃣ Preparar Documentos

Coloque seus documentos em formato `.txt` no diretório do projeto:

```
DOZERO/
├── base_conhecimento.txt         # Arquivo padrão
├── documentos/                   # Ou em uma pasta
│   ├── manual_operacional.txt
│   ├── estatuto_social.txt
│   └── procedimentos_qualidade.txt
```

### 3️⃣ Executar o Processamento

#### Opção 1: Processar arquivo único (padrão)
```bash
python processar_base_conhecimento.py
# Processa automaticamente o arquivo base_conhecimento.txt
```

#### Opção 2: Processar arquivo específico
```bash
python processar_base_conhecimento.py caminho/para/documento.txt
```

#### Opção 3: Processar pasta inteira
```bash
python processar_base_conhecimento.py --pasta documentos/
```

#### Opção 4: Menu interativo
```bash
python processar_base_conhecimento.py
# Escolha opções no menu
```

### 4️⃣ Buscar na Base de Conhecimento

```bash
python processar_base_conhecimento.py --buscar
```

Exemplo de busca:
```
🔍 Digite sua busca: procedimentos de segurança
Deseja usar filtros? (s/n): s
Tipo de documento: manual
Categoria: procedimento_seguranca
```

### 5️⃣ Listar Documentos Processados

```bash
python processar_base_conhecimento.py --listar
```

## 📊 Estrutura de Dados

### Tabela: `base_conhecimento`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | UUID | Identificador único |
| conteudo | TEXT | Conteúdo do chunk |
| embedding | vector(1536) | Vetor para busca semântica |
| chunk_index | INTEGER | Posição no documento |
| documento_origem | TEXT | Nome do arquivo original |
| tipo_documento | TEXT | manual, estatuto, procedimento |
| categoria | TEXT | Subcategoria específica |
| tags | TEXT[] | Tags para filtragem |
| metadata | JSONB | Metadados adicionais |

### Tipos de Documentos Detectados

- **manual**: Manuais técnicos e operacionais
- **estatuto**: Estatutos e regulamentos
- **procedimento**: Procedimentos e processos
- **politica**: Políticas e diretrizes
- **documento**: Outros documentos

## 🔧 Configuração Avançada

### Ajustar Tamanho dos Chunks

No arquivo `src/base_conhecimento_processor.py`:

```python
self.chunk_size = 1500      # Caracteres por chunk
self.chunk_overlap = 200    # Overlap entre chunks
```

### Personalizar Detecção de Tipos

Edite o método `detectar_tipo_documento()` para adicionar novos tipos:

```python
elif 'nova_palavra' in conteudo_lower:
    tipo = 'novo_tipo'
    categoria = 'nova_categoria'
```

## 🔍 Integração com o Sistema AURALIS

O processador se integra perfeitamente com o sistema existente:

1. **Usa os mesmos clientes** (OpenAI e Supabase)
2. **Mesmo formato de embeddings** (text-embedding-ada-002)
3. **Estrutura similar** à tabela de reuniões
4. **Busca semântica unificada** possível

### Exemplo de Busca Combinada (futuro)

```python
# Buscar em reuniões E base de conhecimento
resultados_reunioes = buscar_reunioes("segurança")
resultados_conhecimento = buscar_conhecimento("segurança")
resultados_combinados = combinar_resultados(resultados_reunioes, resultados_conhecimento)
```

## 📈 Métricas e Monitoramento

Visualize estatísticas com a view SQL:

```sql
SELECT * FROM estatisticas_base_conhecimento;
```

Resultado:
```
tipo_documento | total_documentos | total_chunks | tamanho_medio_chunk
---------------|------------------|--------------|--------------------
manual         | 3                | 45           | 1480
procedimento   | 2                | 28           | 1520
estatuto       | 1                | 15           | 1495
```

## 🛠️ Troubleshooting

### Erro: "Arquivo vazio"
- Verifique se o arquivo .txt contém conteúdo
- Confirme a codificação UTF-8

### Erro: "Embedding failed"
- Verifique sua OPENAI_API_KEY
- Confirme conectividade com a API

### Erro: "Supabase insert failed"
- Verifique credenciais Supabase
- Confirme que as tabelas foram criadas
- Verifique limites de armazenamento

## 🚀 Próximos Passos

1. **Atualização Automática**: Implementar verificação de mudanças nos documentos
2. **Interface Web**: Adicionar upload via interface gráfica
3. **OCR**: Suporte para PDFs e imagens
4. **Multilíngue**: Suporte para documentos em outros idiomas
5. **Versionamento**: Controle detalhado de versões com diff

## 📞 Suporte

Em caso de dúvidas ou problemas:
- Verifique os logs no terminal
- Consulte o arquivo de exemplo `base_conhecimento.txt`
- Revise as configurações no `.env`

---

💡 **Dica**: Execute primeiro com o arquivo de exemplo fornecido para testar se tudo está funcionando corretamente!