
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from docxtpl import DocxTemplate
import re


BASE_DIR = Path(__file__).resolve().parent.parent
MODELO = BASE_DIR / "modelos" / "contrato_base_variavel.docx"
PASTA_SAIDA = BASE_DIR / "contratos_gerados"


def somente_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))

def validar_cep(cep):
    digitos = somente_digitos(cep)
    return len(digitos) == 8


def formatar_cep(cep):
    digitos = somente_digitos(cep)

    if len(digitos) != 8:
        raise ValueError(
            "CEP inválido. Informe os 8 dígitos do CEP."
        )

    return f"{digitos[:5]}-{digitos[5:]}"


def validar_cpf(cpf):
    cpf = somente_digitos(cpf)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for tamanho in (9, 10):
        soma = sum(
            int(cpf[i]) * (tamanho + 1 - i)
            for i in range(tamanho)
        )
        digito = (soma * 10) % 11
        digito = 0 if digito == 10 else digito

        if digito != int(cpf[tamanho]):
            return False

    return True


def validar_cnpj(cnpj):
    cnpj = somente_digitos(cnpj)

    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def calcular_digito(base, pesos):
        soma = sum(
            int(numero) * peso
            for numero, peso in zip(base, pesos)
        )
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    primeiro = calcular_digito(
        cnpj[:12],
        [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    )

    segundo = calcular_digito(
        cnpj[:12] + primeiro,
        [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    )

    return cnpj[-2:] == primeiro + segundo


def formatar_cnpj(cnpj):
    digitos = somente_digitos(cnpj)

    if len(digitos) != 14:
        return cnpj.strip()

    return (
        f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/"
        f"{digitos[8:12]}-{digitos[12:]}"
    )


def formatar_cpf(cpf):
    digitos = somente_digitos(cpf)

    if len(digitos) != 11:
        return cpf.strip()

    return (
        f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-"
        f"{digitos[9:]}"
    )

def converter_valor(valor):
    texto = str(valor).strip().replace("R$", "").replace(" ", "")

    if not texto:
        raise ValueError("Informe o valor mensal.")

    if "," in texto:
       
        texto = texto.replace(".", "").replace(",", ".")
    elif texto.count(".") > 1:
        texto = texto.replace(".", "")

    try:
        numero = Decimal(texto)
    except InvalidOperation:
        raise ValueError(
            "Valor mensal inválido. Exemplo: 1500,00."
        )

    if not numero.is_finite() or numero < 0:
        raise ValueError("O valor deve ser positivo ou zero.")

    if numero != numero.quantize(Decimal("0.01")):
        raise ValueError("Informe no máximo duas casas decimais.")

    return numero.quantize(Decimal("0.01"))


def formatar_reais(valor):
    valor = converter_valor(valor)
    inteiro, centavos = f"{valor:.2f}".split(".")
    inteiro_formatado = f"{int(inteiro):,}".replace(",", ".")

    return f"{inteiro_formatado},{centavos}"


UNIDADES = [
    "zero", "um", "dois", "três", "quatro", "cinco",
    "seis", "sete", "oito", "nove"
]

DEZENAS = [
    "", "", "vinte", "trinta", "quarenta", "cinquenta",
    "sessenta", "setenta", "oitenta", "noventa"
]

DEZ_A_DEZENOVE = [
    "dez", "onze", "doze", "treze", "quatorze",
    "quinze", "dezesseis", "dezessete", "dezoito",
    "dezenove"
]

CENTENAS = [
    "", "cento", "duzentos", "trezentos", "quatrocentos",
    "quinhentos", "seiscentos", "setecentos",
    "oitocentos", "novecentos"
]


def numero_por_extenso(numero):
    if numero < 0 or numero > 999999:
        raise ValueError(
            "O valor inteiro deve estar entre 0 e 999.999."
        )

    if numero < 10:
        return UNIDADES[numero]

    if numero < 20:
        return DEZ_A_DEZENOVE[numero - 10]

    if numero < 100:
        dezena, unidade = divmod(numero, 10)
        if unidade == 0:
            return DEZENAS[dezena]
        return f"{DEZENAS[dezena]} e {UNIDADES[unidade]}"

    if numero == 100:
        return "cem"

    if numero < 1000:
        centena, resto = divmod(numero, 100)
        if resto == 0:
            return CENTENAS[centena]
        return f"{CENTENAS[centena]} e {numero_por_extenso(resto)}"

    milhar, resto = divmod(numero, 1000)

    if milhar == 1:
        texto_milhar = "mil"
    else:
        texto_milhar = f"{numero_por_extenso(milhar)} mil"

    if resto == 0:
        return texto_milhar

    if resto < 100 or resto % 100 == 0:
        return f"{texto_milhar} e {numero_por_extenso(resto)}"

    return f"{texto_milhar}, {numero_por_extenso(resto)}"


def valor_por_extenso(valor):
    numero = converter_valor(valor)

    reais = int(numero)
    centavos = int(numero * 100) % 100

    partes = []

    if reais > 0:
        nome_reais = "real" if reais == 1 else "reais"
        partes.append(
            f"{numero_por_extenso(reais)} {nome_reais}"
        )

    if centavos > 0:
        nome_centavos = "centavo" if centavos == 1 else "centavos"
        partes.append(
            f"{numero_por_extenso(centavos)} {nome_centavos}"
        )

    if reais == 0 and centavos == 0:
        return "zero reais"

    if reais > 0 and centavos > 0:
        return f"{partes[0]} e {partes[1]}"

    return partes[0]

MESES = [
    "janeiro", "fevereiro", "março", "abril",
    "maio", "junho", "julho", "agosto",
    "setembro", "outubro", "novembro", "dezembro"
]


def formatar_data_br(texto):
    """Valida a data e retorna no formato DD/MM/AAAA."""
    try:
        data = datetime.strptime(texto.strip(), "%d/%m/%Y")
    except ValueError:
        raise ValueError(
            "Data inválida. Informe no formato DD/MM/AAAA."
        )

    return data.strftime("%d/%m/%Y")


def data_por_extenso(texto):
    """Converte uma data para o formato 14 de outubro de 2026."""
    try:
        data = datetime.strptime(texto.strip(), "%d/%m/%Y")
    except ValueError:
        raise ValueError(
            "Data inválida. Informe no formato DD/MM/AAAA."
        )

    return (
        f"{data.day} de {MESES[data.month - 1]} "
        f"de {data.year}"
    )

def gerar_contrato(dados):
    """Valida os dados, preenche o modelo e salva um novo contrato."""

    campos_obrigatorios = {
        "nome_empresa": "Nome da empresa",
        "cnpj": "CNPJ",
        "endereco": "Endereço",
        "cep": "CEP",
        "representante": "Representante legal",
        "cpf_representante": "CPF do representante",
        "nacionalidade": "Nacionalidade",
        "profissao": "Profissão",
        "valor_mensal": "Valor mensal",
        "data_inicio": "Data de início",
        "data_assinatura": "Data de assinatura",
    }

    # 1. Verificar se todos os campos foram preenchidos
    for campo, descricao in campos_obrigatorios.items():
        valor = dados.get(campo)

        if valor is None or not str(valor).strip():
            raise ValueError(f"Preencha o campo: {descricao}.")

    # 2. Verificar se o modelo existe
    if not MODELO.exists():
        raise FileNotFoundError(
            f"Modelo de contrato não encontrado: {MODELO}"
        )

    # 3. Validar CNPJ e CPF
    if not validar_cnpj(dados["cnpj"]):
        raise ValueError("O CNPJ informado é inválido.")

    if not validar_cpf(dados["cpf_representante"]):
        raise ValueError("O CPF do representante é inválido.")

    # 4. Validar e formatar o valor mensal
    valor = converter_valor(dados["valor_mensal"])

    if valor > Decimal("999999.99"):
        raise ValueError(
            "Por enquanto, o valor máximo aceito é R$ 999.999,99."
        )

    valor_formatado = formatar_reais(valor)
    valor_extenso = valor_por_extenso(valor).capitalize()

    # 5. Validar as datas
    data_inicio = formatar_data_br(dados["data_inicio"])
    data_assinatura = data_por_extenso(
        dados["data_assinatura"]
    )

    # 6. Preparar os dados que serão inseridos no Word
    contexto = {
        "nome_empresa": str(dados["nome_empresa"]).strip(),
        "cnpj": formatar_cnpj(dados["cnpj"]),
        "endereco": str(dados["endereco"]).strip(),
        "cep": str(dados["cep"]).strip(),
        "representante": str(dados["representante"]).strip(),
        "cpf_representante": formatar_cpf(
            dados["cpf_representante"]
        ),
        "nacionalidade": str(dados["nacionalidade"]).strip(),
        "profissao": str(dados["profissao"]).strip(),
        "valor_mensal": valor_formatado,
        "valor_extenso": valor_extenso,
        "data_inicio": data_inicio,
        "data_assinatura_extenso": data_assinatura,
    }

    # 7. Criar a pasta de saída, caso ela não exista
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    # 8. Criar um nome de arquivo seguro e único
    nome_seguro = re.sub(
        r'[<>:"/\\|?*\x00-\x1f]',
        "",
        contexto["nome_empresa"]
    )
    nome_seguro = re.sub(r"\s+", "_", nome_seguro).strip("._ ")

    if not nome_seguro:
        nome_seguro = "Empresa"

    identificador = datetime.now().strftime("%Y%m%d_%H%M%S")

    destino = (
        PASTA_SAIDA
        / f"Contrato_{nome_seguro}_{identificador}.docx"
    )

    # 9. Preencher o modelo e salvar uma cópia
    documento = DocxTemplate(str(MODELO))
    documento.render(contexto)
    documento.save(str(destino))

    return destino
