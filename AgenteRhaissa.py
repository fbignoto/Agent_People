import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.load_tools import load_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite import SqliteSaver

# Carrega variáveis de ambiente
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

# Inicializa modelo LLM
chat_model = ChatOpenAI(api_key=api_key, model='gpt-4o')

# Carrega ferramentas
tools = load_tools(["arxiv", "dalle-image-generator"])

memory = SqliteSaver.from_conn_string(':agent_history:')

system_prompt = SystemMessage(
   """
   You are a helpful bot named Chandler. Your task is to explain topics
   asked by the user via three mediums: text, image or video.
  
   If the asked topic is best explained in text format, use the Wikipedia tool.
   If the topic is best explained by showing a picture of it, generate an image
   of the topic using Dall-E image generator and print the image URL.
   Finally, if video is the best medium to explain the topic, conduct a YouTube search on it
   and return found video links.
   """
)

# Cria agente ReAct com ferramentas
agent = create_react_agent(chat_model, tools)

def execute(agent, query):
    response = agent.invoke({
        'messages': [
            system_prompt,
            HumanMessage(query)
        ]
    })
    
    # Get only the last message (agent's response)
    ai_response = response['messages'][-1].content
    print(f"Resposta do agente: {ai_response}")
    return ai_response

while True:
    consulta = input("- Digite sua pergunta (digite 'sair' para encerrar): ")
    if consulta.lower() == 'sair':
        print("Encerrando...")
        break
    execute(agent, consulta)