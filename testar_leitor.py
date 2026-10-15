from tkinter import Tk, filedialog

from src.leitor_documentos import ler_documento


def main():
    janela = Tk()
    janela.withdraw()

    arquivo_pdf = filedialog.askopenfilename(
        title="Selecione a CNH em PDF",
        filetypes=[("Arquivos PDF", "*.pdf")],
    )

    janela.destroy()

    if not arquivo_pdf:
        print("Nenhum arquivo foi selecionado.")
        return

    try:
        resultado = ler_documento(arquivo_pdf)

        print("\n--- DADOS IDENTIFICADOS ---")
        print(
            "Nome:",
            resultado.get("nome_representante") or "Não identificado",
        )
        print(
            "CPF:",
            resultado.get("cpf_representante") or "Não identificado",
        )
        print(
            "Data de nascimento:",
            resultado.get("data_nascimento") or "Não identificada",
        )

    except Exception as erro:
        print(f"Erro ao ler o documento: {erro}")


if __name__ == "__main__":
    main()