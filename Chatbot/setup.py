import os
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(
    model="gpt-4o-mini",   # or another chat model you have access to
    temperature=0
)
