from tkinter import Tk, filedialog
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps


janela = Tk()
janela.withdraw()

arquivo_pdf = filedialog.askopenfilename(
    title="Selecione a CNH em PDF",
    filetypes=[("Arquivos PDF", "*.pdf")],
)

janela.destroy()

if not arquivo_pdf:
    print("Nenhum arquivo selecionado.")
    raise SystemExit

with pymupdf.open(arquivo_pdf) as documento:
    pagina = documento[0]

    pix = pagina.get_pixmap(
        matrix=pymupdf.Matrix(3, 3),
        alpha=False,
    )

    imagem = Image.frombytes(
        "RGB",
        (pix.width, pix.height),
        pix.samples,
    )

    # Recorte inicial aproximado da região do nome.
    recorte = imagem.crop((150, 220, 1200, 430))

    destino = Path(__file__).parent / "recorte_nome.png"
    recorte.save(destino)

    print(f"Recorte salvo em: {destino}")