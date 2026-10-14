
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import re

from src.gerador_contrato import gerar_contrato
from src.consulta_cnpj import consultar_cnpj


def cnpj_valido(cnpj):
    """Valida o CNPJ e seus dígitos verificadores."""
    cnpj = re.sub(r"\D", "", str(cnpj))

    if len(cnpj) != 14:
        return False

    if cnpj == cnpj[0] * 14:
        return False

    def calcular_digito(numeros, pesos):
        soma = sum(
            int(numero) * peso
            for numero, peso in zip(numeros, pesos)
        )
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    primeiro_digito = calcular_digito(
        cnpj[:12],
        [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    )

    segundo_digito = calcular_digito(
        cnpj[:12] + primeiro_digito,
        [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    )

    return cnpj[-2:] == primeiro_digito + segundo_digito


def normalizar_endereco(endereco):
    """Remove espaços duplicados e quebras de linha."""
    return re.sub(r"\s+", " ", str(endereco or "")).strip()


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

    # ==========================================
    # ÁREA PRINCIPAL COM ROLAGEM
    # ==========================================

    container = ttk.Frame(janela)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, highlightthickness=0)

    barra = ttk.Scrollbar(
        container,
        orient="vertical",
        command=canvas.yview
    )

    conteudo = ttk.Frame(canvas, padding=24)

    janela_conteudo = canvas.create_window(
        (0, 0),
        window=conteudo,
        anchor="nw"
    )

    canvas.configure(yscrollcommand=barra.set)

    def atualizar_rolagem(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def ajustar_largura(event):
        canvas.itemconfigure(
            janela_conteudo,
            width=event.width
        )

    conteudo.bind("<Configure>", atualizar_rolagem)
    canvas.bind("<Configure>", ajustar_largura)

    canvas.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")

    # ==========================================
    # ROLAGEM COM A RODINHA DO MOUSE
    # ==========================================

    def rolar_com_mouse(event):
        if event.delta:
            canvas.yview_scroll(
                -int(event.delta / 120),
                "units"
            )

    def ativar_rolagem(event=None):
        janela.bind_all("<MouseWheel>", rolar_com_mouse)

    def desativar_rolagem(event=None):
        janela.unbind_all("<MouseWheel>")

    canvas.bind("<Enter>", ativar_rolagem)
    canvas.bind("<Leave>", desativar_rolagem)

    # ==========================================
    # CABEÇALHO
    # ==========================================

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

    # ==========================================
    # SEÇÕES E CAMPOS
    # ==========================================

    def adicionar_secao(titulo):
        ttk.Label(
            conteudo,
            text=titulo,
            style="Secao.TLabel"
        ).pack(anchor="w", pady=(12, 8))

        ttk.Separator(conteudo).pack(
            fill="x",
            pady=(0, 12)
        )

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

    # ==========================================
    # DADOS DA EMPRESA
    # ==========================================

    adicionar_secao("1. Dados da empresa contratante")

    adicionar_campo("nome_empresa", "Razão social")

    adicionar_campo(
        "cnpj",
        "CNPJ",
        "Exemplo: 00.000.000/0000-00"
    )

    botao_consultar = tk.Button(
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
    botao_consultar.pack(anchor="w", pady=(4, 14))

    def ao_consultar_cnpj():
        cnpj = campos["cnpj"].get().strip()
        cnpj_limpo = re.sub(r"\D", "", cnpj)

        if not cnpj_limpo:
            messagebox.showwarning(
                "CNPJ obrigatório",
                "Informe o CNPJ antes de consultar.",
                parent=janela
            )
            return

        if not cnpj_valido(cnpj_limpo):
            messagebox.showwarning(
                "CNPJ inválido",
                "Confira os 14 dígitos do CNPJ.",
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
            dados_empresa = None
            erro = None

            try:
                dados_empresa = consultar_cnpj(cnpj_limpo)
            except Exception as exc:
                erro = str(exc)

            def finalizar_consulta():
                try:
                    if not janela.winfo_exists():
                        return
                except tk.TclError:
                    return

                botao_consultar.config(
                    state="normal",
                    text="🔎  Pesquisar CNPJ",
                    bg="#2563EB",
                    cursor="hand2"
                )

                if erro:
                    messagebox.showerror(
                        "Falha na consulta",
                        f"{erro}\n\n"
                        "Verifique o CNPJ ou tente novamente mais tarde.",
                        parent=janela
                    )
                    return

                # Campos que podem ser preenchidos pela API.
                campos_consulta = (
                    "nome_empresa",
                    "cnpj",
                    "endereco",
                    "cep",
                    "representante",
                    "cpf_representante",
                    "cnh_representante",
                    "nacionalidade",
                    "profissao",
                )

                for chave in campos_consulta:
                    valor = dados_empresa.get(chave, "")

                    if not valor or chave not in campos:
                        continue

                    if chave == "endereco":
                        valor = normalizar_endereco(valor)

                    campos[chave].delete(0, tk.END)
                    campos[chave].insert(0, str(valor))

                messagebox.showinfo(
                    "Consulta concluída",
                    "Dados disponíveis preenchidos com sucesso!\n\n"
                    "Confira os dados do representante e da empresa "
                    "antes de gerar o contrato.",
                    parent=janela
                )

            try:
                janela.after(0, finalizar_consulta)
            except tk.TclError:
                pass

        Thread(
            target=executar_consulta,
            daemon=True
        ).start()

    botao_consultar.config(command=ao_consultar_cnpj)

    adicionar_campo("endereco", "Endereço completo")

    adicionar_campo(
        "cep",
        "CEP",
        "Exemplo: 40000-000"
    )

    # ==========================================
    # REPRESENTANTE LEGAL
    # ==========================================

    adicionar_secao("2. Representante legal")

    adicionar_campo("representante", "Nome completo")

    adicionar_campo(
        "cpf_representante",
        "CPF do representante",
        "Exemplo: 000.000.000-00"
    )

    adicionar_campo(
        "cnh_representante",
        "CNH do representante (opcional)"
    )

    adicionar_campo("nacionalidade", "Nacionalidade")

    adicionar_campo(
        "profissao",
        "Profissão ou qualificação",
        "A profissão será preenchida como Empresário pela consulta."
    )

    # ==========================================
    # DADOS CONTRATUAIS
    # ==========================================

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

    # ==========================================
    # GERAÇÃO DO CONTRATO
    # ==========================================

    ttk.Separator(conteudo).pack(
        fill="x",
        pady=(20, 16)
    )

    def ao_gerar():
        dados = {
            chave: entrada.get().strip()
            for chave, entrada in campos.items()
        }

        if dados.get("endereco"):
            dados["endereco"] = normalizar_endereco(
                dados["endereco"]
            )

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
            f"O contrato foi criado!\n\nArquivo:\n{caminho}",
            parent=janela
        )

    botoes = ttk.Frame(conteudo)
    botoes.pack(fill="x", pady=(0, 12))

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
    ).pack(side="left", padx=(6, 0), ipadx=20)

    janela.mainloop()


if __name__ == "__main__":
    iniciar_interface()
