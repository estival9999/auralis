#!/usr/bin/env python3
"""
Script para importar arquivos TXT para a base de conhecimento do AURALIS
Lê arquivos da pasta update_conhecimento/ e insere no Supabase
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from loguru import logger

# Adicionar diretórios ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.config import UPDATE_CONHECIMENTO_DIR, LOG_FORMAT, LOG_LEVEL
from src.database.supabase_client import supabase_client

# Configurar logging
logger.remove()
logger.add(sys.stderr, format=LOG_FORMAT, level=LOG_LEVEL)

class ImportadorConhecimento:
    """Importa documentos TXT para base de conhecimento"""
    
    def __init__(self):
        self.pasta_origem = UPDATE_CONHECIMENTO_DIR
        self.arquivos_processados = []
        self.erros = []
    
    async def importar_arquivos(self):
        """Processa todos os arquivos TXT da pasta"""
        logger.info(f"Iniciando importação de arquivos de: {self.pasta_origem}")
        
        # Verificar se pasta existe
        if not self.pasta_origem.exists():
            logger.error(f"Pasta não encontrada: {self.pasta_origem}")
            return
        
        # Listar arquivos TXT
        arquivos_txt = list(self.pasta_origem.glob("*.txt"))
        
        if not arquivos_txt:
            logger.warning("Nenhum arquivo TXT encontrado para importar")
            return
        
        logger.info(f"Encontrados {len(arquivos_txt)} arquivos para processar")
        
        # Processar cada arquivo
        for arquivo in arquivos_txt:
            await self.processar_arquivo(arquivo)
        
        # Relatório final
        self.exibir_relatorio()
    
    async def processar_arquivo(self, arquivo_path: Path):
        """Processa um arquivo individual"""
        try:
            logger.info(f"Processando: {arquivo_path.name}")
            
            # Ler conteúdo
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            if not conteudo.strip():
                logger.warning(f"Arquivo vazio: {arquivo_path.name}")
                return
            
            # Extrair metadados do nome do arquivo
            titulo = arquivo_path.stem  # Nome sem extensão
            categoria = self.extrair_categoria(titulo)
            tags = self.extrair_tags(titulo, conteudo)
            
            # Inserir no banco
            sucesso = await supabase_client.insert_knowledge_base(
                titulo=titulo,
                conteudo=conteudo,
                categoria=categoria,
                tags=tags
            )
            
            if sucesso:
                self.arquivos_processados.append(arquivo_path.name)
                logger.success(f"✓ Importado: {arquivo_path.name}")
                
                # Mover para pasta de processados
                await self.mover_para_processados(arquivo_path)
            else:
                self.erros.append(f"Erro ao importar: {arquivo_path.name}")
                logger.error(f"✗ Falha ao importar: {arquivo_path.name}")
                
        except Exception as e:
            erro_msg = f"Erro ao processar {arquivo_path.name}: {str(e)}"
            self.erros.append(erro_msg)
            logger.error(erro_msg)
    
    def extrair_categoria(self, titulo: str) -> str:
        """Extrai categoria baseada no título do arquivo"""
        titulo_lower = titulo.lower()
        
        # Mapeamento de palavras-chave para categorias
        categorias = {
            'politica': ['política', 'policy', 'norma', 'regra'],
            'procedimento': ['procedimento', 'processo', 'fluxo', 'passo'],
            'manual': ['manual', 'guia', 'tutorial', 'instrução'],
            'template': ['template', 'modelo', 'exemplo'],
            'relatorio': ['relatório', 'report', 'análise'],
            'ata': ['ata', 'reunião', 'meeting'],
            'projeto': ['projeto', 'project', 'iniciativa']
        }
        
        for categoria, palavras in categorias.items():
            if any(palavra in titulo_lower for palavra in palavras):
                return categoria
        
        return 'geral'
    
    def extrair_tags(self, titulo: str, conteudo: str) -> list:
        """Extrai tags relevantes do documento"""
        tags = []
        texto_completo = f"{titulo} {conteudo}".lower()
        
        # Tags comuns a procurar
        tags_padrao = [
            'rh', 'ti', 'financeiro', 'comercial', 'operacional',
            'compliance', 'segurança', 'qualidade', 'treinamento',
            'onboarding', 'férias', 'benefícios', 'home office',
            'desenvolvimento', 'agile', 'scrum', 'kanban'
        ]
        
        for tag in tags_padrao:
            if tag in texto_completo:
                tags.append(tag)
        
        # Adicionar primeiras palavras do título como tags
        palavras_titulo = titulo.split()[:3]
        tags.extend([p.lower() for p in palavras_titulo if len(p) > 3])
        
        # Remover duplicatas
        return list(set(tags))[:10]  # Limitar a 10 tags
    
    async def mover_para_processados(self, arquivo_path: Path):
        """Move arquivo para pasta de processados"""
        try:
            # Criar pasta de processados se não existir
            pasta_processados = self.pasta_origem / "processados"
            pasta_processados.mkdir(exist_ok=True)
            
            # Mover arquivo
            destino = pasta_processados / arquivo_path.name
            arquivo_path.rename(destino)
            logger.debug(f"Arquivo movido para: {destino}")
            
        except Exception as e:
            logger.warning(f"Não foi possível mover arquivo: {e}")
    
    def exibir_relatorio(self):
        """Exibe relatório final da importação"""
        logger.info("\n" + "="*50)
        logger.info("RELATÓRIO DE IMPORTAÇÃO")
        logger.info("="*50)
        logger.info(f"Total de arquivos processados: {len(self.arquivos_processados)}")
        logger.info(f"Sucessos: {len(self.arquivos_processados)}")
        logger.info(f"Erros: {len(self.erros)}")
        
        if self.arquivos_processados:
            logger.info("\nArquivos importados com sucesso:")
            for arquivo in self.arquivos_processados:
                logger.info(f"  ✓ {arquivo}")
        
        if self.erros:
            logger.error("\nErros encontrados:")
            for erro in self.erros:
                logger.error(f"  ✗ {erro}")
        
        logger.info("="*50 + "\n")

async def main():
    """Função principal"""
    importador = ImportadorConhecimento()
    await importador.importar_arquivos()

if __name__ == "__main__":
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║          AURALIS - Importador de Base de Conhecimento    ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Este script importa arquivos TXT da pasta:              ║
    ║  {str(UPDATE_CONHECIMENTO_DIR):^55} ║
    ║                                                           ║
    ║  Os arquivos serão inseridos na tabela base_conhecimento ║
    ║  e movidos para a subpasta 'processados' após importação ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    confirmar = input("\nDeseja continuar? (s/n): ")
    if confirmar.lower() == 's':
        asyncio.run(main())
    else:
        print("Importação cancelada.")