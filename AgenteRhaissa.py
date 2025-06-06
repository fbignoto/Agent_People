import os
import subprocess
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.tools import Tool
from google.cloud import storage
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import ChatVertexAI


# Configurações iniciais
load_dotenv()

# Criação do modelo Gemini
chat_model = ChatVertexAI(
    model_name="gemini-2.0-flash-lite-001",      
    temperature=0.7,
    project=os.getenv('GOOGLE_CLOUD_PROJECT'),        
    location=os.getenv('GOOGLE_CLOUD_LOCATION'),           
)

system_prompt = SystemMessage(
    """
    Você é a Rhaissa, funcionária do RH da empresa. 
    Você pode responder perguntas sobre políticas da empresa, funcionários, treinamentos e férias.
    Sempre consulte a data atual antes de responder perguntas relacionadas a datas.
    Use as ferramentas disponíveis para buscar informações quando necessário.
    Se não souber a resposta, diga que não tem certeza ou que não pode ajudar.
    """
)

# Knowledge Base
storage_client = storage.Client()
bucket_name = os.getenv('GCP_BUCKET_NAME')
bucket = storage_client.bucket(bucket_name)

def download_from_gcs(blob_name: str, local_path: str):
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)

def create_knowledge_base():
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

knowledge_base = create_knowledge_base()

search_tool = create_retriever_tool(
    retriever=knowledge_base.as_retriever(),
    name="search_knowledge_base",
    description="Útil para buscar informações sobre funcionários, políticas da empresa, treinamentos, e férias."
)

# Tools
def call_gcp_function() -> str:
    """Faz uma chamada para a Cloud Function no GCP"""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True,
            text=True,
            check=True
        )
        token = result.stdout.strip()
        function_url = os.getenv('GCP_FUNCTION_GET_TIME')
        curl_command = [
            "curl",
            "-H", f"Authorization: Bearer {token}",
            f"{function_url}"
        ]
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Erro ao chamar a função: {str(e)}"

gcp_function_tool = Tool(
    name="Buscar_diaatual",
    description="Faz uma chamada para a Cloud Function no GCP que retorna o dia atual.",
    func=lambda x: call_gcp_function()
)

tools = [gcp_function_tool, search_tool]

# Agente
agent = create_react_agent(chat_model, tools)

def execute(agent, query):
    response = agent.invoke({
        'messages': [
            system_prompt,
            HumanMessage(query)
        ]
    })
    
    ai_response = response['messages'][-1].content
    print(f"Resposta do agente: {ai_response}")
    return ai_response

while True:
    consulta = input("- Digite sua pergunta (digite 'sair' para encerrar): ")
    if consulta.lower() == 'sair':
        print("Encerrando...")
        break
    execute(agent, consulta)