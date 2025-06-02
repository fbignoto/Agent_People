# Agent People

## Descrição

Agent People é um assistente virtual de RH desenvolvido com IA generativa usando o modelo GPT-4 e integrado com o Google Cloud Platform. O agente é capaz de responder perguntas sobre políticas da empresa, gerenciar informações de funcionários, treinamentos e férias.

## Funcionalidades

- Consulta de políticas da empresa
- Gestão de informações de funcionários
- Gerenciamento de férias
- Acompanhamento de treinamentos
- Integração com GCP para processamentos em nuvem

## Pré-requisitos

- Python 3.12+
- Conta Google Cloud Platform com as seguintes APIs habilitadas:
  - Cloud Storage
  - Cloud Functions
- Credenciais do Google Cloud configuradas
- OpenAI API Key

## Configuração do Ambiente

1. Clone o repositório
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no arquivo `.env`:

```
GOOGLE_API_KEY=sua_chave_google
GCP_BUCKET_NAME=nome_do_bucket
GOOGLE_CLOUD_PROJECT=id_do_projeto
GOOGLE_CLOUD_LOCATION=regiao
```

## Estrutura do Projeto

```
Agent_People/
├── AgenteRhaissa.py
├── main.py
├── requirements.txt
├── bucket_rhaissa/
│   ├── funcionarios.csv
│   └── politicas.txt
└── scripts/
    └── bucket.py
```

## Uso

Para executar o agente localmente:

```bash
python AgenteRhaissa.py
```

## Deploy

Para fazer deploy da Cloud Function:

```bash
gcloud functions deploy Function_Rhaissa \
 --region=us-central1 \
 --runtime=python312 \
 --source=. \
 --entry-point=main \
 --trigger-http
```

## Exemplos de Uso

O agente pode responder perguntas como:

- "Qual é a política de férias da empresa?"
- "Quais treinamentos estão pendentes para a equipe de tecnologia?"
- "Quando começam as férias do João Santos?"
