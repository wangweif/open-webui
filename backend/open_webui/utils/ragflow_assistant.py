import aiohttp
import asyncio
from open_webui.config import TENANT_ID, KNOWLEDGE_BASE_URL, BASE_KB_ID
import requests
from open_webui.utils.auth import create_token
import logging
log = logging.getLogger(__name__)

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

async def assign_base_kb_permission(user_id):
    # 获取农科小智知识库权限列表
    token = create_token(data={"id": TENANT_ID})
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/permission/kb/{BASE_KB_ID}/authorized_users"
    teamRes = requests.get(api_url,headers={'Content-Type': 'application/json','Cookie': 'token=' + token})
    response_data = teamRes.json() if teamRes.status_code == 200 else {}
    data = response_data.get('data', None)
    log.info(f"-------------农科小智知识库权限列表：{data}")
    if data == None:
        data = [{'user_id':user_id,'permission_types':['read']}]
    else:
        # 统一将permission_type转换为permission_types
        for item in data:
            if 'permission_type' in item:
                item['permission_types'] = [item.pop('permission_type')]
        data.append({'user_id':user_id,'permission_types':['read']})
    payload = {
        "permissions": data
    }

    # 更新农科小智知识库权限列表
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/permission/kb/{BASE_KB_ID}/permissions"
    teamRes = requests.post(api_url,json=payload,headers={'Content-Type': 'application/json','Cookie': 'token=' + token})
    if teamRes.status_code != 200:
        return None
    
async def create_assistant(user_id):
    # 获取可以访问的知识库id列表
    token = create_token(data={"id": TENANT_ID})
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/permission/kb/accessible?tenant_id={TENANT_ID}&user_id={user_id}"
    
    response = requests.get(api_url,headers={'Content-Type': 'application/json','Cookie': 'token=' + token})
    if response.status_code != 200:
        log.error(f"获取知识库列表失败，状态码: {response.status_code}")
        raise Exception(f"Failed to get accessible knowledge bases: {response.status_code}")
    
    response_data = response.json()
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
            "keyword": False,
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
        "top_n": 30,
        "top_k": 2048,
        "user_id": user_id
    }
    
    response = requests.post(api_url,json=payload,headers={'Content-Type': 'application/json','Cookie': 'token=' + token})
    if response.status_code != 200:
        log.error(f"创建助手失败，状态码: {response.status_code}")
        raise Exception(f"Failed to create assistant: {response.status_code}")
    
    response_data = response.json()
    assistant_id = response_data['data']['id']
    return assistant_id


async def create_assistant_for_app(
    name: str, description: str, user_id: str, kb_ids: list = None
):
    token = create_token(data={"id": TENANT_ID})
    """通用的assistant创建函数"""
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/dialog/set"

    # 如果没有提供知识库ID，使用空列表
    if kb_ids is None:
        kb_ids = []

    payload = {
        "name": name,
        "description": description,
        "icon": "",
        "language": "Chinese",
        "prompt_config": {
            "empty_response": "",
            "prologue": "你好！ 我是你的助理，有什么可以帮到你的吗？",
            "quote": True,
            "keyword": False,
            "tts": False,
            "system": '你是一个智能助手，请总结知识库的内容来回答问题，请列举知识库中的数据详细回答。当所有知识库内容都与问题无关时，你的回答必须包括"知识库中未找到您要的答案！"这句话。回答需要考虑聊天历史。\n        以下是知识库：\n        {knowledge}\n        以上是知识库。',
            "refine_multiturn": False,
            "use_kg": False,
            "reasoning": False,
            "parameters": [{"key": "knowledge", "optional": False}],
        },
        "kb_ids": kb_ids,
        "llm_id": "Qwen3:32B___VLLM@VLLM",
        "llm_setting": {
            "temperature": 0.1,
            "top_p": 0.3,
            "presence_penalty": 0.4,
            "frequency_penalty": 0.7,
        },
        "similarity_threshold": 0.2,
        "vector_similarity_weight": 0.3,
        "rerank_id": "bge-reranker-v2-m3___VLLM@VLLM",
        "top_n": 30,
        "top_k": 2048,
        "user_id": user_id,
    }
    session = await get_session()
    headers = {"Content-Type": "application/json", "Cookie": "token=" + token}
    async with session.post(api_url, json=payload, headers=headers) as response:
        return await response.json()


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

# 将用户添加到UserTenant表
async def add_user_to_user_tenant(tenant_id,email):
    token = create_token(data={"id": tenant_id})
    api_url = f"{KNOWLEDGE_BASE_URL}/v1/tenant/{tenant_id}/user"
    payload = {
        "email": email
    }
    response = requests.post(api_url,json=payload,headers={'Content-Type': 'application/json','Cookie': 'token=' + token})
    response_data = response.json()
    if response_data.get('code') != 0:
        log.error(f"将用户添加到UserTenant表失败，状态码: {response_data.get('code')},消息: {response_data.get('message')}")
        return False
    return True

def upload_file_to_kb(file_path, file_name, kb_id):
    """将文件上传到知识库并触发解析
    
    Args:
        file_path (str): 上传的文件路径
        file_name (str): 上传的文件名称
        kb_id (str): 知识库ID
    Returns:
        bool: 上传和解析是否成功
    """
    try:
        api_url = "https://know.baafs.net.cn/v1/document/upload"
        
        # 读取文件内容
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f, 'application/octet-stream')}
            data = {
                "kb_id": kb_id,
                "webkitRelativePath": file_name,
                "parser_id": "naive"
            }
            
            response = requests.post(api_url, files=files, data=data, headers=get_header())
            
            # 检查响应状态码
            if response.status_code != 200:
                log.error(f"上传文件到知识库失败，文件: {file_name}, HTTP状态码: {response.status_code}")
                return False
            
            try:
                response_data = response.json()
                log.info(f"上传响应数据: {response_data}")
                
                # 检查响应格式和状态
                if response_data.get('code') != 0:
                    log.error(f"上传文件到知识库失败，文件: {file_name}, 状态码: {response_data.get('code')}, 消息: {response_data.get('message')}")
                    return False

                # 获取上传成功的文件信息
                uploaded_files = response_data.get('data', [])
                if not uploaded_files:
                    log.error(f"上传成功但未返回文件信息，文件: {file_name}, 响应: {response_data}")
                    return False
                
                if not isinstance(uploaded_files, list) or len(uploaded_files) == 0:
                    log.error(f"文件信息格式错误，文件: {file_name}, data字段: {uploaded_files}")
                    return False
                
                # 获取第一个文件的ID
                first_file = uploaded_files[0]
                if not isinstance(first_file, dict):
                    log.error(f"文件信息不是字典格式，文件: {file_name}, 第一个文件: {first_file}")
                    return False
                
                file_id = first_file.get('id')
                if not file_id:
                    log.error(f"未获取到文件ID，文件: {file_name}, 文件信息: {first_file}")
                    return False
                
                log.info(f"文件 {file_name} 成功上传到知识库 {kb_id}，文件ID: {file_id}")
                
                # 调用解析接口
                parse_result = parse_chunks([file_id], run=1)
                if parse_result and parse_result.get('code') == 0:
                    log.info(f"文件 {file_name} 在知识库 {kb_id} 中的解析任务启动成功")
                else:
                    log.error(f"文件 {file_name} 在知识库 {kb_id} 中的解析任务启动失败: {parse_result}")
                
                return True
                
            except ValueError as e:
                log.error(f"JSON解析失败，文件: {file_name}, 错误: {str(e)}, 响应内容: {response.text}")
                return False
                
    except Exception as e:
        log.error(f"上传文件到知识库时发生异常，文件: {file_name}, 错误: {str(e)}")
        return False
        
def parse_chunks(doc_ids, run=1):
    """解析文档

    Args:
        doc_ids (str): 文档 ID 列表
        run (int, optional): 是否可用状态. Defaults to 1.

    Returns:
        dict: 解析文档后的结果
    """
    url = f"https://know.baafs.net.cn/v1/document/run"
    data = {"delete":False,"doc_ids":doc_ids,"run":run}
    response = requests.post(url, json=data, headers=get_header())
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "retcode": response.status_code,
            "retmsg": "Failed to parse_chunks: {doc_ids}"
        }

def get_header():
    return {
        'authorization': create_token(data={"id": TENANT_ID})
    }