import pymupdf
import pytesseract
from pathlib import Path
from tkinter import Tk, filedialog
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

janela = Tk()
janela.withdraw()

arquivo = filedialog.askopenfilename(
    title="Selecione o PDF da CNH",
    filetypes=[("Arquivos PDF", "*.pdf")],
)

janela.destroy()

if not arquivo:
    print("Nenhum PDF selecionado.")
    raise SystemExit

with pymupdf.open(arquivo) as documento:
    for numero_pagina, pagina in enumerate(documento, start=1):
        print(f"\n--- PÁGINA {numero_pagina} ---")

        pix = pagina.get_pixmap(
            matrix=pymupdf.Matrix(3, 3),
            alpha=False,
        )

        imagem = Image.frombytes(
            "RGB",
            (pix.width, pix.height),
            pix.samples,
        )

        imagem = ImageOps.grayscale(imagem)
        imagem = ImageEnhance.Contrast(imagem).enhance(1.6)
        imagem = imagem.filter(ImageFilter.SHARPEN)

        dados = pytesseract.image_to_data(
            imagem,
            lang="por+eng",
            config="--psm 11",
            output_type=pytesseract.Output.DICT,
        )

        print("\nPALAVRAS COM NÚMEROS OU RÓTULOS RELEVANTES:")

        for i, texto in enumerate(dados["text"]):
            texto = texto.strip()

            if not texto:
                continue

            tem_numero = any(caractere.isdigit() for caractere in texto)

            relevante = any(
                termo in texto.casefold()
                for termo in (
                    "cpf",
                    "registro",
                    "nacionalidade",
                    "brasileiro",
                    "identidade",
                )
            )

            if tem_numero or relevante:
                print(
                    f"Texto={texto!r} | "
                    f"Posição=({dados['left'][i]}, "
                    f"{dados['top'][i]}, "
                    f"{dados['width'][i]}, "
                    f"{dados['height'][i]}) | "
                    f"Confiança={dados['conf'][i]}"
                )
