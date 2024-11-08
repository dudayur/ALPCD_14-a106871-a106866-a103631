import os
import typer
import requests
import json
import csv
import re
from typing import List, Optional
from datetime import datetime


headers = {
    "User-Agent": ""
}


app = typer.Typer()

# Obtém a chave da API da variável de ambiente
API_KEY = os.getenv("ITJOBS_API_KEY")
url = "https://www.itjobs.pt/api"


def fetch_jobs(endpoint: str, params: dict) -> list:
    """Função para fazer requisições à API com autenticação."""
    if not API_KEY:
        typer.echo("Erro: A chave da API não foi configurada. Defina a variável de ambiente ITJOBS_API_KEY.")
        raise typer.Exit(code=1)

    response = requests.get(f"{url}/{endpoint}", headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def save_to_csv(data: list, filename: str, fields: list):
    """Função para salvar dados no formato CSV."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for item in data:
            writer.writerow({field: item.get(field, "") for field in fields})


@app.command()
def top(n: int, export_csv: Optional[bool] = False):
    """Lista os N trabalhos mais recentes publicados pela itjobs.pt."""
    jobs = fetch_jobs("jobs", {"limit": n})
    print(json.dumps(jobs, indent=2))

    if export_csv:
        save_to_csv(
            jobs,
            "top_jobs.csv",
            ["titulo", "empresa", "descricao", "data_publicacao", "salario", "localizacao"]
        )
        print("Arquivo CSV 'top_jobs.csv' criado com sucesso!")


@app.command()
def search(city: str, company: str, n: int, export_csv: Optional[bool] = False):
    """Lista trabalhos full-time de uma empresa específica em uma cidade."""
    jobs = fetch_jobs("jobs", {"city": city, "company": company, "type": "full-time", "limit": n})
    print(json.dumps(jobs, indent=2))

    if export_csv:
        save_to_csv(
            jobs,
            "search_jobs.csv",
            ["titulo", "empresa", "descricao", "data_publicacao", "salario", "localizacao"]
        )
        print("Arquivo CSV 'search_jobs.csv' criado com sucesso!")


@app.command()
def salary(job_id: str):
    """Extrai o salário de uma vaga pelo job_id."""
    job = fetch_jobs(f"jobs/{job_id}", {})

    wage = job.get("salario")
    if not wage:
        wage = extract_wage_from_description(job.get("descricao", ""))

    print(wage if wage else "Salário não especificado")


def extract_wage_from_description(description: str) -> Optional[str]:
    """Extrai o salário da descrição usando expressões regulares, se disponível."""
    matches = re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})", description)
    return matches[0] if matches else None


@app.command()
def skills(skills: List[str], start_date: str, end_date: str, export_csv: Optional[bool] = False):
    """Mostra trabalhos que requerem uma lista de skills dentro de um período."""
    params = {
        "skills": ",".join(skills),
        "date_start": start_date,
        "date_end": end_date
    }
    jobs = fetch_jobs("jobs", params)
    print(json.dumps(jobs, indent=2))

    if export_csv:
        save_to_csv(
            jobs,
            "skills_jobs.csv",
            ["titulo", "empresa", "descricao", "data_publicacao", "salario", "localizacao"]
        )
        print("Arquivo CSV 'skills_jobs.csv' criado com sucesso!")


if __name__ == "__main__":
    app()
