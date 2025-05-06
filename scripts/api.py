#系统初始配置步骤：
#1.设置api_config.json中的globals参数
#2.更新Ollama配置
#3.更新OpenAI配置
#4.配置工具
#5.添加模型（默认为deepseek-r1:32b）
#6.创建工作区模型（默认base_model_id为deepseek-r1:32b）

import requests
import json
import argparse
import os
from typing import Dict, Any, Optional

login_endpoint = "/api/auth/login"
credentials = {"username": "buct255@gmail.com", "password": "admin"}

class ApiClient:
    def __init__(self, base_url: str):
        """
        初始化API客户端
        
        Args:
            base_url: API的基础URL
            login_endpoint: 登录接口端点路径
            login_credentials: 登录凭证（username和password）
        """
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json"
        }
        self.token = None
        
       
    def make_request(self, endpoint: str, method: str = "GET", 
                    data: Optional[Dict[str, Any]] = None, 
                    params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发起API请求
        
        Args:
            endpoint: API端点路径
            method: 请求方法（GET, POST, PUT, DELETE等）
            data: 请求体数据（用于POST/PUT等）
            params: URL参数（用于GET请求）
            
        Returns:
            API响应（JSON格式）
        """
        url = f"{self.base_url}{endpoint}"
        method = method.upper()
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, params=params)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            
            return response.json() if response.text else {}
        
        except requests.exceptions.RequestException as e:
            print(f"请求发生异常: {e}")
            return {"error": str(e)}


def load_api_config(config_file: str = "api_config.json") -> Dict[str, Any]:
    """
    加载API配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        API配置字典
    """
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"警告: 配置文件 {config_file} 不存在，将使用默认配置")
            return {"apis": {}, "auth": {}}
    except Exception as e:
        print(f"加载配置文件出错: {e}")
        return {"apis": {}, "auth": {}}



def interactive_mode():
    """交互式模式，让用户选择预设API或输入自定义API信息"""
    # 加载配置文件
    config_data = load_api_config()
    globals = config_data.get("globals", {})
    apis = config_data.get("apis", {})
    
    print("欢迎使用API请求工具！")
    
    if not apis:
        print("警告: 未找到预设API配置，将退出")
        exit()
    
    # 获取登录凭证
    login_credentials = globals.get("login_credentials", {})
    login_endpoint = globals.get("login_endpoint")
    base_url = globals.get("base_url")

    print("登录中...")
    #登录
    client = ApiClient(base_url=base_url)
    response = client.make_request(login_endpoint, "POST", login_credentials)
    token = response.get("token")
    if not token:
        print("错误: 登录失败，无法获取Token")
        return
    
    # 设置Token到请求头
    client.headers["Authorization"] = f"Bearer {token}"
    print(token)
    print("登录成功!")
    
    
    
    # 显示预设API选项
    print("\n可用的预设API:")
    api_names = list(apis.keys())
    for i, name in enumerate(api_names, 1):
        api = apis[name]
        print(f"{i}. {name} - {api.get('description', '')} ({api.get('method', 'GET')} {api.get('url', '')}{api.get('endpoint', '')})")
    print(f"{len(apis) + 1}. 退出")
    
    # 让用户选择
    while True:
        try:
            choice = int(input("\n请选择一个选项 (输入数字): "))
            if 1 <= choice <= len(apis) + 1:
                break
            else:
                print("无效的选择，请重试")
        except ValueError:
            print("请输入有效的数字")
    
    # 处理用户选择
    if choice <= len(apis):
        # 使用预设API
        selected_api_name = api_names[choice - 1]
        api_config = apis[selected_api_name]
        
       
        endpoint = api_config.get("endpoint")
        method = api_config.get("method")
        default_data = api_config.get("default_data")
        print("default_data:",default_data) 
        
        # 处理路径中的参数
        if "{" in endpoint and "}" in endpoint:
            for part in endpoint.split("/"):
                if part.startswith("{") and part.endswith("}"):
                    param_key = part[1:-1]
                    param_value = input(f"请输入路径参数 {param_key}: ")
                    endpoint = endpoint.replace(f"{{{param_key}}}", param_value)
        
        # 发起请求
        response = client.make_request(endpoint, method, default_data)
        
    else:
        # 退出
        return
    
    # 打印响应
    print("\n响应结果:")
    print(json.dumps(response, indent=2, ensure_ascii=False))


if __name__ == "__main__":    
    interactive_mode()