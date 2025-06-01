import os
from typing import Union
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.schema import AgentAction, AgentFinish
from langchain.tools import Tool
from langchain.tools.retriever import create_retriever_tool
from langchain.prompts import PromptTemplate
from google.cloud import storage
import subprocess
import re
from dotenv import load_dotenv

load_dotenv()

storage_client = storage.Client()
bucket_name = os.getenv('GCP_BUCKET_NAME')
bucket = storage_client.bucket(bucket_name)

def download_from_gcs(blob_name: str, local_path: str):
    """Download arquivo do GCS para pasta local temporária"""
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)

def create_knowledge_base():
    """Cria base de conhecimento a partir dos arquivos no bucket"""
    if not os.path.exists('temp'):
        os.makedirs('temp')

    download_from_gcs('politicas.txt', 'temp/politicas.txt')
    download_from_gcs('funcionarios.csv', 'temp/funcionarios.csv')

    text_loader = TextLoader('temp/politicas.txt')
    csv_loader = CSVLoader('temp/funcionarios.csv')
    
    documents = text_loader.load() + csv_loader.load()

    # Divide documentos em chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    texts = text_splitter.split_documents(documents)

    # Cria embeddings usando Gemini
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        task_type="retrieval_document"
    )
    
    # Cria base de conhecimento vetorial
    vectorstore = FAISS.from_documents(texts, embeddings)
    
    return vectorstore

# Cria base de conhecimento
knowledge_base = create_knowledge_base()

# Cria ferramenta de busca na base de conhecimento
search_tool = create_retriever_tool(
    retriever=knowledge_base.as_retriever(),
    name="search_knowledge_base",
    description="Útil para buscar informações sobre funcionários, políticas da empresa, treinamentos, e férias."
)

def call_gcp_function(a: int, b: int) -> str:
    """Faz uma chamada para a Cloud Function no GCP"""
    try:
        # Obtém o token de autenticação
        result = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True,
            text=True,
            check=True
        )
        token = result.stdout.strip()
        
        # Monta e executa o comando curl
        function_url = "https://us-central1-project-sand-422218.cloudfunctions.net/Function_Rhaissa"
        curl_command = [
            "curl",
            "-H", f"Authorization: Bearer {token}",
            f"{function_url}?a={a}&b={b}"
        ]
        
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Erro ao chamar a função: {str(e)}"

# Criação da ferramenta para a Cloud Function
gcp_function_tool = Tool(
    name="calculate_sum",
    description="Calcula a soma de dois números usando a Cloud Function. Input deve ser dois números separados por vírgula, exemplo: '5,3'",
    func=lambda x: call_gcp_function(*map(int, x.split(',')))
)

# Lista de ferramentas disponíveis para o agente
tools = [search_tool, gcp_function_tool]

class CustomOutputParser(ReActSingleInputOutputParser):
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        # Remove any trailing/leading whitespace
        text = text.strip()
        
        if "Final Answer:" in text:
            # Extract the final answer
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text
            )
            
        # Try to parse out action and action input
        action_match = re.search(r"Action: (.*?)[\n]*Action Input:[\s]*(.*?)(?:\n|$)", text, re.DOTALL)
        if not action_match:
            # If no action/input found but there's a thought, continue the chain
            if "Thought:" in text:
                return AgentAction(tool="search_knowledge_base", tool_input="continue", log=text)
            raise ValueError(f"Could not parse action and action input from text: {text}")
            
        action = action_match.group(1).strip()
        action_input = action_match.group(2).strip()
        
        return AgentAction(tool=action, tool_input=action_input, log=text)

# Define o template do prompt para o agente Gemini
template = """Você é a Rhaissa, analista do time de People e RH da empresa. Tem o objetivo de ajudar a buscar informações sobre funcionários e políticas da empresa.

Você tem acesso às seguintes ferramentas:

{tools}

Quando precisar calcular somas, use a ferramenta calculate_sum fornecendo dois números separados por vírgula.
Para buscar informações sobre a empresa e funcionarios, use a ferramenta search_knowledge_base.

Use o formato EXATO abaixo para suas respostas:

Thought: Primeiro analise o que precisa fazer
Action: Nome da ferramenta a ser usada
Action Input: Input para a ferramenta
(aguarde a observação)
Thought: Analise o resultado e decida se precisa de mais informações
Action/Final Answer: Use outra ferramenta ou dê a resposta final

Pergunta: {input}

{agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)

# Inicialização do modelo com configurações ajustadas
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro-preview-03-25",
    google_api_key=os.getenv('GOOGLE_API_KEY'),
    temperature=0.7,
    convert_system_message_to_human=True,
    max_output_tokens=1024
)

# Configura o agente com o parser customizado
agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
        "tools": lambda x: "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
    }
    | prompt
    | llm
    | CustomOutputParser()
)

# Cria o executor do agente com configurações otimizadas
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5,
    early_stopping_method="generate"
)

def answer_question(question: str) -> str:
    try:
        response = agent_executor.invoke({"input": question})
        return response.get("output", "Desculpe, não consegui processar sua solicitação.")
    except Exception as e:
        return f"Erro ao processar sua pergunta: {str(e)}"

if __name__ == "__main__":
    while True:
        question = input("\nFaça uma pergunta (ou 'sair' para encerrar): ")
        if question.lower() == 'sair':
            break
        print("\nResposta:", answer_question(question))