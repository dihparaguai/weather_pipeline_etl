# Weather Pipeline ETL

Este é um projeto de **Engenharia de Dados** desenvolvido como portfólio para simular um cenário real corporativo. Ele demonstra na prática todo o fluxo necessário para extrair, limpar e persistir dados climáticos de forma 100% automática, usando arquitetura ETL e estruturação em camadas Medallion.

## 1. Objetivo
Estruturar o fluxo automatizado de extração diária de dados climáticos consumidos da OpenWeatherMap API, promovendo a limpeza e padronização (Camadas Bronze e Silver) e finalizando com a carga persistente em um banco de dados PostgreSQL (Camada Gold). Os dados ingeridos no banco serão posteriormente conectados e visualizados dinamicamente através de dashboards no Power BI.

## 2. Tecnologias
- **[Python](https://docs.python.org/3/)**: Linguagem principal para desenvolvimento dos scripts de integração e processamento.
- **[Docker](https://docs.docker.com/)**: Infraestrutura de conteinerização encarregada pelo isolamento e provisionamento do cluster (orquestrador e banco).
- **[Apache Airflow](https://airflow.apache.org/docs/)**: Orquestração, monitoramento e agendamento de tarefas via TaskFlow API. Executado via Docker Compose.
- **[Pandas](https://pandas.pydata.org/docs/)**: Transformação pesada de dados brutos e conversão direta para o formato de alta performance estruturado em `.parquet`.
- **[PostgreSQL](https://www.postgresql.org/docs/)**: Servidor de banco de dados relacional atuando como Data Warehouse local.
- **[SQLAlchemy](https://docs.sqlalchemy.org/)**: Comunicação ORM para inserção de DataFrames de forma automatizada no PostgreSQL.
- **[Loguru](https://loguru.readthedocs.io/)**: Padronização e estruturação dos logs de execução das rotinas.
- **[Power BI](https://learn.microsoft.com/power-bi/)**: Ferramenta de visualização final de BI alimentada pela base relacional tratada no PostgresSQL (camada Gold).

## 3. Estrutura do Projeto
```text
weather_pipeline_etl/
├── dags/
│   └── weather_etl_dag.py        # DAG orquestradora lida pelo Airflow
├── data/
│   ├── bronze/                   # Camada Bronze: Arquivos brutos JSON da API
│   └── silver/                   # Camada Silver: Dados limpos em formato Parquet
├── src/
│   ├── jobs/                     # Scripts isolados de E-T-L (extract.py, transform.py, load.py)
│   └── modules/                  # Conectores e adaptadores auxiliares (API e BD)
├── docker-compose.yml            # Arquivo de infraestrutura de containers do Airflow
└── main.py                       # Orquestração manual do pipeline completo via terminal
```

## 4. Configuração e Dependências

### 4.1 Variáveis de Ambiente (.env)
Crie um arquivo `.env` na raiz do projeto com as credenciais obrigatórias para inicializar os ambientes:
```env
WEATHER_API_KEY=sua_chave_openweather
AIRFLOW_UID=501
PG_USER=seu_usuario_postgres
PG_PASSWORD=sua_senha_postgres
PG_HOST=host.docker.internal
PG_PORT=5432
PG_DB=seu_banco_de_dados

# Força a instalação nativa destas bibliotecas durante a criação do container Airflow
_PIP_ADDITIONAL_REQUIREMENTS="loguru pyarrow pandas psycopg2-binary"
```

### 4.2 Mapeamento de Rede Host para WSL/Docker
Como a infraestrutura do Airflow opera em containers, é necessário configurar o PostgreSQL instalado na máquina local do host Windows a autorizar requisições das sub-redes Docker e WSL (se usado):

1. Modifique o arquivo `pg_hba.conf` do PostgreSQL Server inserindo os direcionamentos IP:
```conf
# Acesso interno para serviços Docker
host    all    all    172.18.0.0/16     md5
# Acesso interno para o terminal WSL
host    all    all    192.168.0.0/24    md5
```
2. Crie uma regra explícita no **Firewall do Windows** permitindo tráfego de entrada na porta de conexão de entrada TCP do PostgreSQL (`5432`).

### 4.3 Criação do Banco e Permissões de Esquema
Como a aplicação opera sob o princípio de mínimo privilégio, é necessário criar previamente o usuário de conexão configurado no `.env` e seu respectivo escopo.

Acesse o PostgreSQL do host Windows como superusuário (geralmente `postgres`) e execute sequencialmente:
```sql
-- Crie o usuário no Postgres apenas se necessário
CREATE USER seu_usuario_postgres WITH PASSWORD 'sua_senha_postgres';

-- Crie o banco de dados apenas se necessário
CREATE DATABASE seu_banco_de_dados OWNER seu_usuario_postgres;

-- Após conectar-se ao banco (seu_banco_de_dados), libere os privilégios gerais:
GRANT ALL ON SCHEMA public TO seu_usuario_postgres;
```

## 5. Como Executar e Validar

1. Com o Docker aberto na sua máquina, inicie o cluster do Airflow rodando no terminal:
```bash
docker compose up -d
```
2. Assim que subir, acesse a interface visual do orquestrador pelo seu navegador no endereço `http://localhost:8080`.
3. Ligue a chave da DAG `weather_pipeline_etl`. O Airflow irá disparar, varrer o histórico dos últimos 30 dias de clima e salvar tudo de forma retroativa no seu banco de dados PostgreSQL.
4. Abra o arquivo do **Power BI** (`.pbix`) já fornecido neste projeto. Como os painéis já foram desenvolvidos e modelados, apenas valide as credenciais solicitadas do banco na porta `5432` para atualizar e interagir instantaneamente com os dados extraídos da Camada Gold!