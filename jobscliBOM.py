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


def fetch_jobs(params: dict, max_results: int = 10000) -> list:
    """Função para obter trabalhos com suporte a paginação."""
    params['api_key'] = API_KEY
    params['limit'] = 20  # Limite de itens por página
    all_results = []
    page = 1

    while len(all_results) < max_results:
        params['page'] = page
        response = requests.get(SEARCH_URL, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Erro na requisição: {response.status_code}")
            break

        try:
            data = response.json()
            results = data.get("results", [])
            if not results:
                break
            all_results.extend(results)
            page += 1
        except ValueError:
            print("Erro ao converter para JSON.")
            break

    return all_results[:max_results]


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
                colunas=["titulo", "empresa", "descricao", "data_de_publicacao", "salario", "localizacao"]):
    """Salva dados em um arquivo CSV."""
    with open(nome_arquivo, mode="w", newline='', encoding='utf-8') as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=colunas)
        writer.writeheader()
        for vaga in vagas:
            try:
                writer.writerow({
                    "titulo": vaga.get("title"),
                    "empresa": vaga.get("company", {}).get("name"),
                    "descricao": vaga.get("body"),
                    "data_de_publicacao": vaga.get("publishedAt"),
                    "salario": vaga.get("wage") or "N/A",
                    "localizacao": ", ".join([loc["name"] for loc in vaga.get("locations", [])])
                })
            except UnicodeEncodeError as e:
                print(f"Erro ao salvar linha no CSV: {e}")


def export_statistics_to_csv(data, filename):
    """Exporta os dados de estatísticas de zona e tipo de trabalho para um CSV."""
    colunas = ["Zona", "Tipo de Trabalho", "Nº de Vagas"]
    with open(filename, mode="w", newline='', encoding='utf-8') as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=colunas)
        writer.writeheader()
        for row in data:
            try:
                writer.writerow(row)
            except UnicodeEncodeError as e:
                print(f"Erro ao salvar linha no CSV: {e}")


def extract_wage_from_description(description: str) -> Optional[str]:
    """Extrai o salário da descrição usando expressões regulares."""
    matches = re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})", description)
    return matches[0] if matches else None
    
def get_job_url(job: str) -> str: 
    formatted_job = job.lower().replace(" ", "-") 
    return f"https://www.ambitionbox.com/jobs/{formatted_job}-jobs-prf"


@app.command()
def top(n: int, export_csv: Optional[bool] = False):
    """Lista os N trabalhos mais recentes publicados pela itjobs.pt."""
    vagas = fetch_jobs({"order_by": "publishedAt"}, max_results=n)
    print(json.dumps(vagas, indent=2))

    if export_csv:
        save_to_csv(
            vagas,
            nome_arquivo='top_jobs.csv',
            colunas=["titulo", "empresa", "descricao", "data_de_publicacao", "salario", "localizacao"]
        )
        print("Arquivo CSV 'top_jobs.csv' criado com sucesso!")
    else:
        print("Exportação para CSV não realizada, use o parâmetro --export-csv para exportar os dados.")


@app.command()
def search(city: str, company: str, export_csv: Optional[bool] = False, n: int = 10):
    """Lista trabalhos full-time de uma empresa específica em uma cidade."""
    jobs = fetch_jobs({"limit": n})
    filtered_jobs = [
        job for job in jobs
        if any(loc.get("name") == city for loc in job.get("locations", [])) and
           job.get("company", {}).get("name") == company
    ]
    print(json.dumps(filtered_jobs, indent=4, ensure_ascii=False))

    if export_csv:
        save_to_csv(
            filtered_jobs,
            "search_jobs.csv",
            colunas=["titulo", "empresa", "descricao", "data_de_publicacao", "salario", "localizacao"]
        )
        print("Arquivo CSV 'search_jobs.csv' criado com sucesso!")

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
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

    jobs = fetch_jobs({"limit": n})
    filtered_jobs = []

    for job in jobs:
        published_at = job.get("publishedAt", "1970-01-01")
        try:
            job_date = datetime.strptime(published_at, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            job_date = datetime(1970, 1, 1)

        if start_date_obj <= job_date <= end_date_obj:
            job_description = job.get("body", "").lower()
            job_title = job.get("title", "").lower()
            all_skills_found = all(skill.lower() in job_description or skill.lower() in job_title for skill in skills)
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

@app.command()
def get_info(job_id: Annotated[int, typer.Argument(help="ID do trabalho")], export: Optional[bool] = False):
    """
    Busca informações de uma vaga específica (jobID) e enriquece com dados da empresa do AmbitionBox.
    """
    url = f"https://api.itjobs.pt/job/get.json?api_key=ee176fa9456283ab9c42f357b036e236&id={job_id}"
    headers = {'User-Agent': "ALPCD_5", 'Cookie': 'itjobs_pt=3cea3cc1f4c6a847f8c459367edf7143:94de45f2a55a15b2672adf8788ac8072e7bfd5c5'}  # Necessário por 'User-Agent' nos headers
    job_data = requests.get(url, headers)
    if not job_data:
        print(f"Não foi possível encontrar o jobID {job_id}. Verifique se o ID é válido.")
        return

    company_name = job_data.get("company", {}).get("name", "Desconhecida")
    if company_name == "Desconhecida":
        print("Não foi possível obter o nome da empresa.")
        return
    modified_company_name = re.sub(r'(.)( *Portugal)(.*)', r"\1", company_name)


    ambitionbox_url = f"https://www.ambitionbox.com/overview/{re.sub(' ', '-', modified_company_name).lower()}-overview"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    soup = requests.get(ambitionbox_url, headers, get_soup=True)

    rank=soup.find("span",class_="css-1jxf684 text-primary-text font-pn-700 text-xl !text-base").text
    description=soup.find("div",class_="css-146c3p1 font-pn-400 text-sm text-neutral mb-2").text
    benefits_all=soup.find_all("div",class_="css-146c3p1 font-pn-400 text-sm text-primary-text")
    benefits = [p.get_text() for p in benefits_all[4:]]


    data = {
    "rank": rank,
    "description": description,
    "benefits": benefits
    }
    print(json.dumps(data, indent=4, ensure_ascii=False))

@app.command()
def statistics_zone():
    """Cria um CSV com a contagem de vagas por zona e tipo de trabalho."""
    jobs = fetch_jobs({"limit": 10000})  # Ajustar o limite conforme necessário
    stats = []

    for job in jobs:
        for location in job.get("locations", []):
            zone = location.get("name", "Unknown")
            job_type = job.get("title", "Unknown")
            stats.append({
                "Zona": zone,
                "Tipo de Trabalho": job_type,
                "Nº de Vagas": 1
            })

    # Consolidar dados para contagem correta
    consolidated_stats = {}
    for entry in stats:
        key = (entry["Zona"], entry["Tipo de Trabalho"])
        if key not in consolidated_stats:
            consolidated_stats[key] = entry
            consolidated_stats[key]["Nº de Vagas"] = 0
        consolidated_stats[key]["Nº de Vagas"] += 1

    # Transformar em lista para CSV
    final_rows = [
        {"Zona": key[0], "Tipo de Trabalho": key[1], "Nº de Vagas": value["Nº de Vagas"]}
        for key, value in consolidated_stats.items()
    ]

    # Exportar para CSV
    export_statistics_to_csv(final_rows, "statistics_zone.csv")
    print("Ficheiro de exportação criado com sucesso.")

@app.command()
def list_skills(job: str): 
    job_url = get_job_url(job)
    

    service=Service(executable_path="chromedriver.exe")
    driver=webdriver.Chrome(service=service)


    driver.get(job_url)
    wait = WebDriverWait(driver, 15)
    target_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@arialabel='Skill']")))
    target_button.click()
    time.sleep(3)
    skills_list = []
    numbers_list = []

    skills_elements = driver.find_elements(By.XPATH, "//span[@class='label']")
    numbers = driver.find_elements(By.XPATH, "//span[contains(text(),'(')]") 
    for i in range(min(10, len(skills_elements))):
        skill = skills_elements[i].text.strip()  # Get the skill name
        number = numbers[i].text.strip('()')  # Clean number from parentheses
        skills_list.append({"skill": skill, "count": int(number)})  # Append as dict

    json_output = json.dumps(skills_list)

    print(json_output)

    time.sleep(3)
    driver.quit

@app.command()
def getd(job_id: Annotated[int, typer.Argument(help="ID do trabalho")], export: Optional[bool] = False):

 
    url = f"https://api.itjobs.pt/job/get.json?api_key=ee176fa9456283ab9c42f357b036e236&id={job_id}"
    headers = {'User-Agent': "ALPCD_5", 'Cookie': 'itjobs_pt=3cea3cc1f4c6a847f8c459367edf7143:94de45f2a55a15b2672adf8788ac8072e7bfd5c5'}  # Necessário por 'User-Agent' nos headers
    job_data = requests.get(url, headers)
    if not job_data:
        print(f"Não foi possível encontrar o jobID {job_id}. Verifique se o ID é válido.")
        return


    company_name = job_data.get("company", {}).get("name", "Desconhecida")
    if company_name == "Desconhecida":
        print("Não foi possível obter o nome da empresa.")
        return
    modified_company_name = re.sub(r'(.)( *Portugal)(.*)', r"\1", company_name)
    url=f"https://www.careerbliss.com/{re.sub(' ', '+', modified_company_name).lower()}/"
    response = requests.get(url)
    print(response.status_code)
    soup=BeautifulSoup(response.content, "html.parser")
    rank=soup.find("span",class_="value").text
    all=soup.find("div",class_="description profile-module")
    description=all.find("p").text
    pattern = re.compile(r'benefits?.*?employees?.*')
    benefits_paragraphs = soup.find_all("p", string=pattern)
    benefits = [p.get_text() for p in benefits_paragraphs]

    data = {
        "rank": rank,
        "description": description,
        "benefits": benefits
    }
    print(json.dumps(data, indent=4, ensure_ascii=False))




if __name__ == "__main__":
    app()


