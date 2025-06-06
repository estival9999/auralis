#!/usr/bin/env python3
"""
Bateria de Testes para Sistema AURALIS
Testa diferentes tipos de perguntas e analisa qualidade das respostas
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Tuple
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agente_busca_melhorado import AgenteBuscaMelhorado

class TestadorAuralis:
    def __init__(self):
        self.agente = AgenteBuscaMelhorado()
        self.resultados = []
        
    async def executar_teste(self, pergunta: str, categoria: str, complexidade: str) -> Dict:
        """Executa um teste individual e retorna resultado estruturado"""
        print(f"\n{'='*80}")
        print(f"CATEGORIA: {categoria} | COMPLEXIDADE: {complexidade}")
        print(f"PERGUNTA: {pergunta}")
        print(f"{'='*80}")
        
        inicio = datetime.now()
        
        try:
            # Processa a pergunta
            resposta = await self.agente.processar_pergunta(pergunta)
            
            fim = datetime.now()
            tempo_resposta = (fim - inicio).total_seconds()
            
            # Analisa a resposta
            analise = self._analisar_resposta(resposta, pergunta, categoria)
            
            resultado = {
                "pergunta": pergunta,
                "categoria": categoria,
                "complexidade": complexidade,
                "resposta": resposta,
                "tempo_resposta": tempo_resposta,
                "analise": analise,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\nRESPOSTA: {resposta}")
            print(f"TEMPO: {tempo_resposta:.2f}s")
            print(f"QUALIDADE: {analise['qualidade_geral']}/10")
            
            return resultado
            
        except Exception as e:
            print(f"ERRO: {str(e)}")
            return {
                "pergunta": pergunta,
                "categoria": categoria,
                "complexidade": complexidade,
                "erro": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _analisar_resposta(self, resposta: str, pergunta: str, categoria: str) -> Dict:
        """Analisa qualidade da resposta"""
        analise = {
            "tem_conteudo": len(resposta.strip()) > 0,
            "tamanho_resposta": len(resposta),
            "menciona_fontes": any(fonte in resposta.lower() for fonte in ["reunião", "base de conhecimento", "documento"]),
            "responde_pergunta": self._verifica_relevancia(resposta, pergunta),
            "clareza": self._avaliar_clareza(resposta),
            "completude": self._avaliar_completude(resposta, categoria),
            "qualidade_geral": 0
        }
        
        # Calcula qualidade geral
        pontos = 0
        if analise["tem_conteudo"]: pontos += 2
        if analise["menciona_fontes"]: pontos += 2
        if analise["responde_pergunta"]: pontos += 3
        if analise["clareza"] >= 7: pontos += 2
        if analise["completude"] >= 7: pontos += 1
        
        analise["qualidade_geral"] = pontos
        return analise
    
    def _verifica_relevancia(self, resposta: str, pergunta: str) -> bool:
        """Verifica se a resposta é relevante para a pergunta"""
        # Análise simplificada - pode ser melhorada
        palavras_chave = pergunta.lower().split()
        palavras_importantes = [p for p in palavras_chave if len(p) > 3]
        
        if not palavras_importantes:
            return True
        
        resposta_lower = resposta.lower()
        relevancia = sum(1 for palavra in palavras_importantes if palavra in resposta_lower)
        
        return relevancia >= len(palavras_importantes) * 0.3
    
    def _avaliar_clareza(self, resposta: str) -> int:
        """Avalia clareza da resposta de 0 a 10"""
        pontos = 10
        
        # Penaliza respostas muito curtas ou muito longas
        if len(resposta) < 50: pontos -= 3
        elif len(resposta) > 1000: pontos -= 2
        
        # Verifica estruturação
        if "\n" in resposta: pontos += 1
        if any(marcador in resposta for marcador in ["1.", "2.", "-", "•"]): pontos += 1
        
        # Limita entre 0 e 10
        return max(0, min(10, pontos))
    
    def _avaliar_completude(self, resposta: str, categoria: str) -> int:
        """Avalia completude da resposta de 0 a 10"""
        pontos = 5  # Base
        
        # Bonus por categoria
        if categoria == "reunioes" and "reunião" in resposta.lower():
            pontos += 2
        elif categoria == "base_conhecimento" and "conhecimento" in resposta.lower():
            pontos += 2
        elif categoria == "hibrida" and all(termo in resposta.lower() for termo in ["reunião", "conhecimento"]):
            pontos += 3
        
        # Bonus por detalhamento
        if len(resposta) > 200: pontos += 1
        if any(exemplo in resposta.lower() for exemplo in ["por exemplo", "como", "específico"]): pontos += 1
        
        return max(0, min(10, pontos))
    
    async def executar_bateria_completa(self):
        """Executa todos os testes da bateria"""
        
        # Define perguntas de teste por categoria
        testes = [
            # CATEGORIA: Reuniões - Fácil
            ("Quais reuniões foram realizadas esta semana?", "reunioes", "facil"),
            ("Quantas reuniões temos registradas?", "reunioes", "facil"),
            ("Qual foi a última reunião gravada?", "reunioes", "facil"),
            
            # CATEGORIA: Reuniões - Média
            ("Quais foram os principais tópicos discutidos nas reuniões de janeiro?", "reunioes", "media"),
            ("Quem participou das reuniões sobre o projeto X?", "reunioes", "media"),
            ("Resuma as decisões tomadas na última reunião de diretoria", "reunioes", "media"),
            
            # CATEGORIA: Reuniões - Difícil
            ("Compare as discussões sobre orçamento entre as reuniões de Q1 e Q2", "reunioes", "dificil"),
            ("Identifique padrões recorrentes nas pautas das últimas 10 reuniões", "reunioes", "dificil"),
            ("Qual foi a evolução do projeto ABC ao longo das reuniões dos últimos 3 meses?", "reunioes", "dificil"),
            
            # CATEGORIA: Base de Conhecimento - Fácil
            ("O que é o sistema AURALIS?", "base_conhecimento", "facil"),
            ("Quais são os principais componentes do sistema?", "base_conhecimento", "facil"),
            ("Como funciona o processamento de áudio?", "base_conhecimento", "facil"),
            
            # CATEGORIA: Base de Conhecimento - Média
            ("Explique a arquitetura de agentes do sistema", "base_conhecimento", "media"),
            ("Como o sistema realiza busca semântica?", "base_conhecimento", "media"),
            ("Quais são as melhores práticas para usar o AURALIS?", "base_conhecimento", "media"),
            
            # CATEGORIA: Base de Conhecimento - Difícil
            ("Compare as vantagens e desvantagens das diferentes estratégias de embeddings usadas", "base_conhecimento", "dificil"),
            ("Como otimizar a performance do sistema para grandes volumes de dados?", "base_conhecimento", "dificil"),
            ("Explique o processo completo de análise contextual multi-fonte", "base_conhecimento", "dificil"),
            
            # CATEGORIA: Híbrida (Reuniões + Base) - Média
            ("Como as reuniões são processadas segundo a documentação do sistema?", "hibrida", "media"),
            ("Quais funcionalidades do AURALIS foram discutidas nas últimas reuniões?", "hibrida", "media"),
            ("Compare o que foi planejado nas reuniões com o que está documentado no sistema", "hibrida", "media"),
            
            # CATEGORIA: Híbrida - Difícil
            ("Analise se as decisões tomadas nas reuniões estão alinhadas com a arquitetura documentada", "hibrida", "dificil"),
            ("Identifique gaps entre o que foi discutido em reuniões e o que está implementado", "hibrida", "dificil"),
            ("Crie um roadmap baseado nas discussões de reuniões e capacidades atuais do sistema", "hibrida", "dificil"),
            
            # CATEGORIA: Sem Contexto - Subjetiva
            ("O que você acha sobre o futuro da IA em ambientes corporativos?", "sem_contexto", "subjetiva"),
            ("Como melhorar a produtividade em reuniões?", "sem_contexto", "subjetiva"),
            ("Qual a importância de documentar conhecimento organizacional?", "sem_contexto", "subjetiva"),
            
            # CATEGORIA: Perguntas Ambíguas/Desafiadoras
            ("Me fale sobre isso", "ambigua", "dificil"),
            ("O que aconteceu?", "ambigua", "dificil"),
            ("Explique melhor", "ambigua", "dificil"),
            ("Como assim?", "ambigua", "dificil"),
            
            # CATEGORIA: Perguntas Complexas Multi-parte
            ("Primeiro, liste todas as reuniões de 2024, depois identifique os participantes mais frequentes, e por fim sugira como melhorar o engajamento baseado nos padrões observados", "complexa", "muito_dificil"),
            ("Analise a evolução técnica do sistema AURALIS conforme documentado, correlacione com as discussões em reuniões, e proponha melhorias arquiteturais considerando ambas as perspectivas", "complexa", "muito_dificil"),
        ]
        
        print("\n" + "="*80)
        print("INICIANDO BATERIA DE TESTES DO SISTEMA AURALIS")
        print(f"Total de testes: {len(testes)}")
        print("="*80)
        
        for pergunta, categoria, complexidade in testes:
            resultado = await self.executar_teste(pergunta, categoria, complexidade)
            self.resultados.append(resultado)
            
            # Pequena pausa entre testes para não sobrecarregar
            await asyncio.sleep(0.5)
        
        # Gera relatório final
        await self._gerar_relatorio()
    
    async def _gerar_relatorio(self):
        """Gera relatório com análise dos resultados"""
        print("\n" + "="*80)
        print("RELATÓRIO FINAL DE TESTES")
        print("="*80)
        
        # Estatísticas gerais
        total_testes = len(self.resultados)
        testes_com_erro = sum(1 for r in self.resultados if "erro" in r)
        tempo_medio = sum(r.get("tempo_resposta", 0) for r in self.resultados if "tempo_resposta" in r) / (total_testes - testes_com_erro)
        
        print(f"\nESTATÍSTICAS GERAIS:")
        print(f"- Total de testes: {total_testes}")
        print(f"- Testes bem-sucedidos: {total_testes - testes_com_erro}")
        print(f"- Testes com erro: {testes_com_erro}")
        print(f"- Tempo médio de resposta: {tempo_medio:.2f}s")
        
        # Análise por categoria
        print(f"\nANÁLISE POR CATEGORIA:")
        categorias = {}
        for r in self.resultados:
            if "erro" not in r:
                cat = r["categoria"]
                if cat not in categorias:
                    categorias[cat] = []
                categorias[cat].append(r["analise"]["qualidade_geral"])
        
        for cat, qualidades in categorias.items():
            media = sum(qualidades) / len(qualidades) if qualidades else 0
            print(f"- {cat}: {media:.1f}/10 (baseado em {len(qualidades)} testes)")
        
        # Análise por complexidade
        print(f"\nANÁLISE POR COMPLEXIDADE:")
        complexidades = {}
        for r in self.resultados:
            if "erro" not in r:
                comp = r["complexidade"]
                if comp not in complexidades:
                    complexidades[comp] = []
                complexidades[comp].append(r["analise"]["qualidade_geral"])
        
        for comp, qualidades in complexidades.items():
            media = sum(qualidades) / len(qualidades) if qualidades else 0
            print(f"- {comp}: {media:.1f}/10 (baseado em {len(qualidades)} testes)")
        
        # Identificar problemas
        print(f"\nPROBLEMAS IDENTIFICADOS:")
        problemas = []
        
        for r in self.resultados:
            if "erro" in r:
                problemas.append(f"- Erro em '{r['pergunta']}': {r['erro']}")
            elif r.get("analise", {}).get("qualidade_geral", 0) < 5:
                problemas.append(f"- Baixa qualidade em '{r['pergunta']}' (nota: {r['analise']['qualidade_geral']}/10)")
        
        if problemas:
            for p in problemas[:10]:  # Limita a 10 problemas
                print(p)
        else:
            print("- Nenhum problema crítico identificado")
        
        # Salvar resultados detalhados
        with open("teste_auralis_resultados.json", "w", encoding="utf-8") as f:
            json.dump(self.resultados, f, ensure_ascii=False, indent=2)
        
        print(f"\nResultados detalhados salvos em: teste_auralis_resultados.json")

async def main():
    testador = TestadorAuralis()
    await testador.executar_bateria_completa()

if __name__ == "__main__":
    asyncio.run(main())