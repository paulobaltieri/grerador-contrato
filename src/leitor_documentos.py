
import re
from datetime import datetime
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


# Caminho do Tesseract instalado no Windows.
CAMINHO_TESSERACT = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

if CAMINHO_TESSERACT.exists():
    pytesseract.pytesseract.tesseract_cmd = str(
        CAMINHO_TESSERACT
    )


def preparar_imagem(imagem):
    """Melhora a imagem antes do reconhecimento por OCR."""
    imagem = ImageOps.grayscale(imagem)
    imagem = ImageEnhance.Contrast(imagem).enhance(2)
    imagem = imagem.filter(ImageFilter.SHARPEN)
    return imagem


def executar_ocr_pagina(pagina):
    """Extrai texto de uma página do PDF usando OCR."""
    pix = pagina.get_pixmap(
        matrix=pymupdf.Matrix(3, 3),
        alpha=False,
    )

    imagem = Image.frombytes(
        "RGB",
        (pix.width, pix.height),
        pix.samples,
    )

    imagem = preparar_imagem(imagem)

    return pytesseract.image_to_string(
        imagem,
        lang="por+eng",
        config="--psm 11",
    ).strip()


def ler_recorte_campos(pagina):
    """Executa OCR em um recorte de campos da CNH."""
    pix = pagina.get_pixmap(
        matrix=pymupdf.Matrix(3, 3),
        alpha=False,
    )

    imagem = Image.frombytes(
        "RGB",
        (pix.width, pix.height),
        pix.samples,
    )

    # Recorte utilizado nos testes da CNH.
    recorte = imagem.crop((350, 430, 900, 570))
    recorte = preparar_imagem(recorte)

    ampliado = recorte.resize(
        (recorte.width * 2, recorte.height * 2)
    )

    return pytesseract.image_to_string(
        ampliado,
        lang="por+eng",
        config="--psm 6",
    ).strip()


def limpar_numero(valor):
    """Mantém somente os dígitos."""
    return re.sub(r"\D", "", valor or "")


def validar_cpf(cpf):
    """Valida os dígitos verificadores de um CPF."""
    cpf = limpar_numero(cpf)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    numeros = [int(digito) for digito in cpf]

    soma = sum(
        numeros[i] * (10 - i)
        for i in range(9)
    )

    digito1 = (soma * 10) % 11

    if digito1 == 10:
        digito1 = 0

    if numeros[9] != digito1:
        return False

    soma = sum(
        numeros[i] * (11 - i)
        for i in range(10)
    )

    digito2 = (soma * 10) % 11

    if digito2 == 10:
        digito2 = 0

    return numeros[10] == digito2


def encontrar_cpf(texto):
    """Procura o CPF identificado no texto extraído."""
    padrao_rotulado = re.compile(
        r"\bCPF\b\s*[:\-]?\s*"
        r"(\d{3}\.?\d{3}\.?\d{3}[- ]?\d{2})",
        re.IGNORECASE,
    )

    correspondencia = padrao_rotulado.search(texto)

    if correspondencia:
        cpf = limpar_numero(correspondencia.group(1))

        if validar_cpf(cpf):
            return cpf

    # Alternativa: aceita somente um CPF válido e único.
    padrao_cpf = (
        r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}[- ]?\d{2}(?!\d)"
    )

    candidatos = re.findall(padrao_cpf, texto)

    validos = list(dict.fromkeys(
        limpar_numero(candidato)
        for candidato in candidatos
        if validar_cpf(candidato)
    ))

    return validos[0] if len(validos) == 1 else ""


def encontrar_nome_mrz(texto):
    """
    Tenta extrair o nome da zona de leitura automática da CNH.
    Exemplo de formato: NOME<<SOBRENOME<OUTRO<SOBRENOME
    """
    for linha in texto.splitlines():
        linha = linha.upper().strip()
        linha = (
            linha.replace("«", "<")
            .replace("‹", "<")
            .replace("＜", "<")
        )

        # Remove espaços inseridos pelo OCR.
        linha = re.sub(r"\s+", "", linha)

        # A linha do nome deve conter somente letras e "<".
        if not re.fullmatch(r"[A-Z<]{8,}", linha):
            continue

        if linha.count("<") < 2:
            continue

        nome = re.sub(r"<+", " ", linha).strip()
        palavras = nome.split()

        if len(palavras) < 3:
            continue

        if not all(palavra.isalpha() for palavra in palavras):
            continue

        # Evita selecionar cabeçalhos comuns.
        bloqueios = {
            "REPUBLICA",
            "FEDERATIVA",
            "MINISTERIO",
            "CARTEIRA",
            "NACIONAL",
            "HABILITACAO",
            "DRIVER",
            "LICENSE",
            "PERMISO",
            "CONDUCCION",
        }

        if any(palavra in bloqueios for palavra in palavras):
            continue

        return nome.title()

    return ""


def nome_parece_valido(nome):
    """Verifica se uma linha tem características de nome completo."""
    palavras = nome.split()

    if len(palavras) < 3 or len(nome) < 10:
        return False

    bloqueios = (
        "REPÚBLICA",
        "FEDERATIVA",
        "MINISTÉRIO",
        "TRANSPORTES",
        "SECRETARIA",
        "NACIONAL",
        "HABILITAÇÃO",
        "DRIVER LICENSE",
        "PERMISO",
        "NASCIMENTO",
        "NACIONALIDADE",
        "BRASILEIRO",
        "IDENTIDADE",
        "EMISSOR",
        "OBSERVACOES",
        "ASSINADO",
        "DIGITALMENTE",
        "DEPARTAMENTO",
        "ESTADUAL",
        "TRÂNSITO",
        "QR CODE",
    )

    if any(bloqueio in nome for bloqueio in bloqueios):
        return False

    if sum(
        len(palavra) >= 2 for palavra in palavras
    ) < 3:
        return False

    return all(palavra.isalpha() for palavra in palavras)


def encontrar_nome(texto):
    """Tenta encontrar o nome no texto convencional da CNH."""
    linhas = [
        " ".join(linha.split()).strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    # Primeiro, procura nas linhas próximas ao título da CNH.
    for i, linha in enumerate(linhas):
        if "CARTEIRA NACIONAL DE HABILITAÇÃO" in linha.upper():
            for candidata in linhas[i + 1:i + 12]:
                candidata = re.sub(
                    r"[^A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ ]",
                    "",
                    candidata.upper(),
                )

                candidata = " ".join(candidata.split())

                if nome_parece_valido(candidata):
                    return candidata.title()

    # Alternativa: verifica as demais linhas.
    for linha in linhas:
        candidata = re.sub(
            r"[^A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ ]",
            "",
            linha.upper(),
        )

        candidata = " ".join(candidata.split())

        if nome_parece_valido(candidata):
            return candidata.title()

    return ""


def encontrar_data_nascimento(texto):
    """Extrai e valida a data de nascimento."""
    padrao = re.compile(
        r"DATA,\s*LOCAL\s*E\s*UF\s*DE\s*NASCIMENTO"
        r"\s*[:\-]?\s*"
        r"(\d{2}/\d{2}/\d{4})",
        re.IGNORECASE,
    )

    correspondencia = padrao.search(texto)

    if not correspondencia:
        return ""

    data = correspondencia.group(1)

    try:
        datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        return ""

    return data


def ler_regiao_nome(pagina):
    """Executa OCR em uma região da imagem da CNH."""
    pix = pagina.get_pixmap(
        matrix=pymupdf.Matrix(3, 3),
        alpha=False,
    )

    imagem = Image.frombytes(
        "RGB",
        (pix.width, pix.height),
        pix.samples,
    )

    recorte = imagem.crop((150, 220, 1200, 430))

    faixa_nome = recorte.crop(
        (
            0,
            0,
            recorte.width,
            int(recorte.height * 0.55),
        )
    )

    faixa_nome = preparar_imagem(faixa_nome)

    faixa_nome = faixa_nome.resize(
        (faixa_nome.width * 2, faixa_nome.height * 2)
    )

    return pytesseract.image_to_string(
        faixa_nome,
        lang="por+eng",
        config="--psm 7",
    ).strip()


def ler_documento(caminho_pdf):
    """
    Lê uma CNH em PDF e retorna:
    - texto extraído;
    - nome do representante;
    - CPF do representante;
    - data de nascimento.
    """
    caminho = Path(caminho_pdf)

    if not caminho.is_file():
        raise FileNotFoundError(
            "O arquivo PDF não foi encontrado."
        )

    if caminho.suffix.lower() != ".pdf":
        raise ValueError("Selecione um arquivo PDF.")

    try:
        textos = []

        with pymupdf.open(caminho) as documento:
            for pagina in documento:
                texto_pdf = pagina.get_text("text").strip()
                texto_ocr = executar_ocr_pagina(pagina)
                texto_campos = ler_recorte_campos(pagina)

                partes = [
                    parte
                    for parte in (
                        texto_pdf,
                        texto_ocr,
                        texto_campos,
                    )
                    if parte
                ]

                textos.append("\n".join(partes))

        texto = "\n".join(textos)

    except Exception as erro:
        raise RuntimeError(
            f"Não foi possível ler o PDF: {erro}"
        ) from erro

    # Prioriza a MRZ; se falhar, tenta o OCR convencional.
    nome = encontrar_nome_mrz(texto)

    if not nome:
        nome = encontrar_nome(texto)

    return {
        "texto": texto,
        "nome_representante": nome,
        "cpf_representante": encontrar_cpf(texto),
        "data_nascimento": encontrar_data_nascimento(texto),
    }
