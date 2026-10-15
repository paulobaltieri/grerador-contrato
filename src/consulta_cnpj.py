import re
import requests


API_OPENCNPJ = "https://api.opencnpj.org/{}"
API_KITANA = "https://kitana.opencnpj.com/cnpj/{}"

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "ConttyGeradorContratos/1.0",
}


def consultar_json(url):
    resposta = requests.get(
        url,
        timeout=20,
        headers=HEADERS,
    )
    resposta.raise_for_status()
    return resposta.json()


def identificar_administrador(socios):
    """Retorna um nome quando há qualificação de administrador."""
    if not isinstance(socios, list):
        return ""

    administradores = []

    for socio in socios:
        if not isinstance(socio, dict):
            continue

        nome = (
            socio.get("nome_socio")
            or socio.get("nomeSocio")
            or ""
        ).strip()

        qualificacao = (
            socio.get("qualificacao_socio")
            or socio.get("descricao")
            or ""
        ).strip().casefold()

        if nome and "administrador" in qualificacao:
            administradores.append(nome)

    # Só sugere automaticamente quando há um único administrador
    # identificável. Não escolhe arbitrariamente entre vários.
    nomes_unicos = list(dict.fromkeys(administradores))

    if len(nomes_unicos) == 1:
        return nomes_unicos[0]

    return ""


def consultar_cnpj(cnpj):
    cnpj = re.sub(r"\D", "", str(cnpj))

    if len(cnpj) != 14:
        raise ValueError("Informe um CNPJ com 14 dígitos.")

    try:
        dados = consultar_json(API_OPENCNPJ.format(cnpj))

    except requests.Timeout:
        raise ConnectionError(
            "A consulta demorou demais. Tente novamente."
        )

    except requests.HTTPError as erro:
        status = erro.response.status_code if erro.response else None

        if status == 404:
            raise ValueError("CNPJ não encontrado na consulta.")

        if status == 429:
            raise ConnectionError(
                "Limite de consultas atingido. Tente mais tarde."
            )

        raise ConnectionError(
            f"Erro HTTP na consulta do CNPJ: {erro}"
        )

    except requests.RequestException as erro:
        raise ConnectionError(
            f"Falha na comunicação com a API: {erro}"
        )

    except ValueError:
        raise ConnectionError(
            "A API retornou uma resposta inválida."
        )

    nome_empresa = dados.get("razao_social", "")
    natureza = str(dados.get("natureza_juridica") or "")

    endereco_partes = [
        dados.get("tipo_logradouro"),
        dados.get("logradouro"),
        dados.get("numero"),
        dados.get("complemento"),
        dados.get("bairro"),
        dados.get("municipio"),
        dados.get("uf"),
    ]

    endereco = ", ".join(
        str(parte).strip()
        for parte in endereco_partes
        if parte and str(parte).strip()
    )

    # Primeiro tenta identificar um administrador na OpenCNPJ.
    socios = dados.get("QSA") or dados.get("qsa") or []
    representante = identificar_administrador(socios)

    # Consulta complementar: também aproveita os dados da Kitana.
    dados_kitana = {}

    try:
        resposta_kitana = consultar_json(API_KITANA.format(cnpj))

        if resposta_kitana.get("success"):
            dados_kitana = resposta_kitana.get("data") or {}

    except (requests.RequestException, ValueError):
        # A consulta principal continua utilizável se a segunda API falhar.
        pass

    if not nome_empresa:
        nome_empresa = dados_kitana.get("razaoSocial", "")

    if not natureza:
        natureza = str(dados_kitana.get("naturezaJuridica") or "")

    # Se a OpenCNPJ não encontrou um administrador único,
    # tenta identificar um na resposta da Kitana.
    if not representante:
        representante = identificar_administrador(
            dados_kitana.get("socios") or []
        )

    natureza_normalizada = natureza.casefold()

    # Para Empresário Individual, sugere a razão social como nome
    # do titular, deixando a conferência explícita.
    if not representante and (
        "empresário (individual)" in natureza_normalizada
        or "empresario individual" in natureza_normalizada
        or "(2135)" in natureza_normalizada
    ):
        representante = nome_empresa

    return {
        "nome_empresa": nome_empresa,
        "cnpj": dados.get("cnpj", cnpj),
        "endereco": endereco,
        "cep": dados.get("cep", ""),
        "representante": representante,
        "representante_precisa_conferir": bool(representante),
    }