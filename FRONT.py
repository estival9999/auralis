"""
Sistema de Reuniões AURALIS - Versão Linux Corrigida
Resolução fixa: 320x240 pixels
Interface otimizada para Linux com entrada de texto funcionando
Interface gráfica principal do sistema com integração completa ao backend de IA
"""

import sys
import os
from pathlib import Path

# IMPORTANTE: Carregar .env ANTES de importar outros módulos
def load_env():
    """
    Carrega variáveis de ambiente do arquivo .env
    
    Esta função é essencial para configurar as credenciais da API OpenAI
    e outras configurações do sistema antes da inicialização
    """
    env_file = Path(__file__).parent / '.env'
    
    if env_file.exists():
        print("📋 Carregando configurações de .env...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value.strip()
                        # Mostrar apenas parte da chave por segurança
                        if key == 'OPENAI_API_KEY':
                            print(f"   ✅ {key} configurada ({value[:20]}...)")
                        elif key in ['SUPABASE_URL', 'DEBUG_MODE']:
                            print(f"   ✅ {key} configurada")
    else:
        print("⚠️  Arquivo .env não encontrado")

# Carregar variáveis de ambiente antes de qualquer outra importação
load_env()

# Agora importar as outras bibliotecas com ambiente configurado
import customtkinter as ctk
from tkinter import messagebox, Canvas
from datetime import datetime, timedelta
import threading
import time
import math
import random
import numpy as np

# Importar o backend integrado (agora com as variáveis de ambiente carregadas)
# Este import deve acontecer após load_env() para garantir configuração correta
from main import AURALISBackend, process_message_async

class SistemaTFT:
    """
    Classe principal da interface gráfica do sistema AURALIS.
    
    Gerencia todas as telas, navegação, animações e integração com o backend.
    Otimizada para display de 320x240 pixels com tema escuro.
    """
    
    def __init__(self):
        # Configurar tema escuro para toda a aplicação
        ctk.set_appearance_mode("dark")
        
        # Inicializar backend AURALIS com sistema de agentes IA
        print("🚀 Inicializando backend AURALIS...")
        # Backend conectado APENAS ao Supabase
        self.backend = AURALISBackend()  # Sem mocks - apenas Supabase
        
        # Paleta de cores personalizada otimizada para tema escuro
        # Cores cuidadosamente selecionadas para boa visibilidade e acessibilidade
        self.cores = {
            "primaria": "#1E88E5",
            "secundaria": "#424242",
            "sucesso": "#43A047",
            "perigo": "#E53935",
            "alerta": "#FB8C00",
            "fundo": "#121212",
            "superficie": "#1E1E1E",
            "texto": "#E0E0E0",
            "texto_secundario": "#9E9E9E",
            "borda": "#2C2C2C",
            "audio_ativo": "#00E676",
            "audio_processando": "#2196F3",
            "audio_inativo": "#616161",
            "glow": "#00BCD4",
            "accent": "#FF4081"
        }
        
        # Janela principal - COM decorações no Linux para funcionar corretamente
        # Importante: manter decorações para garantir funcionalidade de entrada de texto
        self.janela = ctk.CTk()
        self.janela.title("AURALIS - Sistema de Reuniões")
        self.janela.geometry("320x240")
        self.janela.resizable(False, False)  # Tamanho fixo para consistência
        self.janela.configure(fg_color=self.cores["fundo"])
        
        # Estado do sistema - variáveis de controle principais
        self.usuario_logado = None      # Dados do usuário autenticado
        self.frame_atual = None         # Frame/tela atualmente visível
        self.gravando = False           # Status de gravação em andamento
        self.timer_ativo = False        # Controle do timer de gravação
        self.contexto_reuniao = None    # Contexto da reunião para a IA
        
        # Estado da interface de áudio - controla animações e interações
        self.audio_ativo = False        # Interface de áudio está ativa
        self.audio_estado = "idle"      # Estado: idle, recording, processing
        self.animacao_ativa = False     # Controle de animações de partículas
        
        # Centralizar janela na tela do usuário
        self.centralizar_janela()
        
        # Container principal - todas as telas são filhas deste container
        self.container_principal = ctk.CTkFrame(self.janela, fg_color=self.cores["fundo"])
        self.container_principal.pack(fill="both", expand=True)
        
        # Iniciar com tela de login - ponto de entrada do sistema
        self.mostrar_login()
    
    def centralizar_janela(self):
        """
        Centraliza a janela na tela do usuário.
        Calcula a posição baseada nas dimensões da tela.
        """
        self.janela.update_idletasks()
        largura = 320
        altura = 240
        x = (self.janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.janela.winfo_screenheight() // 2) - (altura // 2)
        self.janela.geometry(f"{largura}x{altura}+{x}+{y}")
    
    def executar(self):
        """Inicia o loop principal da interface gráfica"""
        self.janela.mainloop()
    
    def transicao_rapida(self, novo_frame_func):
        """
        Realiza transição rápida entre telas.
        
        Args:
            novo_frame_func: Função que cria a nova tela
        """
        if self.frame_atual:
            self.frame_atual.destroy()
        novo_frame_func()
    
    # ==================== TELA DE LOGIN ====================
    def mostrar_login(self):
        """Cria e exibe a tela de login do sistema"""
        self.frame_atual = ctk.CTkFrame(self.container_principal, fg_color=self.cores["fundo"])
        self.frame_atual.pack(fill="both", expand=True)
        
        # Container central para o formulário de login
        frame_central = ctk.CTkFrame(self.frame_atual, width=280, height=170, fg_color=self.cores["superficie"])
        frame_central.place(relx=0.5, rely=0.5, anchor="center")
        frame_central.pack_propagate(False)  # Manter tamanho fixo
        
        # Espaçamento superior para melhor alinhamento visual
        ctk.CTkFrame(frame_central, height=10, fg_color=self.cores["superficie"]).pack()
        
        # Campos de login
        # Campo de usuário
        ctk.CTkLabel(
            frame_central, 
            text="Usuário", 
            font=ctk.CTkFont(size=12),
            text_color=self.cores["texto_secundario"]
        ).pack(pady=(0, 2))
        
        self.entry_usuario = ctk.CTkEntry(
            frame_central, 
            width=220, 
            height=30,
            fg_color=self.cores["fundo"],
            border_color=self.cores["primaria"],
            placeholder_text="Digite seu nome"
        )
        self.entry_usuario.pack(pady=(0, 8))
        
        # Campo de senha
        ctk.CTkLabel(
            frame_central, 
            text="Senha", 
            font=ctk.CTkFont(size=12),
            text_color=self.cores["texto_secundario"]
        ).pack(pady=(0, 2))
        
        self.entry_senha = ctk.CTkEntry(
            frame_central, 
            width=220, 
            height=30,
            fg_color=self.cores["fundo"],
            border_color=self.cores["primaria"],
            placeholder_text="Digite sua senha",
            show="●"
        )
        self.entry_senha.pack(pady=(0, 12))
        
        # Botão entrar
        self.btn_login = ctk.CTkButton(
            frame_central,
            text="ENTRAR",
            width=220,
            height=40,
            command=self.fazer_login,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.cores["primaria"],
            hover_color="#1976D2"
        )
        self.btn_login.pack()
        
        # Permitir login com Enter na senha
        self.entry_senha.bind("<Return>", lambda e: self.fazer_login())
        
        # Focar no campo usuário após a janela estar completamente carregada
        self.janela.after(100, lambda: self.entry_usuario.focus_set())
    
    def fazer_login(self):
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get()
        
        if not usuario:
            return
        
        # Autenticar via backend
        user = self.backend.authenticate(usuario, senha)
        if user:
            self.usuario_logado = user
            self.transicao_rapida(self.mostrar_menu_principal)
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos", parent=self.janela)
            self.entry_senha.delete(0, "end")
    
    # ==================== MENU PRINCIPAL ====================
    def mostrar_menu_principal(self):
        self.frame_atual = ctk.CTkFrame(self.container_principal, fg_color=self.cores["fundo"])
        self.frame_atual.pack(fill="both", expand=True)
        
        # Cabeçalho
        frame_header = ctk.CTkFrame(self.frame_atual, height=35, fg_color=self.cores["superficie"])
        frame_header.pack(fill="x")
        frame_header.pack_propagate(False)
        
        ctk.CTkLabel(
            frame_header,
            text="Menu Principal",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.cores["texto"]
        ).pack(side="left", padx=15, pady=8)
        
        # Logout
        ctk.CTkButton(
            frame_header,
            text="◄",
            width=28,
            height=25,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=self.cores["texto_secundario"],
            hover_color=self.cores["secundaria"],
            command=self.fazer_logout
        ).pack(side="right", padx=8, pady=5)
        
        # Usuário
        ctk.CTkLabel(
            frame_header,
            text=self.usuario_logado.get('username', self.usuario_logado.get('usuario', 'Usuário')),
            font=ctk.CTkFont(size=10),
            text_color=self.cores["texto_secundario"]
        ).pack(side="right", padx=5)
        
        # Container para botões
        frame_botoes = ctk.CTkFrame(self.frame_atual, fg_color=self.cores["fundo"])
        frame_botoes.pack(fill="both", expand=True)
        
        # Botões
        botoes = [
            ("HISTÓRICO\nREUNIÕES", self.mostrar_historico, self.cores["secundaria"]),
            ("NOVA\nGRAVAÇÃO", self.mostrar_pre_gravacao, self.cores["sucesso"]),
            ("ASSISTENTE\nINTELIGENTE", self.mostrar_assistente, self.cores["primaria"])
        ]
        
        for i, (texto, comando, cor) in enumerate(botoes):
            btn = ctk.CTkButton(
                frame_botoes,
                text=texto,
                width=320,
                height=68,
                command=comando,
                font=ctk.CTkFont(size=15, weight="bold"),
                fg_color=cor,
                hover_color=cor,
                corner_radius=0,
                text_color=self.cores["texto"]
            )
            btn.pack(fill="both", expand=True)
            
            if i < len(botoes) - 1:
                linha = ctk.CTkFrame(frame_botoes, height=1, fg_color=self.cores["fundo"])
                linha.pack(fill="x")
    
    # ==================== HISTÓRICO ====================
    def mostrar_historico(self):
        self.transicao_rapida(self._criar_historico)
    
    def _criar_historico(self):
        self.frame_atual = ctk.CTkFrame(self.container_principal, fg_color=self.cores["fundo"])
        self.frame_atual.pack(fill="both", expand=True)
        
        self.criar_cabecalho_voltar("📋 Histórico de Reuniões")
        
        # Lista
        frame_lista = ctk.CTkScrollableFrame(
            self.frame_atual, 
            height=145,
            fg_color=self.cores["fundo"]
        )
        frame_lista.pack(fill="both", expand=True, padx=0, pady=0)
        
        reunioes = [
            ("Planejamento Q1", "15/01 14:00", "45 min"),
            ("Daily Standup", "14/01 10:00", "15 min"),
            ("Revisão Sprint", "12/01 15:30", "1h 20min"),
            ("Kickoff Projeto", "10/01 09:00", "2h"),
        ]
        
        for i, (titulo, data, duracao) in enumerate(reunioes):
            frame_item = ctk.CTkFrame(
                frame_lista, 
                height=55,
                fg_color=self.cores["superficie"]
            )
            frame_item.pack(fill="x", padx=10, pady=(5 if i == 0 else 0, 0))
            frame_item.pack_propagate(False)
            
            frame_info = ctk.CTkFrame(frame_item, fg_color="transparent")
            frame_info.pack(side="left", fill="both", expand=True, padx=(12, 0))
            
            ctk.CTkLabel(
                frame_info,
                text=titulo,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.cores["texto"],
                anchor="w"
            ).place(x=0, y=8)
            
            ctk.CTkLabel(
                frame_info,
                text=f"{data} • {duracao}",
                font=ctk.CTkFont(size=9),
                text_color=self.cores["texto_secundario"],
                anchor="w"
            ).place(x=0, y=28)
            
            btn_ver = ctk.CTkButton(
                frame_item,
                text="Ver",
                width=50,
                height=30,
                font=ctk.CTkFont(size=11),
                fg_color=self.cores["primaria"],
                command=lambda t=titulo, d=data, dur=duracao: self.mostrar_detalhes_reuniao(t, d, dur)
            )
            btn_ver.place(relx=0.85, rely=0.5, anchor="center")
            
            if i < len(reunioes) - 1:
                separator = ctk.CTkFrame(
                    frame_lista, 
                    height=1, 
                    fg_color=self.cores["secundaria"]
                )
                separator.pack(fill="x", padx=20, pady=0)
    
    def mostrar_detalhes_reuniao(self, titulo, data, duracao):
        self.transicao_rapida(lambda: self._criar_detalhes_reuniao(titulo, data, duracao))
    
    def _criar_detalhes_reuniao(self, titulo, data, duracao):
        self.frame_atual = ctk.CTkFrame(self.container_principal, fg_color=self.cores["fundo"])
        self.frame_atual.pack(fill="both", expand=True)
        
        # Cabeçalho
        frame_header = ctk.CTkFrame(self.frame_atual, height=35, fg_color=self.cores["superficie"])
        frame_header.pack(fill="x")
        frame_header.pack_propagate(False)
        
        ctk.CTkButton(
            frame_header,
            text="◄",
            width=30,
            height=25,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=self.cores["texto"],
            hover_color=self.cores["secundaria"],
            command=lambda: self.transicao_rapida(self._criar_historico)
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkLabel(
            frame_header,
            text="📄 Detalhes",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.cores["texto"]
        ).pack(side="left", padx=10, pady=8)
        
        # Botão analisar
        ctk.CTkButton(
            self.frame_atual,
            text="🤖 Analisar com IA",
            width=300,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.cores["primaria"],
            hover_color="#1976D2",
            command=lambda: self.analisar_com_ia(titulo)
        ).pack(padx=10, pady=(5, 5))
        
        # Info
        frame_info = ctk.CTkFrame(self.frame_atual, height=30, fg_color=self.cores["superficie"])
        frame_info.pack(fill="x", padx=10, pady=(0, 5))
        frame_info.pack_propagate(False)
        
        titulo_curto = titulo[:15] + "..." if len(titulo) > 15 else titulo
        info_text = f"{titulo_curto} • {data} • {duracao}"
        ctk.CTkLabel(
            frame_info,
            text=info_text,
            font=ctk.CTkFont(size=9),
            text_color=self.cores["texto_secundario"]
        ).pack(expand=True)
        
        # Transcrição
        ctk.CTkLabel(
            self.frame_atual,
            text="Transcrição:",
            font=ctk.CTkFont(size=11),
            text_color=self.cores["texto"]
        ).pack(anchor="w", padx=10, pady=(0, 2))
        
        text_transcricao = ctk.CTkTextbox(
            self.frame_atual,
            height=98,
            font=ctk.CTkFont(size=10),
            fg_color=self.cores["superficie"],
            wrap="word"
        )
        text_transcricao.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        transcricao = f"""Reunião: {titulo}
Data: {data} - Duração: {duracao}

PARTICIPANTES:
• {self.usuario_logado.get('username', self.usuario_logado.get('usuario', 'Usuário'))} (Organizador)
• João Silva (Desenvolvimento)
• Maria Santos (Design)
• Pedro Costa (Gestão)

PAUTA:
1. Revisão do Sprint anterior
2. Planejamento do próximo ciclo
3. Discussão de impedimentos
4. Definição de prioridades

PONTOS DISCUTIDOS:
• Objetivos do trimestre foram revisados e aprovados
• Alocação de recursos para o novo projeto
• Prazos definidos conforme cronograma
• Métricas de desempenho analisadas

DECISÕES TOMADAS:
• Aprovar novo orçamento de R$ 50.000
• Contratar 2 desenvolvedores até março
• Implementar nova metodologia ágil

AÇÕES PENDENTES:
• João: Preparar relatório técnico até sexta-feira
• Maria: Agendar reunião com cliente
• Pedro: Revisar documentação do projeto

PRÓXIMOS PASSOS:
• Reunião de acompanhamento em 15 dias
• Revisão mensal de métricas"""
        
        text_transcricao.insert("1.0", transcricao)
        text_transcricao.configure(state="disabled")
    
    def analisar_com_ia(self, titulo):
        self.contexto_reuniao = titulo
        self.transicao_rapida(self._criar_assistente)
    
    # ==================== PRÉ-GRAVAÇÃO ====================
    def mostrar_pre_gravacao(self):
        self.transicao_rapida(self._criar_pre_gravacao)
    
    def _criar_pre_gravacao(self):
        self.frame_atual = ctk.CTkFrame(self.container_principal, fg_color=self.cores["fundo"])
        self.frame_atual.pack(fill="both", expand=True)
        
        self.criar_cabecalho_voltar("🎙️ Nova Gravação")
        
        # Botões
        frame_btns = ctk.CTkFrame(self.frame_atual, height=36, fg_color=self.cores["fundo"])
        frame_btns.pack(fill="x", padx=10, pady=(2, 2))
        frame_btns.pack_propagate(False)
        
        inner_btns = ctk.CTkFrame(frame_btns, fg_color=self.cores["fundo"])
        inner_btns.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkButton(
            inner_btns,
            text="Cancelar",
            width=140,
            height=30,
            fg_color=self.cores["secundaria"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.transicao_rapida(self.mostrar_menu_principal)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            inner_btns,
            text="Iniciar",
            width=140,
            height=30,
            fg_color=self.cores["sucesso"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.iniciar_gravacao
        ).pack(side="left", padx=5)
        
        # Formulário
        frame_form = ctk.CTkFrame(self.frame_atual, fg_color=self.cores["superficie"])
        frame_form.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        
        ctk.CTkLabel(
            frame_form, 
            text="Título da Reunião", 
            font=ctk.CTkFont(size=11),
            text_color=self.cores["texto_secundario"]
        ).pack(pady=(8, 2))
        
        self.entry_titulo = ctk.CTkEntry(
            frame_form, 
            width=270,
            height=30,
            fg_color=self.cores["fundo"],
            border_color=self.cores["primaria"],
            placeholder_text="Ex: Reunião de Planejamento"
        )
        self.entry_titulo.pack(pady=(0, 8))
        
        ctk.CTkLabel(
            frame_form, 
            text="Observações (opcional)", 
            font=ctk.CTkFont(size=11),
            text_color=self.cores["texto_secundario"]
        ).pack(pady=(0, 2))
        
        self.text_obs = ctk.CTkTextbox(
            frame_form, 
            width=270,
            height=40,
            font=ctk.CTkFont(size=10),
            fg_color=self.cores["fundo"]
        )
        self.text_obs.pack(pady=(0, 8))
        
        self.entry_titulo.focus_set()
    
    def iniciar_gravacao(self):
        titulo = self.entry_titulo.get().strip()
        if not titulo:
            self.entry_titulo.configure(
                border_color=self.cores["perigo"], 
                border_width=2,
                placeholder_text="⚠️ Campo obrigatório"
            )
            self.entry_titulo.focus_set()
            self.janela.after(2000, lambda: self.entry_titulo.configure(
                border_color=self.cores["primaria"], 
                border_width=2,
                placeholder_text="Ex: Reunião de Planejamento"
            ))
            return
        
        self.dados_reuniao = {
            'titulo': titulo,
            'observacoes': self.text_obs.get("1.0", "end-1c")
        }
        
        self.transicao_rapida(self._criar_gravacao)
    
    # ==================== GRAVAÇÃO ====================
    def _criar_gravacao(self):
        self.frame_atual = ctk.CTkFrame(self.container_principal, fg_color=self.cores["fundo"])
        self.frame_atual.pack(fill="both", expand=True)
        
        frame_central = ctk.CTkFrame(self.frame_atual, fg_color=self.cores["superficie"])
        frame_central.pack(fill="both", expand=True, padx=10, pady=(5, 8))
        
        titulo_curto = self.dados_reuniao['titulo'][:25]
        if len(self.dados_reuniao['titulo']) > 25:
            titulo_curto += "..."
            
        ctk.CTkLabel(
            frame_central,
            text=titulo_curto,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.cores["texto"]
        ).pack(pady=(15, 10))
        
        self.label_rec = ctk.CTkLabel(
            frame_central,
            text="● REC",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.cores["perigo"]
        )
        self.label_rec.pack()
        
        self.label_timer = ctk.CTkLabel(
            frame_central,
            text="00:00",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color=self.cores["texto"]
        )
        self.label_timer.pack(pady=8)
        
        frame_controles = ctk.CTkFrame(frame_central, fg_color="transparent")
        frame_controles.pack(pady=12)
        
        self.btn_pausar = ctk.CTkButton(
            frame_controles,
            text="⏸",
            width=70,
            height=45,
            font=ctk.CTkFont(size=20),
            fg_color=self.cores["alerta"],
            command=self.pausar_gravacao
        )
        self.btn_pausar.pack(side="left", padx=5)
        
        ctk.CTkButton(
            frame_controles,
            text="⏹",
            width=70,
            height=45,
            font=ctk.CTkFont(size=20),
            fg_color=self.cores["sucesso"],
            command=self.parar_gravacao
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            frame_controles,
            text="✕",
            width=70,
            height=45,
            font=ctk.CTkFont(size=20),
            fg_color=self.cores["perigo"],
            command=self.cancelar_gravacao
        ).pack(side="left", padx=5)
        
        self.gravando = True
        self.pausado = False
        self.tempo_inicial = datetime.now()
        self.tempo_pausado = timedelta()
        self.timer_ativo = True
        self.atualizar_timer()
    
    def atualizar_timer(self):
        if self.timer_ativo and self.gravando and not self.pausado:
            tempo_total = datetime.now() - self.tempo_inicial - self.tempo_pausado
            minutos = int(tempo_total.total_seconds() // 60)
            segundos = int(tempo_total.total_seconds() % 60)
            
            self.label_timer.configure(text=f"{minutos:02d}:{segundos:02d}")
            self.janela.after(100, self.atualizar_timer)
    
    def pausar_gravacao(self):
        if not self.pausado:
            self.pausado = True
            self.momento_pausa = datetime.now()
            self.btn_pausar.configure(text="▶", fg_color=self.cores["sucesso"])
            self.label_rec.configure(text="⏸ PAUSADO", text_color=self.cores["alerta"])
        else:
            self.tempo_pausado += datetime.now() - self.momento_pausa
            self.pausado = False
            self.btn_pausar.configure(text="⏸", fg_color=self.cores["alerta"])
            self.label_rec.configure(text="● REC", text_color=self.cores["perigo"])
            self.atualizar_timer()
    
    def parar_gravacao(self):
        resposta = messagebox.askyesno(
            "Finalizar Gravação",
            "Deseja finalizar a gravação?\n\nA reunião será salva e processada.",
            parent=self.janela
        )
        
        if resposta:
            self.gravando = False
            self.timer_ativo = False
            
            messagebox.showinfo(
                "Sucesso", 
                "Gravação finalizada com sucesso!\n\nA transcrição está sendo processada.",
                parent=self.janela
            )
            self.transicao_rapida(self.mostrar_menu_principal)
    
    def cancelar_gravacao(self):
        resposta = messagebox.askyesno(
            "Cancelar Gravação",
            "Tem certeza que deseja cancelar?\n\nTodo o conteúdo gravado será perdido!",
            parent=self.janela
        )
        
        if resposta:
            self.gravando = False
            self.timer_ativo = False
            self.transicao_rapida(self.mostrar_menu_principal)
    
    # ==================== ASSISTENTE IA ====================
    def mostrar_assistente(self):
        self.transicao_rapida(self._criar_assistente)
    
    def _criar_assistente(self):
        self.frame_atual = ctk.CTkFrame(self.container_principal, fg_color=self.cores["fundo"])
        self.frame_atual.pack(fill="both", expand=True)
        
        self.criar_cabecalho_voltar("🤖 Assistente IA")
        
        self.text_chat = ctk.CTkTextbox(
            self.frame_atual,
            height=120,
            font=ctk.CTkFont(size=11),
            fg_color=self.cores["superficie"]
        )
        self.text_chat.pack(fill="both", expand=True, padx=5, pady=5)
        
        msg_inicial = "🤖 Olá! Como posso ajudá-lo?\n\n"
        if hasattr(self, 'contexto_reuniao') and self.contexto_reuniao:
            msg_inicial += f"📄 Analisando: {self.contexto_reuniao}\n\n"
            msg_inicial += "Posso criar resumo, listar ações ou insights.\n\n"
            self.contexto_reuniao = None
            
        self.text_chat.insert("end", msg_inicial)
        self.text_chat.configure(state="disabled")
        
        frame_entrada = ctk.CTkFrame(self.frame_atual, height=32, fg_color=self.cores["superficie"])
        frame_entrada.pack(fill="x", padx=5, pady=(0, 5))
        frame_entrada.pack_propagate(False)
        
        self.btn_audio = ctk.CTkButton(
            frame_entrada,
            text="🎤",
            width=32,
            height=24,
            font=ctk.CTkFont(size=14),
            fg_color=self.cores["secundaria"],
            hover_color=self.cores["primaria"],
            command=self.abrir_interface_audio
        )
        self.btn_audio.pack(side="left", padx=4)
        
        self.entry_chat = ctk.CTkEntry(
            frame_entrada,
            placeholder_text="Digite ou use o microfone...",
            font=ctk.CTkFont(size=10),
            fg_color=self.cores["fundo"],
            border_color=self.cores["primaria"],
            height=24
        )
        self.entry_chat.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        
        ctk.CTkButton(
            frame_entrada,
            text="➤",
            width=32,
            height=24,
            font=ctk.CTkFont(size=12),
            fg_color=self.cores["primaria"],
            command=self.enviar_mensagem
        ).pack(side="right", padx=4)
        
        self.entry_chat.bind("<Return>", lambda e: self.enviar_mensagem())
        self.entry_chat.focus_set()
    
    def _mostrar_processando(self):
        """Mostra indicador de processamento no chat"""
        self.text_chat.configure(state="normal")
        self.text_chat.insert("end", "🤖 Processando...\n")
        self.text_chat.configure(state="disabled")
        self.text_chat.see("end")
    
    def _resposta_ia_callback(self, resposta: str):
        """Callback para resposta da IA"""
        # Executar na thread principal da GUI
        self.janela.after(0, lambda: self._atualizar_chat_com_resposta(resposta))
    
    def _erro_ia_callback(self, erro: str):
        """Callback para erro no processamento"""
        self.janela.after(0, lambda: self._atualizar_chat_com_erro(erro))
    
    def _atualizar_chat_com_resposta(self, resposta: str):
        """Atualiza o chat com a resposta da IA"""
        self.text_chat.configure(state="normal")
        
        # Remover "Processando..."
        content = self.text_chat.get("1.0", "end-1c")
        lines = content.split('\n')
        if lines and "Processando..." in lines[-1]:
            # Remover última linha
            self.text_chat.delete("end-2l", "end")
        
        # Adicionar resposta
        self.text_chat.insert("end", f"🤖 {resposta}\n\n")
        self.text_chat.configure(state="disabled")
        self.text_chat.see("end")
        
        # Reabilitar entrada
        self.entry_chat.configure(state="normal")
        self.entry_chat.focus_set()
    
    def _atualizar_chat_com_erro(self, erro: str):
        """Atualiza o chat com mensagem de erro"""
        self.text_chat.configure(state="normal")
        
        # Remover "Processando..."
        content = self.text_chat.get("1.0", "end-1c")
        lines = content.split('\n')
        if lines and "Processando..." in lines[-1]:
            self.text_chat.delete("end-2l", "end")
        
        # Adicionar erro
        self.text_chat.insert("end", f"❌ Erro: {erro}\n\n")
        self.text_chat.configure(state="disabled")
        self.text_chat.see("end")
        
        # Reabilitar entrada
        self.entry_chat.configure(state="normal")
        self.entry_chat.focus_set()
    
    def enviar_mensagem(self):
        msg = self.entry_chat.get().strip()
        if not msg:
            return
        
        self.text_chat.configure(state="normal")
        self.text_chat.insert("end", f"👤 {msg}\n")
        self.text_chat.configure(state="disabled")
        self.text_chat.see("end")
        
        self.entry_chat.delete(0, "end")
        
        # Desabilitar entrada durante processamento
        self.entry_chat.configure(state="disabled")
        
        # Mostrar indicador de processamento
        self._mostrar_processando()
        
        # Processar mensagem via backend de forma assíncrona
        process_message_async(
            self.backend,
            msg,
            self._resposta_ia_callback,
            self._erro_ia_callback
        )
    
    # ==================== INTERFACE DE ÁUDIO COM CLIQUE ====================
    def abrir_interface_audio(self):
        """Abre interface de áudio em tela cheia com animação imediata"""
        # Criar nova tela completa para a animação
        self.frame_audio_full = ctk.CTkFrame(
            self.container_principal,
            fg_color=self.cores["fundo"]
        )
        self.frame_audio_full.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Canvas para partículas em tela cheia
        self.canvas_particulas = Canvas(
            self.frame_audio_full,
            width=320,
            height=240,
            bg=self.cores["fundo"],
            highlightthickness=0
        )
        self.canvas_particulas.pack(fill="both", expand=True)
        
        # Área de controle central
        control_frame = ctk.CTkFrame(
            self.frame_audio_full,
            fg_color="transparent"
        )
        control_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Botão circular clicável
        self.btn_microfone = ctk.CTkButton(
            control_frame,
            text="🎤",
            width=60,
            height=60,
            corner_radius=30,
            font=ctk.CTkFont(size=24),
            fg_color=self.cores["secundaria"],
            hover_color=self.cores["primaria"],
            command=self.alternar_gravacao
        )
        self.btn_microfone.pack()
        
        # Instrução
        self.label_instrucao = ctk.CTkLabel(
            control_frame,
            text="Clique para gravar",
            font=ctk.CTkFont(size=11),
            text_color=self.cores["texto_secundario"]
        )
        self.label_instrucao.pack(pady=(5, 0))
        
        # Botão X minimalista no canto
        self.btn_fechar = ctk.CTkButton(
            self.frame_audio_full,
            text="✕",
            width=40,
            height=40,
            font=ctk.CTkFont(size=18),
            fg_color="transparent",
            text_color=self.cores["texto_secundario"],
            hover_color=self.cores["superficie"],
            corner_radius=20,
            border_width=1,
            border_color=self.cores["borda"],
            command=self.fechar_audio
        )
        self.btn_fechar.place(x=270, y=10)
        
        # Estado
        self.audio_estado = "idle"
        self.animacao_ativa = True
        self.particulas = []
        
        # Iniciar animação
        self.animar_particulas()

    def alternar_gravacao(self):
        """Alterna entre estados de gravação ao clicar"""
        if self.audio_estado == "idle":
            # Iniciar gravação
            self.audio_estado = "recording"
            self.btn_microfone.configure(
                text="🔴",
                fg_color=self.cores["audio_ativo"]
            )
            self.label_instrucao.configure(text="Gravando... Clique para parar")
            
        elif self.audio_estado == "recording":
            # Parar gravação e processar
            self.audio_estado = "processing"
            self.btn_microfone.configure(
                text="⏳",
                fg_color=self.cores["audio_processando"],
                state="disabled"
            )
            self.label_instrucao.configure(text="Processando...")
            
            # Simular processamento
            self.janela.after(1500, self.processar_e_fechar)

    def animar_particulas(self):
        """Animação de partículas flutuantes"""
        if not self.animacao_ativa:
            return
        
        self.canvas_particulas.delete("all")
        
        # Centro da tela
        centro_x = 160
        centro_y = 120
        
        # Adicionar novas partículas
        if self.audio_estado == "recording" and random.random() > 0.7:
            self.particulas.append({
                'x': random.randint(50, 270),
                'y': 200,
                'vy': -random.uniform(1, 3),
                'size': random.uniform(2, 5),
                'life': 1.0
            })
        
        elif self.audio_estado == "processing" and random.random() > 0.5:
            # Partículas circulares ao redor do centro
            angulo = random.uniform(0, 2 * math.pi)
            raio = 40
            self.particulas.append({
                'x': centro_x + math.cos(angulo) * raio,
                'y': centro_y + math.sin(angulo) * raio,
                'vx': -math.cos(angulo) * 0.5,
                'vy': -math.sin(angulo) * 0.5,
                'size': 3,
                'life': 1.0
            })
        
        # Atualizar e desenhar partículas
        particulas_vivas = []
        for p in self.particulas:
            # Movimento
            p['x'] += p.get('vx', 0)
            p['y'] += p.get('vy', 0)
            p['life'] -= 0.02
            
            if p['life'] > 0:
                # Cor baseada no estado
                if self.audio_estado == "recording":
                    cor = self.cores["audio_ativo"]
                elif self.audio_estado == "processing":
                    cor = self.cores["audio_processando"]
                else:
                    cor = self.cores["audio_inativo"]
                
                # Aplicar transparência baseada na vida
                cor_alpha = self._ajustar_cor_alpha(cor, p['life'] * 0.6)
                
                # Desenhar partícula
                size = p['size'] * p['life']
                self.canvas_particulas.create_oval(
                    p['x'] - size, p['y'] - size,
                    p['x'] + size, p['y'] + size,
                    fill=cor_alpha, outline=""
                )
                
                particulas_vivas.append(p)
        
        self.particulas = particulas_vivas
        
        # Efeito glow no centro durante estados ativos
        if self.audio_estado in ["recording", "processing"]:
            for i in range(3):
                raio = 30 - i * 8
                alpha = 0.1 * (1 - i * 0.3)
                cor = self.cores["glow"] if self.audio_estado == "recording" else self.cores["audio_processando"]
                cor_glow = self._ajustar_cor_alpha(cor, alpha)
                
                self.canvas_particulas.create_oval(
                    centro_x - raio, centro_y - raio,
                    centro_x + raio, centro_y + raio,
                    fill=cor_glow, outline=""
                )
        
        self.janela.after(30, self.animar_particulas)

    def _ajustar_cor_alpha(self, cor_hex, alpha):
        """Simula transparência"""
        r = int(cor_hex[1:3], 16)
        g = int(cor_hex[3:5], 16)
        b = int(cor_hex[5:7], 16)
        
        fundo_r = int(self.cores["fundo"][1:3], 16)
        fundo_g = int(self.cores["fundo"][3:5], 16)
        fundo_b = int(self.cores["fundo"][5:7], 16)
        
        r = int(r * alpha + fundo_r * (1 - alpha))
        g = int(g * alpha + fundo_g * (1 - alpha))
        b = int(b * alpha + fundo_b * (1 - alpha))
        
        return f"#{r:02x}{g:02x}{b:02x}"

    def processar_e_fechar(self):
        """Processa e retorna resultado"""
        # Adicionar resposta
        self.text_chat.configure(state="normal")
        self.text_chat.insert("end", "🎤 [Comando de voz processado]\n")
        self.text_chat.insert("end", "🤖 Aqui está o resumo que você solicitou...\n\n")
        self.text_chat.configure(state="disabled")
        self.text_chat.see("end")
        
        # Fechar interface
        self.fechar_audio()

    def fechar_audio(self):
        """Fecha interface de áudio e volta para assistente"""
        self.animacao_ativa = False
        
        # Destruir frame de áudio
        self.frame_audio_full.destroy()
    
    # ==================== UTILIDADES ====================
    def criar_cabecalho_voltar(self, titulo):
        frame_header = ctk.CTkFrame(self.frame_atual, height=35, fg_color=self.cores["superficie"])
        frame_header.pack(fill="x")
        frame_header.pack_propagate(False)
        
        ctk.CTkButton(
            frame_header,
            text="◄",
            width=30,
            height=25,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=self.cores["texto"],
            hover_color=self.cores["secundaria"],
            command=lambda: self.transicao_rapida(self.mostrar_menu_principal)
        ).pack(side="left", padx=5, pady=5)
        
        ctk.CTkLabel(
            frame_header,
            text=titulo,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.cores["texto"]
        ).pack(side="left", padx=10, pady=8)
    
    def fazer_logout(self):
        if self.backend and self.usuario_logado:
            self.backend.logout()
        self.usuario_logado = None
        self.transicao_rapida(self.mostrar_login)

# ==================== INICIALIZAÇÃO ====================
if __name__ == "__main__":
    print("🚀 Iniciando Sistema - Versão Linux Corrigida...")
    print("📱 Interface: 320x240 pixels")
    print("🐧 Otimizado para Linux com entrada de texto funcionando")
    print("⚠️ Use Ctrl+C ou feche a janela para sair\n")
    
    app = SistemaTFT()
    app.executar()