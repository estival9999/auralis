#!/usr/bin/env python3
"""
Script principal para processar documentos da base de conhecimento
Executa o processamento de arquivos TXT e envia para o Supabase
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import argparse
import json

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from base_conhecimento_processor import ProcessadorBaseConhecimento


def exibir_banner():
    """Exibe banner inicial do processador"""
    print("\n" + "="*60)
    print("🧠 PROCESSADOR DE BASE DE CONHECIMENTO AURALIS")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60 + "\n")


def processar_arquivo_unico(processador: ProcessadorBaseConhecimento, caminho: str, versao: str = "1.0"):
    """Processa um único arquivo TXT"""
    print(f"\n📄 Processando arquivo único: {caminho}")
    
    if not os.path.exists(caminho):
        print(f"❌ Erro: Arquivo não encontrado: {caminho}")
        return False
    
    if not caminho.endswith('.txt'):
        print(f"❌ Erro: O arquivo deve ser .txt")
        return False
    
    resultado = processador.processar_documento(caminho, versao)
    
    # Exibe resumo do resultado
    print("\n" + "-"*50)
    print("📊 RESUMO DO PROCESSAMENTO:")
    print("-"*50)
    
    if resultado['status'] == 'sucesso':
        print(f"✅ Status: SUCESSO")
        print(f"📄 Documento: {resultado['documento']}")
        print(f"📑 Tipo: {resultado['tipo']}")
        print(f"📁 Categoria: {resultado['categoria']}")
        print(f"🏷️  Tags: {', '.join(resultado['tags'])}")
        print(f"📊 Chunks: {resultado['chunks_processados']}/{resultado['total_chunks']}")
        print(f"🔐 Hash: {resultado['hash'][:16]}...")
        
        if resultado['erros']:
            print(f"\n⚠️  Erros encontrados: {len(resultado['erros'])}")
            for erro in resultado['erros'][:3]:  # Mostra até 3 erros
                print(f"   - {erro}")
    
    elif resultado['status'] == 'ja_existe':
        print(f"⚠️  Status: DOCUMENTO JÁ EXISTE")
        print(f"📄 Documento: {resultado['documento']}")
        print(f"🔐 Hash: {resultado['hash'][:16]}...")
        print("ℹ️  O documento já foi processado anteriormente com o mesmo conteúdo")
    
    else:
        print(f"❌ Status: ERRO")
        print(f"📄 Documento: {resultado['documento']}")
        print(f"❗ Erro: {resultado['erro']}")
    
    return resultado['status'] == 'sucesso'


def processar_pasta_completa(processador: ProcessadorBaseConhecimento, caminho: str):
    """Processa todos os arquivos TXT em uma pasta"""
    print(f"\n📁 Processando pasta: {caminho}")
    
    if not os.path.exists(caminho):
        print(f"❌ Erro: Pasta não encontrada: {caminho}")
        return
    
    resultados = processador.processar_pasta(caminho)
    
    # Exibe resumo geral
    print("\n" + "="*60)
    print("📊 RESUMO GERAL DO PROCESSAMENTO")
    print("="*60)
    
    total = len(resultados)
    sucessos = sum(1 for r in resultados if r['status'] == 'sucesso')
    ja_existentes = sum(1 for r in resultados if r['status'] == 'ja_existe')
    erros = sum(1 for r in resultados if r['status'] == 'erro')
    
    print(f"📁 Total de arquivos: {total}")
    print(f"✅ Processados com sucesso: {sucessos}")
    print(f"⚠️  Já existentes: {ja_existentes}")
    print(f"❌ Erros: {erros}")
    
    # Lista arquivos com erro
    if erros > 0:
        print("\n❌ Arquivos com erro:")
        for r in resultados:
            if r['status'] == 'erro':
                print(f"   - {r['documento']}: {r['erro']}")


def buscar_conhecimento(processador: ProcessadorBaseConhecimento):
    """Interface interativa para buscar na base de conhecimento"""
    print("\n🔍 MODO DE BUSCA NA BASE DE CONHECIMENTO")
    print("Digite 'sair' para voltar ao menu principal\n")
    
    while True:
        consulta = input("🔍 Digite sua busca: ").strip()
        
        if consulta.lower() == 'sair':
            break
        
        if not consulta:
            continue
        
        # Pergunta por filtros opcionais
        usar_filtros = input("Deseja usar filtros? (s/n): ").lower() == 's'
        filtros = {}
        
        if usar_filtros:
            tipo = input("Tipo de documento (deixe vazio para todos): ").strip()
            if tipo:
                filtros['tipo_documento'] = tipo
            
            categoria = input("Categoria (deixe vazio para todas): ").strip()
            if categoria:
                filtros['categoria'] = categoria
        
        # Realiza busca
        print("\n🔄 Buscando...")
        resultados = processador.buscar_conhecimento(consulta, limite=5, filtros=filtros)
        
        if resultados:
            print(f"\n📋 Encontrados {len(resultados)} resultados:\n")
            
            for i, resultado in enumerate(resultados, 1):
                print(f"{i}. 📄 {resultado['documento_origem']} [{resultado['tipo_documento']}]")
                print(f"   📊 Similaridade: {resultado['similaridade']:.2%}")
                print(f"   📝 Trecho: {resultado['conteudo'][:200]}...")
                print(f"   🏷️  Tags: {', '.join(resultado['tags'])}")
                print()
        else:
            print("\n❌ Nenhum resultado encontrado")
        
        print("-" * 60)


def listar_documentos(processador: ProcessadorBaseConhecimento):
    """Lista todos os documentos processados"""
    print("\n📚 DOCUMENTOS NA BASE DE CONHECIMENTO")
    print("-" * 60)
    
    documentos = processador.listar_documentos()
    
    if documentos:
        print(f"Total: {len(documentos)} documentos\n")
        
        # Agrupa por tipo
        por_tipo = {}
        for doc in documentos:
            tipo = doc['tipo']
            if tipo not in por_tipo:
                por_tipo[tipo] = []
            por_tipo[tipo].append(doc)
        
        # Exibe por tipo
        for tipo, docs in por_tipo.items():
            print(f"\n📑 {tipo.upper()} ({len(docs)} documentos):")
            for doc in docs:
                print(f"   - {doc['documento']} [{doc['categoria']}] v{doc['versao']}")
    else:
        print("❌ Nenhum documento encontrado na base")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Processador de Base de Conhecimento AURALIS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python processar_base_conhecimento.py base_conhecimento.txt
  python processar_base_conhecimento.py --pasta documentos/
  python processar_base_conhecimento.py --buscar
  python processar_base_conhecimento.py --listar
        """
    )
    
    parser.add_argument('arquivo', nargs='?', help='Arquivo TXT para processar')
    parser.add_argument('--pasta', help='Processar todos os TXT de uma pasta')
    parser.add_argument('--versao', default='1.0', help='Versão do documento (padrão: 1.0)')
    parser.add_argument('--buscar', action='store_true', help='Modo de busca interativa')
    parser.add_argument('--listar', action='store_true', help='Listar documentos processados')
    
    args = parser.parse_args()
    
    # Exibe banner
    exibir_banner()
    
    # Inicializa processador
    try:
        processador = ProcessadorBaseConhecimento()
    except Exception as e:
        print(f"❌ Erro ao inicializar processador: {e}")
        print("\n⚠️  Verifique se as variáveis de ambiente estão configuradas:")
        print("   - OPENAI_API_KEY")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_ANON_KEY")
        return 1
    
    # Executa ação baseada nos argumentos
    if args.buscar:
        buscar_conhecimento(processador)
    
    elif args.listar:
        listar_documentos(processador)
    
    elif args.pasta:
        processar_pasta_completa(processador, args.pasta)
    
    elif args.arquivo:
        sucesso = processar_arquivo_unico(processador, args.arquivo, args.versao)
        return 0 if sucesso else 1
    
    else:
        # Menu interativo se nenhum argumento foi passado
        while True:
            print("\n📋 MENU PRINCIPAL:")
            print("1. Processar arquivo único (base_conhecimento.txt)")
            print("2. Processar pasta de documentos")
            print("3. Buscar na base de conhecimento")
            print("4. Listar documentos processados")
            print("5. Sair")
            
            opcao = input("\nEscolha uma opção (1-5): ").strip()
            
            if opcao == '1':
                # Processa arquivo padrão
                arquivo_padrao = "base_conhecimento.txt"
                if os.path.exists(arquivo_padrao):
                    processar_arquivo_unico(processador, arquivo_padrao)
                else:
                    print(f"\n❌ Arquivo '{arquivo_padrao}' não encontrado!")
                    arquivo = input("Digite o caminho do arquivo TXT: ").strip()
                    if arquivo:
                        processar_arquivo_unico(processador, arquivo)
            
            elif opcao == '2':
                pasta = input("\nDigite o caminho da pasta: ").strip()
                if pasta:
                    processar_pasta_completa(processador, pasta)
            
            elif opcao == '3':
                buscar_conhecimento(processador)
            
            elif opcao == '4':
                listar_documentos(processador)
            
            elif opcao == '5':
                print("\n👋 Encerrando processador...")
                break
            
            else:
                print("\n❌ Opção inválida!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())