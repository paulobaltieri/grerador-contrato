from pathlib import Path

import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

arquivo = Path(__file__).parent / "nome_cnh.png"

if not arquivo.exists():
    raise FileNotFoundError(
        f"Imagem não encontrada: {arquivo}"
    )

imagem = Image.open(arquivo)
imagem = ImageOps.grayscale(imagem)
imagem = ImageEnhance.Contrast(imagem).enhance(2)
imagem = imagem.filter(ImageFilter.SHARPEN)

imagem = imagem.resize(
    (imagem.width * 3, imagem.height * 3)
)

texto = pytesseract.image_to_string(
    imagem,
    lang="por+eng",
    config="--psm 7",
)

print("Nome reconhecido:")
print(repr(texto.strip()))