import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread

from src.gerador_contrato import gerar_contrato
from src.consulta_cnpj import consultar_cnpj


def iniciar_interface():
    janela = tk.Tk()
    janela.title("Gerador de Contratos - Contty")
    janela.geometry("850x720")
    janela.minsize(650, 550)

    estilo = ttk.Style(janela)

    estilo.configure(
        "Titulo.TLabel",
        font=("Segoe UI", 18, "bold")
    )
    estilo.configure(
        "Subtitulo.TLabel",
        font=("Segoe UI", 10)
    )
    estilo.configure(
        "Secao.TLabel",
        font=("Segoe UI", 12, "bold")
    )
    estilo.configure(
        "Acao.TButton",
        font=("Segoe UI", 11, "bold")
    )

    # Área principal com rolagem
    container = ttk.Frame(janela)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(
        container,
        highlightthickness=0
    )

    barra = ttk.Scrollbar(
        container,
        orient="vertical",
        command=canvas.yview
    )

    conteudo = ttk.Frame(
        canvas,
        padding=24
    )

    janela_conteudo = canvas.create_window(
        (0, 0),
        window=conteudo,
        anchor="nw"
    )

    canvas.configure(
        yscrollcommand=barra.set
    )

    def atualizar_rolagem(event=None):
        canvas.configure(
            scrollregion=canvas.bbox("all")
        )

    def ajustar_largura(event):
        canvas.itemconfigure(
            janela_conteudo,
            width=event.width
        )

    conteudo.bind(
        "<Configure>",
        atualizar_rolagem
    )

    canvas.bind(
        "<Configure>",
        ajustar_largura
    )

    canvas.pack(
        side="left",
        fill="both",
        expand=True
    )

    barra.pack(
        side="right",
        fill="y"
    )

    # Rolagem com a rodinha do mouse no Windows
    def rolar_com_mouse(event):
        if event.delta:
            canvas.yview_scroll(
                -int(event.delta / 120),
                "units"
            )

    # Ativa a rolagem quando o cursor entra na área do formulário.
    # O bind_all permite rolar mesmo sobre campos e botões.
    def ativar_rolagem(event=None):
        janela.bind_all(
            "<MouseWheel>",
            rolar_com_mouse
        )

    def desativar_rolagem(event=None):
        janela.unbind_all("<MouseWheel>")

    canvas.bind(
        "<Enter>",
        ativar_rolagem
    )

    canvas.bind(
        "<Leave>",
        desativar_rolagem
    )

    # Cabeçalho
    ttk.Label(
        conteudo,
        text="Gerador de Contratos",
        style="Titulo.TLabel"
    ).pack(anchor="w")

    ttk.Label(
        conteudo,
        text="CONTTY FINANÇAS CORPORATIVAS LTDA",
        style="Subtitulo.TLabel"
    ).pack(
        anchor="w",
        pady=(2, 20)
    )

    campos = {}

    # Botão azul de consulta de CNPJ
    def criar_botao_consulta():
        botao = tk.Button(
            conteudo,
            text="🔎  Pesquisar CNPJ",
            font=("Segoe UI", 11, "bold"),
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            disabledforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=7,
            borderwidth=0
        )

        botao.pack(
            anchor="w",
            pady=(4, 14)
        )

        botao.bind(
            "<Enter>",
            lambda event: botao.config(
                bg="#1D4ED8"
            ) if botao["state"] != "disabled" else None
        )

        botao.bind(
            "<Leave>",
            lambda event: botao.config(
                bg="#2563EB"
            ) if botao["state"] != "disabled" else None
        )

        return botao

    # Criação de seções
    def adicionar_secao(titulo):
        ttk.Label(
            conteudo,
            text=titulo,
            style="Secao.TLabel"
        ).pack(
            anchor="w",
            pady=(12, 8)
        )

        ttk.Separator(conteudo).pack(
            fill="x",
            pady=(0, 12)
        )

    # Criação de campos
    def adicionar_campo(chave, rotulo, dica=""):
        ttk.Label(
            conteudo,
            text=rotulo
        ).pack(anchor="w")

        entrada = ttk.Entry(conteudo)

        entrada.pack(
            fill="x",
            pady=(4, 2)
        )

        if dica:
            ttk.Label(
                conteudo,
                text=dica,
                style="Subtitulo.TLabel"
            ).pack(
                anchor="w",
                pady=(0, 8)
            )
        else:
            ttk.Frame(
                conteudo,
                height=8
            ).pack()

        campos[chave] = entrada

    # Seção 1: Dados da empresa contratante
    adicionar_secao(
        "1. Dados da empresa contratante"
    )

    adicionar_campo(
        "nome_empresa",
        "Razão social"
    )

    adicionar_campo(
        "cnpj",
        "CNPJ",
        "Exemplo: 00.000.000/0000-00"
    )

    # Botão para consultar o CNPJ
    botao_consultar = criar_botao_consulta()

    def ao_consultar_cnpj():
        cnpj = campos["cnpj"].get().strip()

        if not cnpj:
            messagebox.showwarning(
                "CNPJ obrigatório",
                "Informe o CNPJ antes de consultar.",
                parent=janela
            )
            return

        botao_consultar.config(
            state="disabled",
            text="Consultando...",
            bg="#93C5FD",
            cursor="arrow"
        )

        def executar_consulta():
            try:
                dados_empresa = consultar_cnpj(cnpj)
                erro = None

            except Exception as exc:
                dados_empresa = None
                erro = str(exc)

            def finalizar_consulta():
                if not janela.winfo_exists():
                    return

                botao_consultar.config(
                    state="normal",
                    text="🔎  Pesquisar CNPJ",
                    bg="#2563EB",
                    cursor="hand2"
                )

                if erro:
                    messagebox.showerror(
                        "Erro na consulta",
                        erro,
                        parent=janela
                    )
                    return

                # Preenche os dados retornados pela API
                for chave in (
                    "nome_empresa",
                    "cnpj",
                    "endereco",
                    "cep"
                ):
                    valor = dados_empresa.get(
                        chave,
                        ""
                    )

                    if valor and chave in campos:
                        campos[chave].delete(
                            0,
                            tk.END
                        )

                        campos[chave].insert(
                            0,
                            str(valor)
                        )

                messagebox.showinfo(
                    "Consulta concluída",
                    "Dados cadastrais preenchidos com sucesso!\n\n"
                    "Confira as informações antes de gerar o contrato.",
                    parent=janela
                )

            janela.after(
                0,
                finalizar_consulta
            )

        Thread(
            target=executar_consulta,
            daemon=True
        ).start()

    botao_consultar.config(
        command=ao_consultar_cnpj
    )

    adicionar_campo(
        "endereco",
        "Endereço completo"
    )

    adicionar_campo(
        "cep",
        "CEP",
        "Exemplo: 40000-000"
    )

    # Seção 2: Representante legal
    adicionar_secao(
        "2. Representante legal"
    )

    adicionar_campo(
        "representante",
        "Nome completo"
    )

    adicionar_campo(
        "cpf_representante",
        "CPF do representante",
        "Exemplo: 000.000.000-00"
    )

    adicionar_campo(
        "nacionalidade",
        "Nacionalidade"
    )

    adicionar_campo(
        "profissao",
        "Profissão ou qualificação"
    )

    # Seção 3: Dados contratuais
    adicionar_secao(
        "3. Dados contratuais"
    )

    adicionar_campo(
        "valor_mensal",
        "Valor mensal (R$)",
        "Exemplo: 1500,00 ou 1.500,00"
    )

    adicionar_campo(
        "data_inicio",
        "Data de início",
        "Formato: DD/MM/AAAA"
    )

    adicionar_campo(
        "data_assinatura",
        "Data de assinatura",
        "Formato: DD/MM/AAAA"
    )

    # Ações
    ttk.Separator(conteudo).pack(
        fill="x",
        pady=(20, 16)
    )

    def ao_gerar():
        dados = {
            chave: entrada.get().strip()
            for chave, entrada in campos.items()
        }

        try:
            caminho = gerar_contrato(dados)

        except (ValueError, FileNotFoundError) as erro:
            messagebox.showerror(
                "Não foi possível gerar o contrato",
                str(erro),
                parent=janela
            )
            return

        except Exception as erro:
            messagebox.showerror(
                "Erro inesperado",
                "Ocorreu um erro ao gerar o documento:\n"
                f"{erro}",
                parent=janela
            )
            return

        messagebox.showinfo(
            "Contrato gerado com sucesso",
            f"O contrato foi criado!\n\n"
            f"Arquivo:\n{caminho}",
            parent=janela
        )

    botoes = ttk.Frame(conteudo)

    botoes.pack(
        fill="x",
        pady=(0, 12)
    )

    ttk.Button(
        botoes,
        text="Gerar contrato Word",
        style="Acao.TButton",
        command=ao_gerar
    ).pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 6)
    )

    ttk.Button(
        botoes,
        text="Sair",
        command=janela.destroy
    ).pack(
        side="left",
        padx=(6, 0),
        ipadx=20
    )

    janela.mainloop()