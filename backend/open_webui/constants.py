from enum import Enum


class MESSAGES(str, Enum):
    DEFAULT = lambda msg="": f"{msg if msg else ''}"
    MODEL_ADDED = lambda model="": f"模型 '{model}' 已成功添加。"
    MODEL_DELETED = (
        lambda model="": f"模型 '{model}' 已成功删除。"
    )


class WEBHOOK_MESSAGES(str, Enum):
    DEFAULT = lambda msg="": f"{msg if msg else ''}"
    USER_SIGNUP = lambda username="": (
        f"新用户注册: {username}" if username else "新用户注册"
    )


class ERROR_MESSAGES(str, Enum):
    def __str__(self) -> str:
        return super().__str__()

    DEFAULT = (
        lambda err="": f'{"出错了 :/" if err == "" else "[错误: " + str(err) + "]"}'
    )
    ENV_VAR_NOT_FOUND = "未找到所需的环境变量，程序即将终止。"
    CREATE_USER_ERROR = "创建账户时出错，请稍后重试。如果问题持续存在，请联系技术支持。"
    DELETE_USER_ERROR = "删除用户时出错，请重试。"
    EMAIL_MISMATCH = "此邮箱与您注册的邮箱不匹配，请检查后重试。"
    EMAIL_TAKEN = "此邮箱已被注册，请使用已有账户登录或选择其他邮箱。"
    USERNAME_TAKEN = (
        "此用户名已被注册，请选择其他用户名。"
    )
    PASSWORD_TOO_LONG = "密码过长，请确保密码长度小于72字节。"
    PASSWORD_TOO_WEAK = "密码强度不符合要求：密码长度至少需要8位，且必须包含大写字母、小写字母、数字、特殊字符中的至少3种。"
    PASSWORD_EXPIRED = "您的密码已过期（90天），请修改密码后再登录。"
    ACCOUNT_LOCKED = "账户因登录失败次数过多已被锁定，请30分钟后再试。"
    COMMAND_TAKEN = "此命令已被注册，请选择其他命令。"
    FILE_EXISTS = "此文件已被注册，请选择其他文件。"

    ID_TAKEN = "此ID已被注册，请选择其他ID。"
    MODEL_ID_TAKEN = "此模型ID已被注册，请选择其他模型ID。"
    NAME_TAG_TAKEN = "此名称标签已被注册，请选择其他名称标签。"

    INVALID_TOKEN = (
        "会话已过期或令牌无效，请重新登录。"
    )
    INVALID_CRED = "邮箱或密码错误，请检查后重试。"
    INVALID_EMAIL_FORMAT = "邮箱格式无效，请确保使用有效的邮箱地址（例如：yourname@example.com）。"
    INVALID_PASSWORD = (
        "密码错误，请检查后重试。"
    )
    INVALID_TRUSTED_HEADER = "您的提供商未提供可信的请求头，请联系管理员寻求帮助。"

    EXISTING_USERS = "无法关闭身份验证，因为已存在用户。如果要禁用 WEBUI_AUTH，请确保您的 Web 界面没有任何现有用户且是全新安装。"

    UNAUTHORIZED = "401 未授权"
    ACCESS_PROHIBITED = "您没有权限访问此资源，请联系管理员寻求帮助。"
    ACTION_PROHIBITED = (
        "出于安全考虑，此操作已被限制。"
    )

    FILE_NOT_SENT = "文件未发送"
    FILE_NOT_SUPPORTED = "您尝试上传的文件格式不受支持，请上传支持的格式后重试。"

    NOT_FOUND = "未找到您要查找的内容 :/"
    USER_NOT_FOUND = "未找到您要查找的用户 :/"
    API_KEY_NOT_FOUND = "API密钥缺失，请提供有效的API密钥以访问此功能。"
    API_KEY_NOT_ALLOWED = "环境中未启用API密钥的使用。"

    MALICIOUS = "检测到异常活动，请几分钟后重试。"

    PANDOC_NOT_INSTALLED = "服务器未安装 Pandoc，请联系管理员寻求帮助。"
    INCORRECT_FORMAT = (
        lambda err="": f"格式无效，请使用正确的格式{err}"
    )
    RATE_LIMIT_EXCEEDED = "API调用频率超限"

    MODEL_NOT_FOUND = lambda name="": f"未找到模型 '{name}'"
    OPENAI_NOT_FOUND = lambda name="": "未找到 OpenAI API"
    OLLAMA_NOT_FOUND = "WebUI 无法连接到 Ollama"
    CREATE_API_KEY_ERROR = "创建API密钥时出错，请稍后重试。如果问题持续存在，请联系技术支持。"
    API_KEY_CREATION_NOT_ALLOWED = "环境中不允许创建API密钥。"

    EMPTY_CONTENT = "提供的内容为空，请确保在继续之前有文本或数据。"

    DB_NOT_SQLITE = "此功能仅在使用 SQLite 数据库时可用。"

    INVALID_URL = (
        "您提供的URL无效，请检查后重试。"
    )

    WEB_SEARCH_ERROR = (
        lambda err="": f"{err if err else '网络搜索时出错。'}"
    )

    OLLAMA_API_DISABLED = (
        "Ollama API 已禁用，请启用后使用此功能。"
    )

    FILE_TOO_LARGE = (
        lambda size="": f"您尝试上传的文件过大，请上传小于 {size} 的文件。"
    )

    DUPLICATE_CONTENT = (
        "检测到重复内容，请提供唯一内容以继续。"
    )
    FILE_NOT_PROCESSED = "此文件的提取内容不可用，请确保文件已处理后再继续。"


class TASKS(str, Enum):
    def __str__(self) -> str:
        return super().__str__()

    DEFAULT = lambda task="": f"{task if task else 'generation'}"
    TITLE_GENERATION = "title_generation"
    TAGS_GENERATION = "tags_generation"
    EMOJI_GENERATION = "emoji_generation"
    QUERY_GENERATION = "query_generation"
    IMAGE_PROMPT_GENERATION = "image_prompt_generation"
    AUTOCOMPLETE_GENERATION = "autocomplete_generation"
    FUNCTION_CALLING = "function_calling"
    MOA_RESPONSE_GENERATION = "moa_response_generation"
