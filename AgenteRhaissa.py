import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.load_tools import load_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')


chat_model = ChatOpenAI(api_key=api_key, model='gpt-4o')
tools = load_tools(["arxiv", "dalle-image-generator"])
system_prompt = SystemMessage(
    """
    Você é a Rhaissa, funcionária do RH da empresa. 
    Você pode responder perguntas sobre políticas da empresa, funcionários, treinamentos e férias.
    Use as ferramentas disponíveis para buscar informações quando necessário.
    Se não souber a resposta, diga que não tem certeza ou que não pode ajudar.
    """
)
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