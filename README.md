CLI para Consulta de Oportunidades de Emprego na API ITJobs

Este projeto tem como objetivo criar uma Interface de Linha de Comando (CLI) para interagir com a API ITJobs, que fornece informações sobre oportunidades de emprego na área de TI. Através desta CLI, é possível listar e pesquisar empregos usando diversos parâmetros, como habilidades específicas, cidade, empresa, intervalo de datas, entre outros.

Pré-requisitos
Python 3.7+: Esta aplicação requer Python 3.7 ou uma versão superior.
Bibliotecas Python:
typer (para a criação da CLI)
requests (para interagir com a API)
csv e json (para manipulação de dados e exportação para CSV)
Para instalar as bibliotecas necessárias, execute:

bash
Copiar código
pip install typer requests
Utilização
Estrutura do Código
A aplicação possui as seguintes funcionalidades principais:

Listagem de empregos mais recentes: Obtém e exibe uma lista dos N empregos mais recentes.
Pesquisa por cidade e empresa: Filtra vagas com base em cidade e empresa, com opção de exportação para CSV.
Extração de salário: Através de um ID específico, extrai o salário da vaga.
Filtro por habilidades: Permite pesquisar empregos que requerem uma lista específica de habilidades, num intervalo de datas.
Configuração da Chave API
É necessário configurar uma chave API para autenticar as solicitações à API ITJobs. A chave API deve ser definida no código como API_KEY. Obtém a tua chave em https://www.itjobs.pt/api/docs.

Comandos Disponíveis
Os comandos estão implementados através da biblioteca Typer para simplificar o uso da CLI.

1. Listagem dos Empregos Mais Recentes
bash
Copiar código
python nome_do_script.py top --n <numero_de_empregos> [--export-csv]
Exemplo:

bash
Copiar código
python nome_do_script.py top --n 10 --export-csv
Este comando exibe os N empregos mais recentes e, se especificado, exporta os resultados para top_jobs.csv.

2. Pesquisa de Empregos por Cidade e Empresa
bash
Copiar código
python nome_do_script.py search --city <cidade> --company <empresa> [--export-csv] [--n <numero_de_empregos>]
Exemplo:

bash
Copiar código
python nome_do_script.py search --city "Lisboa" --company "ExemploTech" --export-csv --n 10
Este comando exibe os empregos que correspondem à cidade e empresa indicadas, com a opção de exportação para CSV.

3. Extração de Salário por ID de Vaga
bash
Copiar código
python nome_do_script.py salary --job-id <ID_da_vaga>
Exemplo:

bash
Copiar código
python nome_do_script.py salary --job-id 12345
Este comando exibe o salário para a vaga especificada pelo ID.

4. Pesquisa de Empregos por Habilidades
bash
Copiar código
python nome_do_script.py skills --skills <habilidade1> <habilidade2> --start-date <AAAA-MM-DD> --end-date <AAAA-MM-DD> [--export-csv] [--n <numero_de_empregos>]
Exemplo:

bash
Copiar código
python nome_do_script.py skills --skills "Python" "SQL" "Machine Learning" --start-date "2023-01-01" --end-date "2023-12-31" --export-csv --n 10
Este comando filtra empregos que requerem todas as habilidades especificadas num intervalo de datas, com a opção de exportação para CSV.

Estrutura do Projeto
fetch_jobs: Função para obter uma lista de empregos a partir da API.
fetch_job: Função para obter detalhes de um emprego específico pelo ID.
save_to_csv: Função que exporta os dados para um ficheiro CSV.
extract_wage_from_description: Função que tenta extrair o salário da descrição, se não estiver explicitamente presente.
top: Comando que exibe os N empregos mais recentes.
search: Comando que pesquisa empregos por cidade e empresa.
salary: Comando que exibe o salário de uma vaga pelo ID.
skills: Comando que pesquisa empregos com base numa lista de habilidades e intervalo de datas.
Notas
Documentação da API: Aconselha-se que explore a documentação oficial para conhecer as rotas, parâmetros e tipos de dados retornados pela API.
Teste da API: Ferramentas como o Postman podem ser úteis para testar a API antes de implementar o código.
