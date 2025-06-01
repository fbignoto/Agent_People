import os
from typing import List
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from google.cloud import storage
import pandas as pd
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

prompt = ChatPromptTemplate.from_messages([
    ("system", """Você é um assistente que ajuda a buscar informações sobre funcionários e políticas da empresa.
    Use a base de conhecimento para responder perguntas sobre:
    - Datas de aniversário e informações de funcionários
    - Períodos de férias
    - Treinamentos pendentes
    - Políticas da empresa
    
    Seja conciso e direto nas respostas."""),
    ("human", "{input}")
])

# Inicialização do modelo
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro-preview-03-25",
    google_api_key=os.getenv('GOOGLE_API_KEY'),
    temperature=0.7,
    convert_system_message_to_human=True
)

def answer_question(question: str) -> str:
    # Busca documentos relevantes
    docs = knowledge_base.similarity_search(question, k=3)
    context = "\n".join([doc.page_content for doc in docs])
    
    # Cria mensagem com contexto
    messages = prompt.format_messages(
        input=f"Com base no seguinte contexto, responda: {question}\n\nContexto: {context}"
    )
    
    # Gera resposta
    response = llm(messages)
    return response.content

if __name__ == "__main__":
    while True:
        question = input("\nFaça uma pergunta (ou 'sair' para encerrar): ")
        if question.lower() == 'sair':
            break
        print("\nResposta:", answer_question(question))