
from pathlib import Path
from datetime import datetime
from docx import Document
import shutil
import sys


BASE_DIR = Path(__file__).resolve().parent.parent

ARQUIVO_ORIGINAL = BASE_DIR / "modelos" / "contrato_base.docx"
ARQUIVO_MODELO = BASE_DIR / "modelos" / "contrato_base_variavel.docx"
PASTA_BACKUP = BASE_DIR / "modelos" / "backup"


def substituir_paragrafo(documento, identificador, novo_texto):
    encontrados = [
        p for p in documento.paragraphs
        if identificador.lower() in p.text.lower()
    ]

    if len(encontrados) != 1:
        raise ValueError(
            f"Esperado exatamente 1 parágrafo para "
            f"'{identificador}', encontrados: {len(encontrados)}"
        )

    paragrafo = encontrados[0]

    if not paragrafo.runs:
        raise ValueError(
            f"O parágrafo '{identificador}' não possui trechos editáveis."
        )

    # Mantém a formatação do primeiro trecho do parágrafo.
    paragrafo.runs[0].text = novo_texto

    # Limpa os demais trechos para evitar texto duplicado.
    for trecho in paragrafo.runs[1:]:
        trecho.text = ""


def main():
    if not ARQUIVO_ORIGINAL.exists():
        print(f"ERRO: modelo original não encontrado:\n{ARQUIVO_ORIGINAL}")
        sys.exit(1)

    if ARQUIVO_MODELO.exists():
        print(
            "ERRO: o modelo variável já existe.\n"
            "Confira o arquivo antes de executar novamente:\n"
            f"{ARQUIVO_MODELO}"
        )
        sys.exit(1)

    PASTA_BACKUP.mkdir(parents=True, exist_ok=True)

    # Backup com data e hora, sem sobrescrever cópias anteriores.
    identificador = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_backup = (
        PASTA_BACKUP / f"contrato_base_{identificador}.docx"
    )
    shutil.copy2(ARQUIVO_ORIGINAL, arquivo_backup)

    documento = Document(ARQUIVO_ORIGINAL)

    substituir_paragrafo(
        documento,
        "68.516.962/0001-31",
        "CONTRATANTE: {{ nome_empresa }}, inscrita no CNPJ: "
        "{{ cnpj }}, estabelecida na {{ endereco }}, CEP: {{ cep }}, "
        "representada neste ato por {{ representante }}, CPF: "
        "{{ cpf_representante }}, nacionalidade {{ nacionalidade }}, "
        "{{ profissao }}, aqui denominada CONTRATANTE."
    )

    substituir_paragrafo(
        documento,
        "O valor para a execução dos serviços descritos acima",
        "O valor para a execução dos serviços descritos acima é de "
        "R$ {{ valor_mensal }} ({{ valor_extenso }}) por mês, "
        "para o pacote de Assessoria Contábil. O valor do contrato "
        "será reajustado todo mês de janeiro, de acordo com a livre "
        "negociação entre as partes, não podendo o reajuste ser "
        "inferior à variação do índice de inflação do período contratual."
    )

    substituir_paragrafo(
        documento,
        "O presente contrato tem a vigência",
        "O presente contrato tem a vigência por período indeterminado, "
        "a começar em {{ data_inicio }}."
    )

    substituir_paragrafo(
        documento,
        "Salvador (BA),",
        "Salvador (BA), {{ data_assinatura_extenso }}."
    )

    documento.save(ARQUIVO_MODELO)

    print("Modelo variável criado com sucesso!")
    print(f"Modelo: {ARQUIVO_MODELO}")
    print(f"Backup: {arquivo_backup}")


if __name__ == "__main__":
    main()
