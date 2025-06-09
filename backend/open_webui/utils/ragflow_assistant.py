import requests
from open_webui.config import TENANT_ID, KNOWLEDGE_BASE_URL

async def create_assistant(user_id, authorization, cookies):
    # 获取可以访问的知识库id列表
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/permission/kb/accessible?tenant_id={TENANT_ID}&user_id={user_id}"
    response = requests.get(api_url, headers={'Content-Type': 'application/json','Authorization': authorization,'Cookie': cookies})
    print("可以访问的知识库列表：",response.json())
    kb_ids = [kb['kb_id'] for kb in response.json()['data']]
    # kb_ids去重 
    kb_ids = list(set(kb_ids))

    # 创建assistant
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/dialog/set"
    payload = {
        "name": "小智3.0",
        "description": "小智3.0pipeline",
        "icon": "",
        "language": "Chinese",
        "prompt_config": {
            "empty_response": "",
            "prologue": "你好！ 我是你的助理，有什么可以帮到你的吗？",
            "quote": True,
            "keyword": False,
            "tts": False,
            "system": "你是一个智能助手，请总结知识库的内容来回答问题，请列举知识库中的数据详细回答。当所有知识库内容都与问题无关时，你的回答必须包括“知识库中未找到您要的答案！”这句话。回答需要考虑聊天历史。\n        以下是知识库：\n        {knowledge}\n        以上是知识库。",
            "refine_multiturn": False,
            "use_kg": False,
            "reasoning": False,
            "parameters": [
                {
                    "key": "knowledge",
                    "optional": False
                }
            ]
        },
        "kb_ids": kb_ids,
        "llm_id": "Qwen3:32B___VLLM@VLLM",
        "llm_setting": {
            "temperature": 0.1,
            "top_p": 0.3,
            "presence_penalty": 0.4,
            "frequency_penalty": 0.7
        },
        "similarity_threshold": 0.2,
        "vector_similarity_weight": 0.3,
        "top_n": 8,
        "user_id": user_id
    }
    response = requests.post(api_url, json=payload, headers={'Content-Type': 'application/json','Authorization': authorization,'Cookie': cookies})
    # print("创建assistant：",response.json())
    assistant_id = response.json()['data']['id']
    return assistant_id

async def get_assistant(assistant_id):
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/dialog/get?dialog_id={assistant_id}"
    response = requests.get(api_url, headers={'Content-Type': 'application/json'})
    return response.json()

async def update_assistant(payload):
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/dialog/set_assistant"
    response = requests.post(api_url, json=payload, headers={'Content-Type': 'application/json'})
    return response.json()
    
async def get_kbs(kb_ids):
    if isinstance(kb_ids, list):
        kb_ids_str = ','.join(kb_ids)
    else:
        kb_ids_str = kb_ids
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/kb/get?kb_ids={kb_ids_str}"
    response = requests.get(api_url, headers={'Content-Type': 'application/json'})
    return response.json()

# 获取用户可以访问的知识库列表
async def get_accessible_kbs(assistant_id):
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/permission/kb/assistant_accessible?assistant_id={assistant_id}"
    response = requests.get(api_url, headers={'Content-Type': 'application/json'})
    return response.json()
    