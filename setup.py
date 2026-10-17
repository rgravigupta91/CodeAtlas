import os
#from gen_ai_hub.proxy.langchain import ChatOpenAI
from langchain_openai import ChatOpenAI
# from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
import json
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
    model=os.getenv("MODEL"),
)