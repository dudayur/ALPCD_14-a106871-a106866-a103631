import csv
import json
import re
from datetime import datetime
from typing import List, Optional
import requests
import typer

# URL base da API
API_KEY = "91e0f74216c91fb6275adaa79e372f22"
BASE_URL = "https://api.itjobs.pt/job/get.json"
SEARCH_URL = "https://api.itjobs.pt/job/list.json"

# Headers padrão para as requisições
headers = {
    "User-Agent": ""  # Pode adicionar o User-Agent conforme necessário
}

# Inicialização do Typer
app = typer.Typer()


def fetch_jobs(params: dict) -> list:
    """Função para obter os trabalhos através da API."""
    params['api_key'] = API_KEY
    response = requests.get(SEARCH_URL, headers=headers, params=params)

    if response.status_code == 200:
        try:
            data = response.json()
            return data.get("results", [])
        except ValueError:
            print("Erro ao converter para JSON.")
            return []
    else:
        print(f"Erro na requisição: {response.status_code}")
        return []


def fetch_job(job_id: int) -> dict:
    """Obtém informações detalhadas de um trabalho específico."""
    params = {
        "api_key": API_KEY,
        "id": job_id
    }
    response = requests.get(BASE_URL, headers=headers, params=params)

    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print("Erro ao converter para JSON.")
            return {}
    else:
        print(f"Erro na requisição: {response.status_code}")
        return {}


def save_to_csv(vagas, nome_arquivo="data.csv",
                colunas=["titulo", "empresa", "descricao", "data_de_publicacao", "salario", "localizacao"]
                ):
    # Define os nomes das colunas

    # Abre o arquivo para escrita
    with open(nome_arquivo, mode="w", newline='') as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=colunas)

        # Escreve o cabeçalho
        writer.writeheader()

        # Escreve cada vaga
        for vaga in vagas:
            writer.writerow({
                "titulo": vaga.get("title"),
                "empresa": vaga.get("company", {}).get("name"),
                "descricao": vaga.get("body"),
                "data_de_publicacao": vaga.get("publishedAt"),
                "salario": vaga.get("wage") or "N/A",
                "localizacao": ", ".join([loc["name"] for loc in vaga.get("locations", [])])
            })


def extract_wage_from_description(description: str) -> Optional[str]:
    """Extrai o salário da descrição usando expressões regulares."""
    matches = re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})", description)
    return matches[0] if matches else None


@app.command()
def top(n: int, export_csv: Optional[bool] = False):
    """Lista os N trabalhos mais recentes publicados pela itjobs.pt."""
    vagas = fetch_jobs({"limit": n})
    print(json.dumps(vagas, indent=2))

    if export_csv:
        save_to_csv(
            vagas,
            nome_arquivo='top_jobs.csv',
            colunas=["titulo", "empresa", "descricao", "data_de_publicacao", "salario", "localizacao"]

        )
    print("Arquivo CSV 'data.csv' criado com sucesso!")


@app.command()
def search(city: str, company: str, export_csv: Optional[bool] = False, n: int = 10) -> object:
    """Lista trabalhos full-time de uma empresa específica em uma cidade."""

    # Busca uma lista de trabalhos com limite 'n' (número de vagas a listar), usando a função fetch_jobs
    jobs = fetch_jobs({"limit": n})
    print(json.dumps(jobs, indent=2))  # Exibe os dados JSON dos trabalhos no terminal de forma organizada

    # Filtra a lista de trabalhos para obter apenas aqueles que:
    # 1. Contêm a cidade especificada em algum dos locais associados (procurando "city" em "locations")
    # 2. Pertencem à empresa especificada (procurando "company" no nome da empresa)
    filtered_jobs = [
        job for job in jobs  # "jobs" já é uma lista de resultados obtida da API
        if any(loc.get("name") == city for loc in job.get("locations", [])) and
           job.get("company", {}).get("name") == company
    ]

    # Se o parâmetro 'export_csv' for True, guarda os trabalhos filtrados num ficheiro CSV
    if export_csv:
        # Chama a função save_to_csv para criar o CSV 'search_jobs.csv' com as colunas especificadas
        save_to_csv(
            filtered_jobs,
            "search_jobs.csv",
            colunas=["titulo", "empresa", "descricao", "data_de_publicacao", "salario", "localizacao"]
        )
        print("Arquivo CSV 'search_jobs.csv' criado com sucesso!")  # Confirmação de criação do ficheiro CSV

    # Retorna a lista de trabalhos filtrados
    return filtered_jobs


@app.command()
def salary(job_id: int):
    """Extrai o salário de uma vaga pelo job_id."""
    job = fetch_job(job_id)

    wage = job.get("wage")
    if not wage:
        wage = extract_wage_from_description(job.get("description", ""))

    print(wage if wage else "Salário não especificado")


@app.command()
def skills(skills: List[str], start_date: str, end_date: str, export_csv: Optional[bool] = False, n: int = 10):
    """Mostra trabalhos que requerem uma lista de skills dentro de um período."""
    # Converte as datas de início e fim para objetos datetime para comparação
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

    jobs = fetch_jobs({"limit": n})

    filtered_jobs = []
    for job in jobs:
        published_at = job.get("publishedAt", "1970-01-01")

        # Tenta converter a string para um objeto datetime
        try:
            job_date = datetime.strptime(published_at, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Caso a conversão falhe (por exemplo, o formato da data está errado), usa uma data padrão
            print(f"Erro ao converter data: {published_at}")
            job_date = datetime(1970, 1,
                                1)  # Valor default em caso de erro
        # Verifica se data esta entre os intervalos de input
        if start_date_obj <= job_date <= end_date_obj:
            job_description = job.get("body", "").lower()
            job_title = job.get("title", "").lower()

            # Para cada skill, verifica se está presente na descrição ou no título do trabalho
            all_skills_found = True  # Variável para verificar se todas as skills foram encontradas
            for skill in skills:
                skill = skill.lower()  # Converte a skill para minúsculas para comparação sem diferenças de maiúsculas/minúsculas

                # Verifica se a skill está na descrição do trabalho
                if skill in job_description:
                    continue  # Se a skill for encontrada na descrição, continua para a próxima skill
                # Verifica se a skill está no título do trabalho
                elif skill in job_title:
                    continue  # Se a skill for encontrada no título, continua para a próxima skill
                else:
                    # Se a skill não for encontrada em nenhum dos dois campos, marca como False
                    all_skills_found = False
                    break  # Interrompe a verificação das skills para este trabalho, pois faltou uma skill

            # Se todas as skills foram encontradas no título ou na descrição, adiciona o trabalho à lista de filtrados
            if all_skills_found:
                filtered_jobs.append(job)

    print(json.dumps(filtered_jobs, indent=2))

    if export_csv:
        save_to_csv(
            filtered_jobs,
            nome_arquivo='skills_jobs.csv',
            colunas=["titulo", "empresa", "descricao", "data_de_publicacao", "salario", "localizacao"]

        )
    print("Arquivo CSV 'skills_jobs.csv' criado com sucesso!")
    return filtered_jobs


if __name__ == "__main__":
    app()
