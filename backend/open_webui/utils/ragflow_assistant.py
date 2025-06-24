import aiohttp
import asyncio
from open_webui.config import TENANT_ID, KNOWLEDGE_BASE_URL

# HTTP 请求超时配置
REQUEST_TIMEOUT = 10  # 10秒超时

# 全局 aiohttp session，使用连接池复用连接
_session = None

async def get_session():
    """获取全局 aiohttp session，支持连接池复用"""
    global _session
    if _session is None or _session.closed:
        connector = aiohttp.TCPConnector(
            limit=20,  # 总连接池大小
            limit_per_host=10,  # 每个主机的连接数
            ttl_dns_cache=300,  # DNS 缓存 5 分钟
            use_dns_cache=True,
        )
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        _session = aiohttp.ClientSession(connector=connector, timeout=timeout)
    return _session

async def create_assistant(user_id, authorization, cookies):
    # 获取可以访问的知识库id列表
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/permission/kb/accessible?tenant_id={TENANT_ID}&user_id={user_id}"
    
    session = await get_session()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': authorization,
        'Cookie': cookies
    }
    async with session.get(api_url, headers=headers) as response:
        response_data = await response.json()
        print("可以访问的知识库列表：", response_data)
        kb_ids = [kb['kb_id'] for kb in response_data['data']]
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
            "keyword": True,
            "tts": False,
            "system": "你是一个智能助手，请总结知识库的内容来回答问题，请列举知识库中的数据详细回答。当所有知识库内容都与问题无关时，你的回答必须包括\"知识库中未找到您要的答案！\"这句话。回答需要考虑聊天历史。\n        以下是知识库：\n        {knowledge}\n        以上是知识库。",
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
        "rerank_id": "bge-reranker-v2-m3___VLLM@VLLM",
        "top_n": 14,
        "user_id": user_id
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': authorization,
        'Cookie': cookies
    }
    async with session.post(api_url, json=payload, headers=headers) as response:
        response_data = await response.json()
        assistant_id = response_data['data']['id']
        return assistant_id

async def get_assistant(assistant_id):
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/dialog/get?dialog_id={assistant_id}"
    
    session = await get_session()
    headers = {'Content-Type': 'application/json'}
    async with session.get(api_url, headers=headers) as response:
        return await response.json()

async def update_assistant(payload):
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/dialog/set_assistant"
    
    session = await get_session()
    headers = {'Content-Type': 'application/json'}
    async with session.post(api_url, json=payload, headers=headers) as response:
        return await response.json()
    
async def get_kbs(kb_ids):
    if isinstance(kb_ids, list):
        kb_ids_str = ','.join(kb_ids)
    else:
        kb_ids_str = kb_ids
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/kb/get?kb_ids={kb_ids_str}"
    
    session = await get_session()
    headers = {'Content-Type': 'application/json'}
    async with session.get(api_url, headers=headers) as response:
        return await response.json()

# 获取用户可以访问的知识库列表
async def get_accessible_kbs(assistant_id):
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/permission/kb/assistant_accessible?assistant_id={assistant_id}"
    
    session = await get_session()
    headers = {'Content-Type': 'application/json'}
    async with session.get(api_url, headers=headers) as response:
        return await response.json()

# 清理全局 session 的函数（用于应用关闭时调用）
async def cleanup_session():
    """清理全局 aiohttp session"""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None
    