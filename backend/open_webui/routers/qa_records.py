import logging
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from open_webui.models.chats import Chats
from open_webui.models.users import Users
from open_webui.utils.auth import get_admin_user
from open_webui.constants import ERROR_MESSAGES

log = logging.getLogger(__name__)

router = APIRouter()


class AttachmentInfo(BaseModel):
    """附件信息"""
    name: Optional[str] = None  # 附件名称
    type: str  # 'file' or 'image'
    id: Optional[str] = None  # 文件ID (用于访问文件内容)
    url: Optional[str] = None  # 图片URL
    content: Optional[str] = None  # 文件文本内容
    size: Optional[int] = None  # 文件大小
    content_type: Optional[str] = None  # 文件MIME类型


class QARecord(BaseModel):
    id: str
    question: str
    answer: str
    user_name: str
    user_email: str
    user_id: str
    attachments: List[AttachmentInfo]
    created_at: int
    updated_at: int
    model: str
    chat_id: Optional[str] = None


class QARecordsSearchResponse(BaseModel):
    records: List[QARecord]
    total: int


def extract_qa_records_from_chats() -> List[QARecord]:
    """从所有聊天记录中提取问答对"""
    qa_records = []
    
    try:
        # 获取所有聊天记录
        all_chats = Chats.get_chats()
        
        for chat in all_chats:
            try:
                # 获取用户信息
                user = Users.get_user_by_id(chat.user_id)
                if not user:
                    continue
                
                # 获取聊天历史中的消息
                messages_dict = chat.chat.get("history", {}).get("messages", {})
                if not messages_dict:
                    # 尝试直接从 chat.messages 获取
                    messages_dict = chat.chat.get("messages", {})
                
                if not messages_dict:
                    continue
                
                # 将消息字典转换为列表并按 ID 排序
                messages = []
                for msg_id, msg_data in messages_dict.items():
                    if isinstance(msg_data, dict):
                        msg_data['id'] = msg_id
                        messages.append(msg_data)
                
                # 按创建时间或索引排序
                # messages.sort(key=lambda x: x.get('timestamp', 0))
                
                # 提取问答对（用户消息 + 助手回复）
                i = 0
                while i < len(messages) - 1:
                    current_msg = messages[i]
                    next_msg = messages[i + 1]
                    
                    # 检查是否是用户问题后跟助手回答
                    if (current_msg.get('role') == 'user' and 
                        next_msg.get('role') == 'assistant'):
                        
                        question_content = current_msg.get('content', '')
                        answer_content = next_msg.get('content', '')
                        
                        # 跳过空内容
                        if not question_content or not answer_content:
                            i += 1
                            continue
                        
                        # 提取附件信息
                        attachments = []
                        if current_msg.get('files'):
                            for file_obj in current_msg.get('files', []):
                                if isinstance(file_obj, dict):
                                    # 直接从消息中获取文件信息
                                    file_data = file_obj.get('file', {}) if isinstance(file_obj.get('file'), dict) else {}
                                    file_meta = file_data.get('meta', {}) if isinstance(file_data.get('meta'), dict) else {}
                                    
                                    # 获取文件内容
                                    content = None
                                    if file_data and isinstance(file_data, dict):
                                        data_content = file_data.get('data', {})
                                        if isinstance(data_content, dict):
                                            content = data_content.get('content')
                                    
                                    if file_obj.get('type') == 'image':
                                        attachment = AttachmentInfo(
                                            name=None,
                                            type='image',
                                            id=None,
                                            url=file_obj.get('url'),
                                            content=None,
                                            size=None,
                                            content_type=None
                                        )
                                    else:
                                        attachment = AttachmentInfo(
                                            name=file_meta.get('name', 'Unknown'),
                                            type='file',
                                            id=file_obj.get('id'),
                                            url=file_obj.get('url'),
                                            content=content,
                                            size=file_meta.get('size'),
                                            content_type=file_meta.get('content_type')
                                        )
                                    
                                    attachments.append(attachment)
                        
                        # 提取模型信息
                        model = next_msg.get('model', chat.chat.get('models', ['unknown'])[0] if isinstance(chat.chat.get('models'), list) else chat.chat.get('models', 'unknown'))
                        if isinstance(model, dict):
                            model = model.get('id', 'unknown')
                        
                        # 创建问答记录
                        qa_record = QARecord(
                            id=f"{chat.id}_{current_msg.get('id', i)}",
                            question=question_content,
                            answer=answer_content,
                            user_name=user.name,
                            user_email=user.email,
                            user_id=user.id,
                            attachments=attachments,
                            created_at=chat.created_at,
                            updated_at=chat.updated_at,
                            model=str(model),
                            chat_id=chat.id
                        )
                        
                        qa_records.append(qa_record)
                        
                        # 跳过助手回复，继续下一对
                        i += 2
                    else:
                        i += 1
                        
            except Exception as e:
                log.error(f"处理聊天记录 {chat.id} 时出错: {str(e)}")
                continue
                
    except Exception as e:
        log.error(f"提取问答记录时出错: {str(e)}")
    
    return qa_records


############################
# GetAllQARecords
############################

@router.get("/all", response_model=List[QARecord])
async def get_all_qa_records(user=Depends(get_admin_user)):
    """获取所有问答记录（仅管理员）"""
    try:
        qa_records = extract_qa_records_from_chats()
        # 按创建时间倒序排序
        qa_records.sort(key=lambda x: x.created_at, reverse=True)
        return qa_records
    except Exception as e:
        log.error(f"获取所有问答记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT()
        )


############################
# SearchQARecords
############################

@router.get("/search", response_model=QARecordsSearchResponse)
async def search_qa_records(
    query: str = "",
    page: int = 1,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    user=Depends(get_admin_user)
):
    """搜索问答记录（仅管理员）
    
    参数:
    - query: 搜索关键词
    - page: 页码（从1开始）
    - limit: 每页记录数
    - sort_by: 排序字段 (created_at, user_name, user_email)
    - sort_order: 排序方向 (asc, desc)
    """
    try:
        qa_records = extract_qa_records_from_chats()
        
        # 如果有搜索关键词，进行过滤
        if query:
            query_lower = query.lower()
            filtered_records = [
                record for record in qa_records
                if (query_lower in record.question.lower() or
                    query_lower in record.answer.lower() or
                    query_lower in record.user_name.lower() or
                    query_lower in record.user_email.lower())
            ]
        else:
            filtered_records = qa_records
        
        # 排序
        reverse = sort_order == "desc"
        if sort_by == "user_name":
            filtered_records.sort(key=lambda x: x.user_name.lower(), reverse=reverse)
        elif sort_by == "user_email":
            filtered_records.sort(key=lambda x: x.user_email.lower(), reverse=reverse)
        else:  # 默认按创建时间排序
            filtered_records.sort(key=lambda x: x.created_at, reverse=reverse)
        
        # 分页
        total = len(filtered_records)
        start = (page - 1) * limit
        end = start + limit
        paginated_records = filtered_records[start:end]
        
        return QARecordsSearchResponse(
            records=paginated_records,
            total=total
        )
    except Exception as e:
        log.error(f"搜索问答记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT()
        )


############################
# GetQARecordsByUserId
############################

@router.get("/user/{user_id}", response_model=List[QARecord])
async def get_qa_records_by_user_id(user_id: str, user=Depends(get_admin_user)):
    """根据用户ID获取问答记录（仅管理员）"""
    try:
        qa_records = extract_qa_records_from_chats()
        
        # 过滤出指定用户的记录
        user_records = [record for record in qa_records if record.user_id == user_id]
        
        # 按创建时间倒序排序
        user_records.sort(key=lambda x: x.created_at, reverse=True)
        
        return user_records
    except Exception as e:
        log.error(f"获取用户问答记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT()
        )


############################
# GetQARecordById
############################

@router.get("/{record_id}", response_model=Optional[QARecord])
async def get_qa_record_by_id(record_id: str, user=Depends(get_admin_user)):
    """根据ID获取问答记录（仅管理员）"""
    try:
        qa_records = extract_qa_records_from_chats()
        
        for record in qa_records:
            if record.id == record_id:
                return record
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="问答记录未找到"
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"获取问答记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT()
        )
