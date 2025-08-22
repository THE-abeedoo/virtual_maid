import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class ChatHistoryManager:
    """聊天历史管理器"""

    def __init__(self, history_file: str = "chat_history.json", max_history: int = 10):
        self.history_file = history_file
        self.max_history = max_history
        self.history: List[Dict] = self._load_history()

    def _load_history(self) -> List[Dict]:
        """从文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return []

    def _save_history(self):
        """保存历史记录到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def add_conversation(self, user_input: str, assistant_response: str,
                         conversation_type: str = "chat", metadata: Optional[Dict] = None):
        """
        添加一条对话记录

        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            conversation_type: 对话类型 ("chat", "code_execution", "image_analysis")
            metadata: 额外的元数据
        """
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "type": conversation_type,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "metadata": metadata or {}
        }

        self.history.append(conversation)

        # 保持最大历史记录数量
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        self._save_history()

    def get_recent_history(self, count: int = None) -> List[Dict]:
        """获取最近的历史记录"""
        if count is None:
            count = self.max_history
        return self.history[-count:] if self.history else []

    def format_history_for_ai(self, count: int = 10, current_prompt: str = None) -> List[Dict]:
        """
        格式化历史记录用于AI上下文

        Args:
            count: 获取的历史记录数量
            current_prompt: 当前的prompt模板（如果提供，只对最新一条使用）

        Returns:
            格式化后的消息列表，适合传递给AI API
        """
        recent_history = self.get_recent_history(count)
        formatted_messages = []

        for i, record in enumerate(recent_history):
            # 对于历史记录，只保存核心信息，不使用prompt模板
            user_content = record["user_input"]
            assistant_content = record["assistant_response"]

            # 如果是当前最新的一条且提供了prompt模板，则使用模板
            if i == len(recent_history) - 1 and current_prompt:
                user_content = current_prompt.format(user_input=record["user_input"])

            # 添加用户消息
            formatted_messages.append({
                "role": "user",
                "content": user_content
            })

            # 添加助手回复
            formatted_messages.append({
                "role": "assistant",
                "content": assistant_content
            })

        return formatted_messages

    def clear_history(self):
        """清空历史记录"""
        self.history = []
        self._save_history()

    def get_history_summary(self) -> str:
        """获取历史记录摘要"""
        if not self.history:
            return "暂无历史记录"

        total = len(self.history)
        chat_count = sum(1 for h in self.history if h["type"] == "chat")
        code_count = sum(1 for h in self.history if h["type"] == "code_execution")
        image_count = sum(1 for h in self.history if h["type"] == "image_analysis")

        return f"历史记录总数: {total}, 闲聊: {chat_count}, 代码执行: {code_count}, 图片分析: {image_count}"


# 全局历史管理器实例
chat_history = ChatHistoryManager()