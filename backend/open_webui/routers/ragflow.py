from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import logging

from open_webui.utils.auth import get_verified_user
from open_webui.utils.ragflow_assistant import (
    get_assistant,
    get_kbs,
    update_assistant,
    get_accessible_kbs,
    create_assistant_for_app,
)
from open_webui.models.users import Users
from open_webui.models.app_sessions import AppSessions, AppSessionModel
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
    reasoning_enabled: bool = False


class UpdateKnowledgeBaseRequest(BaseModel):
    assistant_id: str
    kb_ids: List[str]


class UpdateTavilyRequest(BaseModel):
    assistant_id: str
    tavily_enabled: bool = False

class UpdateReasoningRequest(BaseModel):
    assistant_id: str
    reasoning_enabled: bool = False

class UpdateRefineMultiturnRequest(BaseModel):
    assistant_id: str
    refine_multiturn: bool = False


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
        prompt_config = assistant_data.get('prompt_config', {})
        if 'tavily_api_key' in prompt_config:
            tavily_api_key = prompt_config['tavily_api_key']
        else:
            tavily_api_key = None
        
        reasoning_enabled = prompt_config.get('reasoning', False)
        
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
            tavily_enabled=bool(tavily_api_key),
            reasoning_enabled=reasoning_enabled
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
            tavily_enabled=bool(assistant_data.get('tavily_api_key')),
            reasoning_enabled=assistant_data.get('prompt_config', {}).get('reasoning', False)
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

@router.post("/assistant/update-reasoning")
async def update_assistant_reasoning(
    request: UpdateReasoningRequest,
):
    """
    更新assistant的推理配置
    当用户切换推理时调用此接口
    """
    try:
        # 获取当前assistant信息
        assistant_response = await get_assistant(request.assistant_id)
        
        if 'data' not in assistant_response:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        assistant_data = assistant_response['data']
        
        # 获取当前的prompt_config并更新reasoning
        prompt_config = assistant_data.get('prompt_config', {}).copy()
        if request.reasoning_enabled:
            prompt_config['reasoning'] = True
            prompt_config['refine_multiturn'] = True
        elif 'reasoning' in prompt_config:
            # 如果禁用推理，移除reasoning
            del prompt_config['reasoning']
            del prompt_config['refine_multiturn']
        
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
        
        return {"success": True, "message": "Reasoning configuration updated successfully"}
        
    except Exception as e:
        log.error(f"Error updating assistant reasoning config: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

@router.post("/assistant/update-refine-multiturn")
async def update_assistant_refine_multiturn(
    request: UpdateRefineMultiturnRequest,
):
    """
    更新assistant的query refine配置
    当用户切换query refine时调用此接口
    """
    try:
        # 获取当前assistant信息
        assistant_response = await get_assistant(request.assistant_id)
        
        if 'data' not in assistant_response:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        assistant_data = assistant_response['data']
        
        # 获取当前的prompt_config并更新refine_multiturn
        prompt_config = assistant_data.get('prompt_config', {}).copy()
        if request.refine_multiturn:
            prompt_config['refine_multiturn'] = True
        elif 'refine_multiturn' in prompt_config:
            # 如果禁用query refine，移除refine_multiturn
            del prompt_config['refine_multiturn']
        
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
        
        return {"success": True, "message": "Refine multiturn configuration updated successfully"}
        
    except Exception as e:
        log.error(f"Error updating assistant refine multiturn config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 新增的app session管理相关接口
class ModelAppMapping:
    """模型到应用ID的映射"""

    MODEL_APP_ID_MAP = {
        "rag_flow_webapi_pipeline_cs": 1,
        "n8n_project_research": 2,
        "contract_review": 3,
    }

    @classmethod
    def get_app_id(cls, model_id: str) -> Optional[int]:
        return cls.MODEL_APP_ID_MAP.get(model_id)

    @classmethod
    def is_supported_model(cls, model_id: str) -> bool:
        return model_id in cls.MODEL_APP_ID_MAP

    @classmethod
    def is_supported_model_except_rag_flow(cls, model_id: str) -> bool:
        """判断是否在 MODEL_APP_ID_MAP 中，且不为 rag_flow_webapi_pipeline_cs"""
        return model_id in cls.MODEL_APP_ID_MAP and model_id != "rag_flow_webapi_pipeline_cs"


class GetOrCreateAssistantRequest(BaseModel):
    model_id: str
    user_id: str


class GetOrCreateAssistantResponse(BaseModel):
    assistant_id: str
    is_new: bool
    message: str


async def get_or_create_assistant(
    request: GetOrCreateAssistantRequest, user=Depends(get_verified_user)
) -> GetOrCreateAssistantResponse:
    """
    根据模型ID和用户ID获取或创建assistant
    专门为 n8n_project_research 和 contract_review 模型使用
    rag_flow_webapi_pipeline_cs 模型继续使用用户表中的默认 assistant_id
    """
    try:
        # rag_flow_webapi_pipeline_cs 使用用户默认的 assistant_id
        if request.model_id == "rag_flow_webapi_pipeline_cs":
            assistant_id = getattr(user, "assistant_id", None)
            if not assistant_id:
                raise HTTPException(
                    status_code=400, detail="User does not have an associated assistant"
                )
            return GetOrCreateAssistantResponse(
                assistant_id=assistant_id,
                is_new=False,
                message="Using default user assistant",
            )

        # 检查是否为支持的模型
        if not ModelAppMapping.is_supported_model(request.model_id):
            raise HTTPException(
                status_code=400,
                detail=f"Model {request.model_id} is not supported for assistant management",
            )

        # 获取app_id
        app_id = ModelAppMapping.get_app_id(request.model_id)

        # 查询是否已存在app session
        existing_session = AppSessions.get_app_session_by_app_user(
            app_id, user.ragflow_user_id
        )

        if existing_session:
            return GetOrCreateAssistantResponse(
                assistant_id=existing_session.assistant_id,
                is_new=False,
                message="Using existing assistant",
            )

        # 创建新的assistant
        assistant_name = f"Assistant for {request.model_id} - {user.ragflow_user_id}"
        assistant_description = f"Dedicated assistant for {request.model_id} model"

        create_response = await create_assistant_for_app(
            name=assistant_name, description=assistant_description, user_id=user.ragflow_user_id
        )

        if "code" in create_response and create_response["code"] != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create assistant: {create_response.get('message', 'Unknown error')}",
            )

        # 从创建响应中获取assistant_id
        if "data" not in create_response:
            raise HTTPException(
                status_code=500, detail="Invalid response from assistant creation"
            )

        new_assistant_id = create_response["data"]["id"]

        # 保存app session记录
        app_session = AppSessions.insert_new_app_session(
            app_id=app_id, user_id=user.ragflow_user_id, assistant_id=new_assistant_id
        )

        if not app_session:
            raise HTTPException(status_code=500, detail="Failed to save app session")

        return GetOrCreateAssistantResponse(
            assistant_id=new_assistant_id,
            is_new=True,
            message="Created new assistant successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting or creating assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/{model_id}/assistant")
async def get_model_assistant(
    model_id: str, user=Depends(get_verified_user)
) -> GetOrCreateAssistantResponse:
    """
    根据模型ID获取当前用户的assistant信息
    用于模型切换时获取对应的assistant_id
    """
    try:
        # 直接调用 get_or_create_assistant 逻辑
        request = GetOrCreateAssistantRequest(model_id=model_id, user_id=user.id)
        return await get_or_create_assistant(request, user)

    except Exception as e:
        log.error(f"Error getting model assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))
