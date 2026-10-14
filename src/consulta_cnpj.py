
import re
import requests


def consultar_cnpj(cnpj):
    cnpj = re.sub(r"\D", "", str(cnpj))

    if len(cnpj) != 14:
        raise ValueError("Informe um CNPJ com 14 dígitos.")

    url = f"https://api.opencnpj.org/{cnpj}"

    try:
        resposta = requests.get(
            url,
            timeout=20,
            headers={
                "Accept": "application/json",
                "User-Agent": "ConttyGeradorContratos/1.0",
            },
        )

        if resposta.status_code == 404:
            raise ValueError("CNPJ não encontrado na consulta.")

        if resposta.status_code == 429:
            raise ConnectionError(
                "Limite de consultas atingido. Tente novamente mais tarde."
            )

        resposta.raise_for_status()
        dados = resposta.json()

    except requests.Timeout:
        raise ConnectionError(
            "A consulta demorou demais. Tente novamente."
        )

    except requests.HTTPError as erro:
        raise ConnectionError(f"Erro HTTP na consulta do CNPJ: {erro}")

    except requests.RequestException as erro:
        raise ConnectionError(f"Falha na comunicação com a API: {erro}")

    except ValueError as erro:
        if isinstance(erro, requests.exceptions.JSONDecodeError):
            raise ConnectionError(
                "A API retornou uma resposta que não é um JSON válido."
            )
        raise

    partes_endereco = [
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
        for parte in partes_endereco
        if parte and str(parte).strip()
    )

    return {
        "nome_empresa": dados.get("razao_social", ""),
        "cnpj": dados.get("cnpj", cnpj),
        "endereco": endereco,
        "cep": dados.get("cep", ""),
    }
