from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import logging

from open_webui.utils.auth import get_verified_user
from open_webui.utils.ragflow_assistant import get_assistant, get_kbs, update_assistant, get_accessible_kbs
from open_webui.models.users import Users
from open_webui.config import RAGFLOW_TAVILY_API_KEY
log = logging.getLogger(__name__)

router = APIRouter()


class KnowledgeBase(BaseModel):
    kb_id: str
    kb_name: str
    enabled: bool = True


class AssistantInfo(BaseModel):
    assistant_id: str
    kb_ids: List[str]
    knowledge_bases: List[KnowledgeBase]
    tavily_api_key: Optional[str] = None
    tavily_enabled: bool = False


class UpdateKnowledgeBaseRequest(BaseModel):
    assistant_id: str
    kb_ids: List[str]


class UpdateTavilyRequest(BaseModel):
    assistant_id: str
    tavily_enabled: bool = False


@router.get("/assistant/{assistant_id}/info")
async def get_assistant_info(
    assistant_id: str,
) -> AssistantInfo:
    """
    获取assistant的完整信息，包括kb_ids、知识库列表和tavily_api_key
    当选择rag_flow_webapi_pipeline_cs模型时调用此接口
    """
    try:
        # 获取assistant信息
        assistant_response = await get_assistant(assistant_id)
        print("assistant_response", assistant_response)
        
        if 'data' not in assistant_response:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        assistant_data = assistant_response['data']
        kb_ids = assistant_data.get('kb_ids', [])
        kb_names = assistant_data.get('kb_names', [])
        prompt_config = assistant_data.get('prompt_config')
        if 'tavily_api_key' in prompt_config:
            tavily_api_key = prompt_config['tavily_api_key']
        else:
            tavily_api_key = None
        
        knowledge_bases = []
        
        for kb_id, kb_name in zip(kb_ids, kb_names):
            knowledge_bases.append(KnowledgeBase(
                kb_id=kb_id,
                kb_name=kb_name,
                enabled=True
            ))
        
        accessible_kbs = await get_accessible_kbs(assistant_id)
        
        if 'data' in accessible_kbs:
            for kb in accessible_kbs['data']:
                if kb['kb_id'] not in kb_ids and kb['kb_id'] not in [kb.kb_id for kb in knowledge_bases]:
                    knowledge_bases.append(KnowledgeBase(
                        kb_id=kb['kb_info']['id'],
                        kb_name=kb['kb_info']['name'],
                        enabled=False
                    ))

        return AssistantInfo(
            assistant_id=assistant_id,
            kb_ids=kb_ids,
            knowledge_bases=knowledge_bases,
            tavily_api_key=tavily_api_key,
            tavily_enabled=bool(tavily_api_key)
        )
        
    except Exception as e:
        log.error(f"Error getting assistant info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistant/{assistant_id}/knowledge-bases")
async def get_assistant_knowledge_bases(
    assistant_id: str,
    user=Depends(get_verified_user)
) -> AssistantInfo:
    """
    获取assistant的知识库信息
    当选择rag_flow_webapi_pipeline_cs模型时调用此接口
    """
    try:
        # 获取assistant信息
        assistant_response = await get_assistant(assistant_id)
        
        if 'data' not in assistant_response:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        assistant_data = assistant_response['data']
        kb_ids = assistant_data.get('kb_ids', [])
        
        knowledge_bases = []
        
        # 如果有知识库ID，获取知识库信息
        if kb_ids:
            kb_ids_str = ','.join(kb_ids) if isinstance(kb_ids, list) else kb_ids
            kbs_response = await get_kbs(kb_ids_str)
            
            if 'data' in kbs_response:
                for kb in kbs_response['data']:
                    knowledge_bases.append(KnowledgeBase(
                        kb_id=kb['id'],
                        kb_name=kb['name'],
                        enabled=True
                    ))
        
        return AssistantInfo(
            assistant_id=assistant_id,
            kb_ids=kb_ids,
            knowledge_bases=knowledge_bases,
            tavily_api_key=assistant_data.get('tavily_api_key'),
            tavily_enabled=bool(assistant_data.get('tavily_api_key'))
        )
        
    except Exception as e:
        log.error(f"Error getting assistant knowledge bases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/update-knowledge-bases")
async def update_assistant_knowledge_bases(
    request: UpdateKnowledgeBaseRequest,
):
    """
    更新assistant的知识库配置
    当用户切换知识库开关时调用此接口
    """
    try:
        # 获取当前assistant信息
        assistant_response = await get_assistant(request.assistant_id)
        
        if 'data' not in assistant_response:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        assistant_data = assistant_response['data']
        
        # 构造更新数据，按照update载荷的结构
        update_payload = {
            "dialog_id": assistant_data.get('id'),  # 使用assistant的id作为dialog_id
            "name": assistant_data.get('name'),
            "description": assistant_data.get('description'),
            "icon": assistant_data.get('icon', ""),
            "language": assistant_data.get('language'),
            "prompt_config": assistant_data.get('prompt_config', {}),
            "kb_ids": request.kb_ids,  # 更新的知识库IDs
            "llm_id": assistant_data.get('llm_id'),
            "llm_setting": assistant_data.get('llm_setting', {}),
            "similarity_threshold": assistant_data.get('similarity_threshold'),
            "vector_similarity_weight": assistant_data.get('vector_similarity_weight'),
            "top_n": assistant_data.get('top_n'),
            "rerank_id": assistant_data.get('rerank_id', "")
        }
        
        # 更新assistant
        update_response = await update_assistant(update_payload)
        
        if 'code' in update_response and update_response['code'] != 0:
            raise HTTPException(status_code=400, detail=update_response.get('message', 'Update failed'))
        
        return {"success": True, "message": "Knowledge bases updated successfully"}
        
    except Exception as e:
        log.error(f"Error updating assistant knowledge bases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/{model_id}/knowledge-bases")
async def get_model_knowledge_bases(
    model_id: str,
    user=Depends(get_verified_user)
) -> AssistantInfo:
    """
    根据模型ID获取知识库信息
    专门为rag_flow_webapi_pipeline_cs模型使用
    """
    if model_id != "rag_flow_webapi_pipeline_cs":
        raise HTTPException(status_code=400, detail="This endpoint is only for rag_flow_webapi_pipeline_cs model")
    
    try:
        # 从用户信息中获取assistant_id
        assistant_id = getattr(user, 'assistant_id', None)
        
        if not assistant_id:
            raise HTTPException(status_code=400, detail="User does not have an associated assistant")
        
        return await get_assistant_knowledge_bases(assistant_id, user)
        
    except Exception as e:
        log.error(f"Error getting model knowledge bases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant/update-tavily")
async def update_assistant_tavily(
    request: UpdateTavilyRequest,
):
    """
    更新assistant的tavily搜索配置
    当用户切换联网搜索时调用此接口
    """
    try:
        # 获取当前assistant信息
        assistant_response = await get_assistant(request.assistant_id)
        
        if 'data' not in assistant_response:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        assistant_data = assistant_response['data']
        
        # 获取当前的prompt_config并更新tavily_api_key
        prompt_config = assistant_data.get('prompt_config', {}).copy()
        if request.tavily_enabled:
            prompt_config['tavily_api_key'] = RAGFLOW_TAVILY_API_KEY
        elif 'tavily_api_key' in prompt_config:
            # 如果禁用tavily，移除tavily_api_key
            del prompt_config['tavily_api_key']
        
        # 构造更新数据，按照update载荷的结构
        update_payload = {
            "dialog_id": assistant_data.get('id'),  # 使用assistant的id作为dialog_id
            "name": assistant_data.get('name'),
            "description": assistant_data.get('description'),
            "icon": assistant_data.get('icon', ""),
            "language": assistant_data.get('language'),
            "prompt_config": prompt_config,  # 更新的prompt_config
            "kb_ids": assistant_data.get('kb_ids', []),
            "llm_id": assistant_data.get('llm_id'),
            "llm_setting": assistant_data.get('llm_setting', {}),
            "similarity_threshold": assistant_data.get('similarity_threshold'),
            "vector_similarity_weight": assistant_data.get('vector_similarity_weight'),
            "top_n": assistant_data.get('top_n'),
            "rerank_id": assistant_data.get('rerank_id', "")
        }
        
        # 更新assistant
        update_response = await update_assistant(update_payload)
        
        if 'code' in update_response and update_response['code'] != 0:
            raise HTTPException(status_code=400, detail=update_response.get('message', 'Update failed'))
        
        return {"success": True, "message": "Tavily configuration updated successfully"}
        
    except Exception as e:
        log.error(f"Error updating assistant tavily config: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 