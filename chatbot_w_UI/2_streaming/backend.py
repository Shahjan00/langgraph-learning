from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage
from typing import TypedDict, Annotated
from dotenv import load_dotenv

import logging

logging.getLogger("google_genai.models").setLevel(logging.ERROR)

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model = 'gemini-3.5-flash-lite'
)

class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]

def chatNode(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)

    return {'messages':[response]}

graph = StateGraph(ChatState)

graph.add_node('chatNode',chatNode)

graph.add_edge(START, 'chatNode')
graph.add_edge('chatNode', END)

checkpointer = MemorySaver()

chatbot = graph.compile(checkpointer=checkpointer)

# thread_id = 1

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



