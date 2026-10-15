from tkinter import Tk, filedialog
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


CAMINHO_TESSERACT = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
pytesseract.pytesseract.tesseract_cmd = CAMINHO_TESSERACT


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

# Salva a página inteira para conferir as dimensões.
pasta = Path(__file__).resolve().parent
imagem.save(pasta / "pagina_cnh_diagnostico.png")

# Recorte ampliado da região que estamos investigando.
recorte = imagem.crop((150, 220, 1200, 400))
recorte.save(pasta / "recorte_nome_diagnostico.png")

faixas = {
    "faixa_superior": (0.00, 0.40),
    "faixa_central": (0.20, 0.70),
    "faixa_ampla": (0.00, 0.75),
}

for nome_faixa, (inicio, fim) in faixas.items():
    y1 = int(recorte.height * inicio)
    y2 = int(recorte.height * fim)

    faixa = recorte.crop((0, y1, recorte.width, y2))
    faixa = ImageOps.grayscale(faixa)
    faixa = ImageEnhance.Contrast(faixa).enhance(2)
    faixa = faixa.filter(ImageFilter.SHARPEN)
    faixa = faixa.resize(
        (faixa.width * 2, faixa.height * 2)
    )

    texto = pytesseract.image_to_string(
        faixa,
        lang="por+eng",
        config="--psm 6",
    ).strip()

    print(f"\n--- {nome_faixa} ---")
    print(repr(texto))

print("\nImagens salvas na pasta do projeto:")
print(pasta / "pagina_cnh_diagnostico.png")
print(pasta / "recorte_nome_diagnostico.png")