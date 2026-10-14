
from docx import Document
from src.gerador_contrato import gerar_contrato


dados_teste = {
    "nome_empresa": "EMPRESA TESTE LTDA",
    "cnpj": "11222333000181",
    "endereco": "Rua de Teste, 100, Centro, Salvador/BA",
    "cep": "40000-000",
    "representante": "MARIA DA SILVA",
    "cpf_representante": "52998224725",
    "nacionalidade": "brasileira",
    "profissao": "empresária",
    "valor_mensal": "1500,00",
    "data_inicio": "01/11/2026",
    "data_assinatura": "14/10/2026",
}


try:
    caminho = gerar_contrato(dados_teste)

    print("\nContrato de teste gerado!")
    print(f"Arquivo: {caminho}")

    documento = Document(caminho)

    texto_completo = "\n".join(
        paragrafo.text
        for paragrafo in documento.paragraphs
    )

    marcadores = [
        "{{ nome_empresa }}",
        "{{ cnpj }}",
        "{{ endereco }}",
        "{{ valor_mensal }}",
        "{{ data_inicio }}",
    ]

    pendentes = [
        marcador
        for marcador in marcadores
        if marcador in texto_completo
    ]

    if pendentes:
        print("\nATENÇÃO: foram encontrados marcadores pendentes:")
        for marcador in pendentes:
            print(f"- {marcador}")
    else:
        print("Verificação dos marcadores: OK")

    if "EMPRESA TESTE LTDA" in texto_completo:
        print("Verificação do nome da empresa: OK")
    else:
        print("ATENÇÃO: nome da empresa não encontrado.")

except (ValueError, FileNotFoundError) as erro:
    print(f"\nNão foi possível gerar o contrato: {erro}")
