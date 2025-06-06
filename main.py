import os
import subprocess
from flask import Flask, jsonify
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.tools import Tool
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI

app = Flask(__name__)

# Configurações iniciais
load_dotenv()

chat_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-04-17",
    temperature=0.7        
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
# storage_client = storage.Client()
# bucket_name = os.getenv('GCP_BUCKET_NAME', 'bucket_rhaissa')
# bucket = storage_client.bucket(bucket_name)

def download_from_gcs(blob_name: str, local_path: str):
    print(f"Downloading {blob_name} from GCS bucket {bucket_name} to {local_path}")
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)

def create_knowledge_base():
    print("Creating knowledge base from GCS files")
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

# Tools
def call_gcp_function() -> str:
    """Faz uma chamada para a Cloud Function no GCP"""

    print("Chamando a Cloud Function para obter o dia atual")
    try:
        # print("Obtendo token de identidade do GCP")
        # result = subprocess.run(
        #     ["gcloud", "auth", "print-identity-token"],
        #     capture_output=True,
        #     text=True,
        #     check=True
        # )
        # token = result.stdout.strip()

        function_url = os.getenv('GCP_FUNCTION_GET_TIME')
        print(f"Function URL: {function_url}")
        curl_command = [
            "curl",
            f"{function_url}"
        ]
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        print(f"Response from GCP function: {result}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Erro ao chamar a função: {str(e)}"

def execute(agent, query):
    print("Iniciando execução do agente")
    response = agent.invoke({
        'messages': [
            system_prompt,
            HumanMessage(query)
        ]
    })
    
    ai_response = response['messages'][-1].content
    print(f"Resposta do agente: {ai_response}")
    return ai_response

@app.route('/', methods=['POST'])
def handle_request(request):
    request_json = request.get_json(silent=True)
    query = request_json.get('query') if request_json else ''
    print(f"Received query: {query}")
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        gcp_function_tool = Tool(
            name="Buscar_dia_atual",
            description="Faz uma chamada para a Cloud Function no GCP que retorna o dia atual.",
            func=lambda _: call_gcp_function()
        )

        # knowledge_base = create_knowledge_base()

        # search_tool = create_retriever_tool(
        #     retriever=knowledge_base.as_retriever(),
        #     name="search_knowledge_base",
        #     description="Útil para buscar informações sobre funcionários, políticas da empresa, treinamentos, e férias."
        # )

        tools = [gcp_function_tool]

        agent = create_react_agent(chat_model, tools)

        response = execute(agent, query)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)