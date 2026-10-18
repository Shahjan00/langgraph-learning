from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage
from typing import TypedDict, Annotated
from dotenv import load_dotenv
import sqlite3

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

import requests
import os

import logging

logging.getLogger("google_genai.models").setLevel(logging.ERROR)

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model = 'gemini-3.5-flash-lite'
)

# Tools List

searchtool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(num1 : int, num2 : int, operation : str) -> dict:
    """
    Perform basic arthmetic operations on two number.
    Supported operations : add, sub, mul, div
    """

    try :
        if operation == 'add':
            result = num1 + num2
        elif operation == 'sub':
            result = num1 - num2
        elif operation == 'mul':
            result = num1 * num2
        elif operation == 'div':
            if num2 == 0:
                return {'error' : 'Division by Zero is not allowed'}
            else:
                result = num1 / num2
        else:
            return {'error' : f'Unsupported Operation: {operation}'}

        return {'Num1' : num1, 'Num2' : num2, 'Operation' : operation, 'result' : result}
    except Exception as e:
        return {'error' : str(e)}

@tool
def get_stock_price(symbol : str) -> dict:
    """
    Fetch Latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')
    using Alpha Vantage with api key in the URL
    """
    api_key = os.getenv('Alpha_Vantage_API_KEY')
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&interval=5min&apikey={api_key}'
    r = requests.get(url)
    return r.json()


conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)

class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]

tools = [calculator, get_stock_price, searchtool]

llm_with_tools = llm.bind_tools(tools)

def chatNode(state: ChatState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)

    return {'messages':[response]}

tool_node = ToolNode(tools)

graph = StateGraph(ChatState)

graph.add_node('chatNode',chatNode)
graph.add_node('tools', tool_node)

graph.add_edge(START, 'chatNode')
graph.add_conditional_edges('chatNode', tools_condition)
graph.add_edge('tools', 'chatNode')


checkpointer = SqliteSaver(conn=conn)

chatbot = graph.compile(checkpointer=checkpointer)


def get_all_thread():
    all_threads = set()

    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)


# while True:
#     user_input = input("User : ")
#     if user_input.strip().lower() in ['quit', 'exit', 'bye']:
#         print("Ai : Byee have a Good Day...")
#         break

#     initial_state = {
#         'messages' : [HumanMessage(content=user_input)]
#     }
#     config = {'configurable' : {'thread_id' : thread_id}}

#     # response = chatbot.invoke(initial_state, config=config)['messages'][-1].text
#     print(f"Ai : ", end="")
    
#     for message_chunk, metadata in  chatbot.stream(
#         initial_state,
#         config=config,
#         stream_mode='messages'
#     ):
#         if message_chunk.content:
#             print(message_chunk.text, end = " ", flush=True)

#     print("")



