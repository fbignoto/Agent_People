# Agent People

## Descrição

Agent People é um assistente virtual de RH desenvolvido com IA generativa usando o modelo Gemini e integrado com o Google Cloud Platform. O agente é capaz de responder perguntas sobre políticas da empresa, gerenciar informações de funcionários, treinamentos e férias.

## Componentes

O projeto possui duas implementações principais:

1. **AgenteRhaissa.py** - Versão local do agente com base de conhecimento completa

   - Utiliza Gemini para processamento de linguagem natural
   - Acessa base de conhecimento local (políticas e dados de funcionários)
   - Interface via linha de comando

2. **main.py** - Versão para deploy no GCP como Cloud Function
   - Implementada como API HTTP
   - Utiliza Gemini 2.5 Flash Preview
   - Otimizada para execução em nuvem

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
  - Vertex AI (para Gemini)
- Credenciais do Google Cloud configuradas

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
GCP_FUNCTION_GET_TIME=url_da_funcao_tempo
```

## Estrutura do Projeto

```
Agent_People/
├── AgenteRhaissa.py     # Implementação local
├── main.py              # Implementação GCP
├── requirements.txt
├── bucket_rhaissa/      # Base de conhecimento
│   ├── funcionarios.csv
│   └── politicas.txt
└── scripts/
    └── bucket.py        # Utilitários GCP
```

## Uso

### Execução Local

Para executar o agente localmente com interface de linha de comando:

```bash
python AgenteRhaissa.py
```

### Deploy no GCP

Para fazer deploy da versão cloud como Cloud Function:

```bash
gcloud functions deploy agent-people \
 --gen2 \
 --region=us-central1 \
 --runtime=python312 \
 --source=. \
 --entry-point=handle_request \
 --trigger-http \
 --memory=256Mi

```

### Invocação do agente

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" "{URL da function}" -d '{"query": "quem é voce?"}' -H "Content-Type: application/json"
```

## Exemplos de Uso

O agente pode responder perguntas como:

- "Qual é a política de férias da empresa?"
- "Quais treinamentos estão pendentes para a equipe de tecnologia?"
- "Quando começam as férias do João Santos?"

## Desenvolvimento

- O arquivo `.gcloudignore` especifica quais arquivos não devem ser enviados para o GCP
- A versão local (`AgenteRhaissa.py`) mantém uma base de conhecimento completa
- A versão cloud (`main.py`) é otimizada para performance e custos

# Tarefa 1: Agente de IA generativa GCP

## Objetivo

Planejar, projetar, tarefar, desenvolver e implantar um agente de IA generativa utilizando o modelo Gemini 2.5,.
Use Python como linguagem, com desenvolvimento local e deploy no Google Cloud Platform (GCP)

---

## Critérios de Aceitação

- [ ] Tarefação do projeto
- [ ] Artefatos criados corretamente no GCP
- [ ] Código e dependências validados
- [ ] Permitir atualizações iterativas (ao aplicar alterações no codigo local, que seja possível aplica-las no ambiente cloud GCP)
- [ ] Código versionado em repositório (pode usar github pessoal)
- [ ] Documentação básica do processo adicionada ao `README.md`
