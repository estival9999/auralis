#!/usr/bin/env python3
"""
Teste Simplificado do Sistema AURALIS
Versão síncrona para testar a performance do agente
"""

import json
import time
from datetime import datetime
from typing import Dict, List
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agente_busca_melhorado import AgenteBuscaMelhorado

class TestadorAuralisSimples:
    def __init__(self):
        print("Inicializando testador AURALIS...")
        try:
            self.agente = AgenteBuscaMelhorado()
            print("✅ Agente inicializado com sucesso")
        except Exception as e:
            print(f"❌ Erro ao inicializar agente: {e}")
            raise
        
        self.resultados = []
        
    def executar_teste(self, pergunta: str, categoria: str, complexidade: str) -> Dict:
        """Executa um teste individual"""
        print(f"\n{'='*80}")
        print(f"CATEGORIA: {categoria} | COMPLEXIDADE: {complexidade}")
        print(f"PERGUNTA: {pergunta}")
        print(f"{'='*80}")
        
        inicio = time.time()
        
        try:
            # Processa a pergunta (versão síncrona)
            resposta = self.agente.processar_pergunta(pergunta)
            
            fim = time.time()
            tempo_resposta = fim - inicio
            
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
            
            print(f"\nRESPOSTA ({len(resposta)} caracteres):")
            # Limita a exibição da resposta
            if len(resposta) > 300:
                print(resposta[:300] + "...")
            else:
                print(resposta)
            
            print(f"\nTEMPO: {tempo_resposta:.2f}s")
            print(f"QUALIDADE: {analise['qualidade_geral']}/10")
            
            # Análise detalhada
            print(f"\nANÁLISE:")
            print(f"- Menciona fontes: {'✅' if analise['menciona_fontes'] else '❌'}")
            print(f"- Responde pergunta: {'✅' if analise['responde_pergunta'] else '❌'}")
            print(f"- Clareza: {analise['clareza']}/10")
            print(f"- Completude: {analise['completude']}/10")
            
            return resultado
            
        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
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
            "menciona_fontes": any(fonte in resposta.lower() for fonte in ["reunião", "base de conhecimento", "documento", "informação disponível"]),
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
        """Verifica se a resposta é relevante"""
        palavras_chave = pergunta.lower().split()
        palavras_importantes = [p for p in palavras_chave if len(p) > 3 and p not in ["qual", "quais", "como", "onde", "quando", "porque"]]
        
        if not palavras_importantes:
            return True
        
        resposta_lower = resposta.lower()
        relevancia = sum(1 for palavra in palavras_importantes if palavra in resposta_lower)
        
        return relevancia >= len(palavras_importantes) * 0.3
    
    def _avaliar_clareza(self, resposta: str) -> int:
        """Avalia clareza da resposta"""
        pontos = 10
        
        if len(resposta) < 50: pontos -= 3
        elif len(resposta) > 1500: pontos -= 2
        
        if "\n" in resposta: pontos += 1
        if any(marcador in resposta for marcador in ["1.", "2.", "-", "•"]): pontos += 1
        
        return max(0, min(10, pontos))
    
    def _avaliar_completude(self, resposta: str, categoria: str) -> int:
        """Avalia completude da resposta"""
        pontos = 5
        
        if categoria == "reunioes" and "reunião" in resposta.lower():
            pontos += 2
        elif categoria == "base_conhecimento" and any(k in resposta.lower() for k in ["conhecimento", "sistema", "auralis"]):
            pontos += 2
        elif categoria == "hibrida" and any(termo in resposta.lower() for termo in ["reunião", "conhecimento"]):
            pontos += 3
        
        if len(resposta) > 200: pontos += 1
        if any(exemplo in resposta.lower() for exemplo in ["por exemplo", "como", "específico"]): pontos += 1
        
        return max(0, min(10, pontos))
    
    def executar_bateria_reduzida(self):
        """Executa uma bateria reduzida de testes essenciais"""
        
        # Conjunto reduzido mas representativo de testes
        testes = [
            # Reuniões - Básico
            ("Quais reuniões foram realizadas recentemente?", "reunioes", "facil"),
            ("Qual foi o tema da última reunião gravada?", "reunioes", "facil"),
            
            # Reuniões - Intermediário
            ("Resuma os principais pontos discutidos nas reuniões sobre tecnologia", "reunioes", "media"),
            ("Quem são os participantes mais frequentes nas reuniões?", "reunioes", "media"),
            
            # Base de Conhecimento - Básico
            ("O que é o sistema AURALIS?", "base_conhecimento", "facil"),
            ("Como funciona o processamento de reuniões?", "base_conhecimento", "facil"),
            
            # Base de Conhecimento - Intermediário
            ("Explique a arquitetura do sistema de busca", "base_conhecimento", "media"),
            ("Quais são as principais funcionalidades do AURALIS?", "base_conhecimento", "media"),
            
            # Híbrida
            ("Como as reuniões são armazenadas e processadas pelo sistema?", "hibrida", "media"),
            ("Existe alguma reunião que discutiu melhorias no sistema AURALIS?", "hibrida", "media"),
            
            # Sem Contexto/Subjetiva
            ("Como melhorar a eficiência das reuniões corporativas?", "sem_contexto", "subjetiva"),
            
            # Ambígua
            ("Me explique isso melhor", "ambigua", "dificil"),
            
            # Complexa
            ("Liste as últimas reuniões, identifique os temas principais e sugira como o sistema pode ajudar a melhorar o acompanhamento desses temas", "complexa", "muito_dificil"),
        ]
        
        print("\n" + "="*80)
        print("INICIANDO BATERIA DE TESTES REDUZIDA DO SISTEMA AURALIS")
        print(f"Total de testes: {len(testes)}")
        print("="*80)
        
        for pergunta, categoria, complexidade in testes:
            resultado = self.executar_teste(pergunta, categoria, complexidade)
            self.resultados.append(resultado)
            
            # Pausa entre testes
            time.sleep(1)
        
        # Gera relatório
        self._gerar_relatorio()
    
    def _gerar_relatorio(self):
        """Gera relatório com análise dos resultados"""
        print("\n" + "="*80)
        print("RELATÓRIO FINAL DE TESTES")
        print("="*80)
        
        # Estatísticas gerais
        total_testes = len(self.resultados)
        testes_com_erro = sum(1 for r in self.resultados if "erro" in r)
        testes_ok = total_testes - testes_com_erro
        
        print(f"\n📊 ESTATÍSTICAS GERAIS:")
        print(f"- Total de testes: {total_testes}")
        print(f"- Testes bem-sucedidos: {testes_ok}")
        print(f"- Testes com erro: {testes_com_erro}")
        
        if testes_ok > 0:
            tempo_medio = sum(r.get("tempo_resposta", 0) for r in self.resultados if "tempo_resposta" in r) / testes_ok
            print(f"- Tempo médio de resposta: {tempo_medio:.2f}s")
        
        # Análise por categoria
        print(f"\n📈 ANÁLISE POR CATEGORIA:")
        categorias = {}
        for r in self.resultados:
            if "erro" not in r:
                cat = r["categoria"]
                if cat not in categorias:
                    categorias[cat] = {"qualidades": [], "tempos": []}
                categorias[cat]["qualidades"].append(r["analise"]["qualidade_geral"])
                categorias[cat]["tempos"].append(r["tempo_resposta"])
        
        for cat, dados in categorias.items():
            if dados["qualidades"]:
                media_qual = sum(dados["qualidades"]) / len(dados["qualidades"])
                media_tempo = sum(dados["tempos"]) / len(dados["tempos"])
                print(f"\n{cat.upper()}:")
                print(f"  - Qualidade média: {media_qual:.1f}/10")
                print(f"  - Tempo médio: {media_tempo:.2f}s")
                print(f"  - Amostras: {len(dados['qualidades'])}")
        
        # Problemas identificados
        print(f"\n⚠️  PROBLEMAS IDENTIFICADOS:")
        problemas_encontrados = False
        
        # Erros
        for r in self.resultados:
            if "erro" in r:
                print(f"- ❌ Erro em '{r['pergunta'][:50]}...': {r['erro']}")
                problemas_encontrados = True
        
        # Baixa qualidade
        for r in self.resultados:
            if "erro" not in r and r.get("analise", {}).get("qualidade_geral", 0) < 5:
                print(f"- ⚡ Baixa qualidade em '{r['pergunta'][:50]}...' (nota: {r['analise']['qualidade_geral']}/10)")
                problemas_encontrados = True
        
        if not problemas_encontrados:
            print("- ✅ Nenhum problema crítico identificado")
        
        # Insights
        print(f"\n💡 INSIGHTS E OBSERVAÇÕES:")
        
        # Análise de menção de fontes
        menciona_fontes = sum(1 for r in self.resultados if "erro" not in r and r["analise"]["menciona_fontes"])
        if testes_ok > 0:
            perc_fontes = (menciona_fontes / testes_ok) * 100
            print(f"- {perc_fontes:.0f}% das respostas mencionam fontes de dados")
        
        # Análise de relevância
        respostas_relevantes = sum(1 for r in self.resultados if "erro" not in r and r["analise"]["responde_pergunta"])
        if testes_ok > 0:
            perc_relevancia = (respostas_relevantes / testes_ok) * 100
            print(f"- {perc_relevancia:.0f}% das respostas são relevantes para as perguntas")
        
        # Salvar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"teste_auralis_resultados_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "resumo": {
                    "total_testes": total_testes,
                    "testes_ok": testes_ok,
                    "testes_erro": testes_com_erro,
                    "tempo_medio": tempo_medio if testes_ok > 0 else 0
                },
                "resultados_detalhados": self.resultados
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 Resultados salvos em: {filename}")

def main():
    print("🚀 Iniciando teste do sistema AURALIS...\n")
    
    try:
        testador = TestadorAuralisSimples()
        testador.executar_bateria_reduzida()
        
        print("\n✅ Testes concluídos com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução dos testes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()