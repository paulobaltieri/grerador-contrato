
import tkinter as tk
from tkinter import ttk, messagebox
from src.gerador_contrato import gerar_contrato


def iniciar_interface():
    janela = tk.Tk()
    janela.title("Gerador de Contratos - Contty")
    janela.geometry("850x720")
    janela.minsize(650, 550)

    estilo = ttk.Style(janela)
    estilo.configure("Titulo.TLabel", font=("Segoe UI", 18, "bold"))
    estilo.configure("Subtitulo.TLabel", font=("Segoe UI", 10))
    estilo.configure("Secao.TLabel", font=("Segoe UI", 12, "bold"))
    estilo.configure("Acao.TButton", font=("Segoe UI", 11, "bold"))

    # Área principal com rolagem vertical
    container = ttk.Frame(janela)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, highlightthickness=0)
    barra = ttk.Scrollbar(
        container, orient="vertical", command=canvas.yview
    )
    conteudo = ttk.Frame(canvas, padding=24)

    janela_conteudo = canvas.create_window(
        (0, 0), window=conteudo, anchor="nw"
    )

    canvas.configure(yscrollcommand=barra.set)

    def atualizar_rolagem(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def ajustar_largura(event):
        canvas.itemconfigure(janela_conteudo, width=event.width)

    conteudo.bind("<Configure>", atualizar_rolagem)
    canvas.bind("<Configure>", ajustar_largura)

    canvas.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")

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
    ).pack(anchor="w", pady=(2, 20))

    campos = {}

    def adicionar_secao(titulo):
        ttk.Label(
            conteudo,
            text=titulo,
            style="Secao.TLabel"
        ).pack(anchor="w", pady=(12, 8))

        separador = ttk.Separator(conteudo)
        separador.pack(fill="x", pady=(0, 12))

    def adicionar_campo(chave, rotulo, dica=""):
        ttk.Label(conteudo, text=rotulo).pack(anchor="w")

        entrada = ttk.Entry(conteudo)
        entrada.pack(fill="x", pady=(4, 2))

        if dica:
            ttk.Label(
                conteudo,
                text=dica,
                style="Subtitulo.TLabel"
            ).pack(anchor="w", pady=(0, 8))
        else:
            ttk.Frame(conteudo, height=8).pack()

        campos[chave] = entrada

    # Seção 1
    adicionar_secao("1. Dados da empresa contratante")

    adicionar_campo("nome_empresa", "Razão social")
    adicionar_campo("cnpj", "CNPJ", "Exemplo: 00.000.000/0000-00")
    adicionar_campo("endereco", "Endereço completo")
    adicionar_campo("cep", "CEP", "Exemplo: 40000-000")

    # Seção 2
    adicionar_secao("2. Representante legal")

    adicionar_campo("representante", "Nome completo")
    adicionar_campo(
        "cpf_representante",
        "CPF do representante",
        "Exemplo: 000.000.000-00"
    )
    adicionar_campo("nacionalidade", "Nacionalidade")
    adicionar_campo("profissao", "Profissão ou qualificação")

    # Seção 3
    adicionar_secao("3. Dados contratuais")

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
    ttk.Separator(conteudo).pack(fill="x", pady=(20, 16))

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
                f"Ocorreu um erro ao gerar o documento:\n{erro}",
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
    botoes.pack(fill="x", pady=(0, 12))

    ttk.Button(
        botoes,
        text="Gerar contrato Word",
        style="Acao.TButton",
        command=ao_gerar
    ).pack(side="left", fill="x", expand=True, padx=(0, 6))

    ttk.Button(
        botoes,
        text="Sair",
        command=janela.destroy
    ).pack(side="left", padx=(6, 0), ipadx=20)

    janela.mainloop()
