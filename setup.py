import os
#from gen_ai_hub.proxy.langchain import ChatOpenAI
#from langchain_openai import ChatOpenAI
from langchain_openai import OpenAI
#from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
import json
from dotenv import load_dotenv
# --- Setup environment ---
load_dotenv()

""" def set_env_vars():
    with open("../irpa-r1208-hands-on-exercises-sk.json", "r") as key_file:
        svcKey = json.load(key_file)

    env_vars = {    
        "AICORE_AUTH_URL": svcKey["url"],
        "AICORE_CLIENT_ID": svcKey["clientid"],
        "AICORE_CLIENT_SECRET": svcKey["clientsecret"],
        "AICORE_RESOURCE_GROUP": "default",
        "AICORE_BASE_URL": svcKey["serviceurls"]["AI_API_URL"]
    }
    os.environ.update(env_vars) """

#set_env_vars()

#proxy_client = get_proxy_client('gen-ai-hub')
#llm = ChatOpenAI(proxy_model_name = 'gpt-4o', proxy_client = proxy_client, temperature=0.0)
""" llm = ChatOpenAI(
    base_url="http://localhost:6655/litellm/v1",
    api_key="a99d909b-7d26-42b0-aca5-0d4159e20f09",
    model="anthropic--claude-4.6-sonnet",
) """

llm = OpenAI(model='gpt-3.5-turbo-instruct')
print(llm.invoke("What is the capital of France?"))