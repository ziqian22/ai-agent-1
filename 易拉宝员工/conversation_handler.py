"""
Claude对话理解模块
处理框架外的自由输入，使用Claude理解用户意图
"""

import anthropic
import json
from typing import Dict, Any, Optional
from conversation_state import ConversationContext, ConversationState


class ClaudeConversationHandler:
    """处理自由输入的对话理解"""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        初始化对话处理器

        Args:
            api_key: Claude API密钥
            base_url: API基础URL（用于中转服务）
        """
        if base_url:
            self.client = anthropic.Anthropic(
                api_key=api_key,
                base_url=base_url
            )
        else:
            self.client = anthropic.Anthropic(api_key=api_key)

        # 使用中转服务的模型名称
        if base_url and "zhouyang168" in base_url:
            self.model = "claude-opus-4-7"
        else:
            self.model = "claude-opus-4-20250514"

    def understand_product_modification(
        self,
        user_input: str,
        current_product_info: Dict[str, Any],
        conversation_history: list = None,
        persistent_context: str = None
    ) -> Dict[str, Any]:
        """
        理解用户对产品信息的修改意图

        Args:
            user_input: 用户输入
            current_product_info: 当前产品信息
            conversation_history: 对话历史

        Returns:
            {
                "intent": "modify_product_info",
                "modifications": {
                    "product_name": "新名称",
                    "brand": "新品牌",
                    ...
                },
                "design_requirements": ["slogan用艺术字", "Logo放大一点"],
                "response": "回复用户的消息"
            }
        """
        try:
            # 构建对话历史文本
            history_text = ""
            if conversation_history:
                history_text = "\n\n最近的对话：\n"
                for msg in conversation_history[-5:]:  # 取最近5条
                    role = "用户" if msg["role"] == "user" else "助手"
                    history_text += f"{role}: {msg['content']}\n"

            # 添加持久化上下文
            context_text = ""
            if persistent_context:
                context_text = f"\n\n【重要信息 - 请始终记住】\n{persistent_context}\n"

            prompt = f"""用户想要修改产品信息或提出设计要求。

当前产品信息：
{json.dumps(current_product_info, ensure_ascii=False, indent=2)}
{context_text}{history_text}
用户说："{user_input}"

请分析用户的需求，返回JSON格式。

**重要规则**：
1. 只要用户提到"改成"、"修改"、"是"、"应该是"、"不是"等词，就认为是在修改信息
2. 即使用户的表达不完整或包含否定，也要提取出正确的值
3. 例如："品牌改成朴道,不是浦道" → 提取"朴道"作为新值
4. 例如："产品名称应该是XX" → 提取"XX"作为新值
5. 例如："不是XX，是YY" → 提取"YY"作为新值

如果是修改产品基本信息（名称、品牌、特点等）：
{{
  "intent": "modify_product_info",
  "modifications": {{
    "字段名": "新值"
  }},
  "design_requirements": [],
  "response": "好的，已修改"
}}

如果是设计要求（如：slogan用艺术字、Logo放大、颜色调整等）：
{{
  "intent": "modify_product_info",
  "modifications": {{}},
  "design_requirements": ["具体的设计要求"],
  "response": "好的，已记录"
}}

如果两者都有：
{{
  "intent": "modify_product_info",
  "modifications": {{
    "字段名": "新值"
  }},
  "design_requirements": ["设计要求"],
  "response": "好的，已更新"
}}

**重要**：response 字段必须简短（不超过20字），不要重复用户的输入内容。
只返回JSON，不要其他内容。"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,  # 增加 token 限制，避免响应被截断
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            result_text = response.content[0].text
            result = self._extract_json(result_text)

            return result

        except Exception as e:
            error_msg = str(e)
            print(f"理解产品修改意图出错: {error_msg}")

            # 区分不同类型的错误
            if "401" in error_msg or "Unauthorized" in error_msg or "无效凭证" in error_msg:
                return {
                    "intent": "error",
                    "response": f"⚠️ API认证失败，请检查Claude API配置。\n\n错误详情: {error_msg}"
                }
            elif "timeout" in error_msg.lower():
                return {
                    "intent": "error",
                    "response": f"⚠️ API调用超时，请稍后重试。"
                }
            else:
                return {
                    "intent": "error",
                    "response": f"⚠️ 调用Claude API时出错: {error_msg}\n\n请检查网络连接或API配置。"
                }

    def understand_style_intent(
        self,
        user_input: str,
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        理解用户的风格选择意图，包括多风格生成需求

        Args:
            user_input: 用户输入
            conversation_history: 对话历史

        Returns:
            {
                "intent": "multi_style" | "single_style" | "custom_style" | "unknown",
                "generation_mode": "multi_style" | "hybrid" | "single_style_multi",
                "selected_styles": ["科技感", "简约商务", ...],
                "style_config": {...},  # 如果是单一风格或自定义风格
                "response": "回复用户的消息"
            }
        """
        try:
            # 构建对话历史文本
            history_text = ""
            if conversation_history:
                history_text = "\n\n最近的对话：\n"
                for msg in conversation_history[-5:]:  # 取最近5条
                    role = "用户" if msg["role"] == "user" else "助手"
                    history_text += f"{role}: {msg['content']}\n"

            prompt = f"""用户正在选择易拉宝的设计风格。
{history_text}
用户说："{user_input}"

可用的预设风格：
- 科技感：现代、智能、清爽
- 简约商务：高端、克制、精致
- 自然清新：健康、环保、舒适
- 时尚活力：活力、年轻、创新
- 高端奢华：高端、奢华、尊贵

请分析用户的意图，返回JSON格式：

**情况1：用户想要生成多种不同风格**
例如："各种风格都生成"、"生成多个不同风格"、"每种风格都试试"、"多风格对比"
{{
  "intent": "multi_style",
  "generation_mode": "multi_style",
  "selected_styles": ["科技感", "简约商务", "自然清新", "时尚活力", "高端奢华"],
  "response": "好的，我将为您生成5种不同风格的易拉宝"
}}

**情况2：用户指定了多个具体风格**
例如："生成科技感和商务风"、"我要科技、清新、活力三种"
{{
  "intent": "multi_style",
  "generation_mode": "multi_style",
  "selected_styles": ["科技感", "简约商务"],  // 提取用户提到的风格
  "response": "好的，我将为您生成科技感和简约商务两种风格"
}}

**情况3：用户选择单一风格，但要多个方案**
例如："科技感，多生成几张"、"科技风格，给我5张不同的"
{{
  "intent": "single_style",
  "generation_mode": "single_style_multi",
  "selected_styles": ["科技感"],
  "style_config": {{
    "name": "科技感",
    "scene": "现代科技办公空间,简约玻璃幕墙,智能设备环境",
    "lighting": "明亮的LED灯光,清爽的蓝白色光效,通透的科技感光线",
    "colors": "浅蓝色+白色+浅灰色,荧光蓝点缀,整体明亮清爽",
    "atmosphere": "专业、现代、智能、高效、清爽"
  }},
  "response": "好的，我将为您生成5张科技感风格的易拉宝"
}}

**情况4：用户选择单一预设风格**
例如："科技感"、"我要科技风"、"选择科技感"
{{
  "intent": "single_style",
  "generation_mode": "ask_user",  // 需要询问用户选择生成模式
  "selected_styles": ["科技感"],
  "style_config": {{
    "name": "科技感",
    "scene": "现代科技办公空间,简约玻璃幕墙,智能设备环境",
    "lighting": "明亮的LED灯光,清爽的蓝白色光效,通透的科技感光线",
    "colors": "浅蓝色+白色+浅灰色,荧光蓝点缀,整体明亮清爽",
    "atmosphere": "专业、现代、智能、高效、清爽"
  }},
  "response": "好的，已选择科技感风格"
}}

**情况5：用户描述自定义风格**
例如："我想要蓝色调的，有水元素的设计"
{{
  "intent": "custom_style",
  "generation_mode": "single_style_multi",
  "selected_styles": [],
  "style_config": {{
    "name": "自定义风格",
    "scene": "根据用户描述生成",
    "lighting": "根据用户描述生成",
    "colors": "根据用户描述生成",
    "atmosphere": "根据用户描述生成"
  }},
  "response": "好的，已设置自定义风格"
}}

**重要规则**：
1. 如果用户说"各种"、"所有"、"多种"、"不同风格"，就选择所有5种预设风格
2. 如果用户明确提到具体风格名称，就只选择那些风格
3. 如果用户只选择一个风格但要求"多张"、"多个方案"，使用 single_style_multi 模式
4. response 字段必须简短（不超过30字）

只返回JSON，不要其他内容。"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            result_text = response.content[0].text
            result = self._extract_json(result_text)

            return result

        except Exception as e:
            print(f"理解风格意图出错: {str(e)}")
            return {
                "intent": "unknown",
                "response": f"抱歉，我没理解您想要的风格。请选择一个预设风格或描述您想要的风格。"
            }

    def understand_custom_style(
        self,
        user_input: str,
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        理解用户的自定义风格描述

        Args:
            user_input: 用户输入的风格描述
            conversation_history: 对话历史

        Returns:
            {
                "intent": "custom_style",
                "style_config": {
                    "name": "自定义风格",
                    "scene": "场景描述",
                    "lighting": "光线描述",
                    "colors": "颜色描述",
                    "atmosphere": "氛围描述"
                },
                "response": "回复用户的消息"
            }
        """
        try:
            # 构建对话历史文本
            history_text = ""
            if conversation_history:
                history_text = "\n\n最近的对话：\n"
                for msg in conversation_history[-5:]:  # 取最近5条
                    role = "用户" if msg["role"] == "user" else "助手"
                    history_text += f"{role}: {msg['content']}\n"

            prompt = f"""用户想要自定义易拉宝的设计风格。
{history_text}
用户说："{user_input}"

请分析用户想要的风格，并生成风格配置，返回JSON格式：
{{
  "intent": "custom_style",
  "style_config": {{
    "name": "风格名称",
    "scene": "场景描述",
    "lighting": "光线描述",
    "colors": "颜色描述",
    "atmosphere": "氛围描述",
    "icon": "🎨",
    "description": "简短描述"
  }},
  "response": "好的，已设置风格"
}}

**重要**：response 字段必须简短（不超过15字）。
只返回JSON，不要其他内容。"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,  # 增加 token 限制，避免响应被截断
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            result_text = response.content[0].text
            result = self._extract_json(result_text)

            return result

        except Exception as e:
            print(f"理解自定义风格出错: {str(e)}")
            return {
                "intent": "unknown",
                "response": f"抱歉，我没理解您想要的风格。能否更具体地描述一下？"
            }

    def understand_feedback(
        self,
        user_input: str,
        current_results: list
    ) -> Dict[str, Any]:
        """
        理解用户对生成结果的反馈

        Args:
            user_input: 用户反馈
            current_results: 当前生成结果

        Returns:
            {
                "intent": "satisfied" | "adjust_parameters" | "regenerate",
                "adjustments": {
                    "brightness": "+20%",
                    "text_size": "larger",
                    ...
                },
                "response": "回复用户的消息"
            }
        """
        try:
            prompt = f"""用户对生成的易拉宝提供了反馈。

用户说："{user_input}"

请分析用户的意图，返回JSON格式：

如果用户满意：
{{
  "intent": "satisfied",
  "response": "太好了！"
}}

如果用户要求调整：
{{
  "intent": "adjust_parameters",
  "adjustments": {{
    "brightness": "调整说明",
    "colors": "颜色调整",
    "text_size": "文字调整",
    "layout": "布局调整"
  }},
  "response": "好的，已记录"
}}

如果用户要求重新生成：
{{
  "intent": "regenerate",
  "reason": "原因",
  "response": "好的，重新生成"
}}

**重要**：response 字段必须简短（不超过15字）。
只返回JSON，不要其他内容。"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,  # 增加 token 限制，避免响应被截断
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            result_text = response.content[0].text
            result = self._extract_json(result_text)

            return result

        except Exception as e:
            print(f"理解反馈出错: {str(e)}")
            return {
                "intent": "unknown",
                "response": f"抱歉，我没理解您的反馈。您是满意当前设计，还是需要调整？"
            }

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从响应中提取JSON"""
        try:
            # 尝试直接解析
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {str(e)}")
            print(f"原始文本: {text}")

            # 尝试提取代码块中的JSON
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                if end > start:
                    json_text = text[start:end].strip()
                    try:
                        return json.loads(json_text)
                    except json.JSONDecodeError:
                        pass

            if "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                if end > start:
                    json_text = text[start:end].strip()
                    try:
                        return json.loads(json_text)
                    except json.JSONDecodeError:
                        pass

            # 尝试查找 JSON 对象并修复截断的 JSON
            try:
                start_idx = text.find('{')
                end_idx = text.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_text = text[start_idx:end_idx + 1]
                    return json.loads(json_text)
            except json.JSONDecodeError:
                # 如果 JSON 被截断，尝试修复
                try:
                    start_idx = text.find('{')
                    if start_idx != -1:
                        json_text = text[start_idx:]
                        # 尝试补全被截断的 JSON
                        if not json_text.endswith('}'):
                            # 计算需要补全的括号
                            open_braces = json_text.count('{')
                            close_braces = json_text.count('}')
                            open_brackets = json_text.count('[')
                            close_brackets = json_text.count(']')
                            open_quotes = json_text.count('"') - json_text.count('\\"')

                            # 补全未闭合的字符串
                            if open_quotes % 2 != 0:
                                json_text += '"'

                            # 补全未闭合的数组
                            for _ in range(open_brackets - close_brackets):
                                json_text += ']'

                            # 补全未闭合的对象
                            for _ in range(open_braces - close_braces):
                                json_text += '}'

                            return json.loads(json_text)
                except (json.JSONDecodeError, Exception) as repair_error:
                    print(f"JSON修复失败: {str(repair_error)}")

            # 无法解析，返回错误
            print(f"无法解析JSON，完整响应: {text}")
            return {
                "intent": "error",
                "response": f"⚠️ Claude返回格式有误，可能是响应被截断。请重试。\n\n原始响应: {text}",
                "raw_response": text
            }


# 快捷按钮关键词映射
QUICK_ACTION_KEYWORDS = {
    # 产品确认阶段
    "confirm": ["confirm", "确认", "是的", "对", "正确", "没问题", "ok"],
    "edit": ["edit", "修改", "改", "不对", "错了"],
    "reanalyze": ["reanalyze", "重新分析", "再分析一次"],

    # 风格选择阶段
    "科技感": ["科技感", "科技", "现代", "智能"],
    "简约商务": ["简约商务", "简约", "商务", "高端"],
    "自然清新": ["自然清新", "自然", "清新", "环保"],
    "时尚活力": ["时尚活力", "时尚", "活力", "年轻"],
    "高端奢华": ["高端奢华", "奢华", "尊贵"],

    # 反馈阶段
    "satisfied": ["满意", "很好", "不错", "可以", "完美", "喜欢"],
    "regenerate": ["重新生成", "再来一次", "不满意", "重新"],
    "download_all": ["下载全部", "全部下载", "打包下载"],
    "new": ["生成新产品", "新产品", "重新开始"],
    "retry": ["重试", "再试一次"],
}


def is_quick_action(user_input: str) -> Optional[str]:
    """
    判断用户输入是否匹配快捷按钮

    Args:
        user_input: 用户输入

    Returns:
        匹配的快捷按钮值，如果不匹配返回None
    """
    user_input_lower = user_input.lower().strip()

    for action, keywords in QUICK_ACTION_KEYWORDS.items():
        if user_input_lower in keywords:
            return action

    return None
