from pathlib import Path
import pymupdf
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from tkinter import Tk, filedialog


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

BASE_DIR = Path(__file__).resolve().parent

janela = Tk()
janela.withdraw()

arquivo = filedialog.askopenfilename(
    title="Selecione a CNH em PDF",
    filetypes=[("Arquivos PDF", "*.pdf")],
)

janela.destroy()

if not arquivo:
    print("Nenhum arquivo selecionado.")
    raise SystemExit

with pymupdf.open(arquivo) as documento:
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

    # Recorte da região dos campos da CNH.
    recorte = imagem.crop((150, 220, 1200, 430))

    recorte = ImageOps.grayscale(recorte)
    recorte = ImageEnhance.Contrast(recorte).enhance(2)
    recorte = recorte.filter(ImageFilter.SHARPEN)

    caminho_imagem = BASE_DIR / "diagnostico_cnh_recorte.png"
    recorte.save(caminho_imagem)

    print("Recorte salvo em:", caminho_imagem)

    # Testa o OCR na imagem original e ampliada.
    recorte_ampliado = recorte.resize(
        (recorte.width * 2, recorte.height * 2)
    )

    for nome, imagem_teste in (
        ("ORIGINAL", recorte),
        ("AMPLIADO", recorte_ampliado),
    ):
        for configuracao in ("--psm 6", "--psm 7", "--psm 11"):
            texto = pytesseract.image_to_string(
                imagem_teste,
                lang="por+eng",
                config=configuracao,
            )

            print(f"\n--- {nome} | OCR {configuracao} ---")
            print(texto)

