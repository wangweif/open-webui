import os
import json
from typing import Dict, Any, Optional
import logging as logger
import requests



class IntentClassifier:
    def __init__(self, chat_history):
        self.rules = self._load_rules()
        self.system_prompt = self.rules
        self.chat_history = chat_history

    def _load_rules(self) -> str:
        """加载意图分类规则"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        rules_path = os.path.join(current_dir, "intent_prompt.txt")

        with open(rules_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _build_context_prompt(self, last_question: str, current_text: str) -> str:
        """构建包含上下文的提示"""
        context_str = ""
        if last_question:
            context_str = "对话历史：\n"
            context_str += f"用户: {last_question}\n"

        prompt = f"{self.system_prompt}\n\n{context_str}\n当前输入: {current_text}\n请分类:"
        return prompt

    def classify(self, text: str) -> Dict[str, Any]:
        """
        对输入文本进行意图分类 
        """
        try:
            # 构建提示
            prompt = self._build_context_prompt(self.chat_history, text)
            logger.info(f'last_question: {self.chat_history}, text: {text}')

            # 调用模型并指定结构化输出格式
            payload = json.dumps({
                "model": "Qwen3:8B",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "chat_template_kwargs": {"enable_thinking":False}
            })
            try:
                url = "http://192.168.8.88:8005/v1/chat/completions"
                headers = {
                    'Content-Type': 'application/json'
                }
                response = requests.request("POST", url, headers=headers, data=payload)
                logger.debug(f'Response: {response}')
                # 解析JSON响应
                result = response.json()['choices'][0]['message']['content']
                logger.debug(f'result: {result}')
                return json.loads(result)
            except Exception as e:
                logger.error(f'Error: {e}')


        except Exception as e:
            logger.error(f"Error in classify: {str(e)}")
            raise