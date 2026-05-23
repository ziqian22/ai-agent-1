"""
对话状态定义
定义Agent与用户交互的各个状态和状态转换规则
"""

from enum import Enum
from typing import Dict, List, Optional, Any
import json


class ConversationState(Enum):
    """对话状态枚举"""
    WELCOME = "welcome"                    # 欢迎状态
    IMAGE_UPLOADED = "image_uploaded"      # 图片已上传，等待分析
    CONFIRM_PRODUCT = "confirm_product"    # 确认产品信息
    COLLECT_STYLE = "collect_style"        # 收集设计风格
    CONFIRM_INTENT = "confirm_intent"      # 确认生成意图
    GENERATING = "generating"              # 生成中
    SHOW_RESULTS = "show_results"          # 展示结果
    FEEDBACK = "feedback"                  # 收集反馈
    COMPLETED = "completed"                # 完成


class StateTransition:
    """状态转换规则"""

    # 定义允许的状态转换
    ALLOWED_TRANSITIONS = {
        ConversationState.WELCOME: [
            ConversationState.IMAGE_UPLOADED
        ],
        ConversationState.IMAGE_UPLOADED: [
            ConversationState.CONFIRM_PRODUCT,
            ConversationState.WELCOME  # 允许重新开始
        ],
        ConversationState.CONFIRM_PRODUCT: [
            ConversationState.COLLECT_STYLE,
            ConversationState.IMAGE_UPLOADED  # 允许重新分析
        ],
        ConversationState.COLLECT_STYLE: [
            ConversationState.CONFIRM_INTENT,
            ConversationState.CONFIRM_PRODUCT  # 允许返回修改产品信息
        ],
        ConversationState.CONFIRM_INTENT: [
            ConversationState.GENERATING,
            ConversationState.COLLECT_STYLE  # 允许返回修改风格
        ],
        ConversationState.GENERATING: [
            ConversationState.SHOW_RESULTS,
            ConversationState.WELCOME  # 生成失败时可以重新开始
        ],
        ConversationState.SHOW_RESULTS: [
            ConversationState.FEEDBACK,
            ConversationState.COMPLETED
        ],
        ConversationState.FEEDBACK: [
            ConversationState.COLLECT_STYLE,  # 重新选择风格
            ConversationState.GENERATING,     # 微调重新生成
            ConversationState.COMPLETED       # 满意，完成
        ],
        ConversationState.COMPLETED: [
            ConversationState.WELCOME  # 开始新的任务
        ]
    }

    @classmethod
    def can_transition(cls, from_state: ConversationState, to_state: ConversationState) -> bool:
        """
        检查是否允许从一个状态转换到另一个状态

        Args:
            from_state: 当前状态
            to_state: 目标状态

        Returns:
            是否允许转换
        """
        allowed = cls.ALLOWED_TRANSITIONS.get(from_state, [])
        return to_state in allowed

    @classmethod
    def get_next_states(cls, current_state: ConversationState) -> List[ConversationState]:
        """
        获取当前状态可以转换到的所有状态

        Args:
            current_state: 当前状态

        Returns:
            可转换的状态列表
        """
        return cls.ALLOWED_TRANSITIONS.get(current_state, [])


class ConversationContext:
    """对话上下文，存储对话过程中的所有信息"""

    def __init__(self):
        self.state: ConversationState = ConversationState.WELCOME
        self.product_info: Optional[Dict[str, Any]] = None
        self.style_config: Optional[Dict[str, Any]] = None
        self.generation_params: Optional[Dict[str, Any]] = None
        self.results: List[Dict[str, Any]] = []
        self.feedback_history: List[str] = []
        self.adjustments: Dict[str, Any] = {}
        self.uploaded_files: List[str] = []
        self.task_ids: List[str] = []
        self.logo_path: Optional[str] = None  # Logo路径
        self.conversation_history: List[Dict[str, str]] = []  # 对话历史
        self.design_requirements: List[str] = []  # 设计要求（持久化）
        self.important_context: Dict[str, Any] = {}  # 重要上下文（不会被遗忘）
        self.num_images: int = 1  # 生成数量（默认1张）
        self.current_product_id: Optional[str] = None  # 当前产品在知识库中的ID
        self.save_to_kb: bool = True  # 是否保存到知识库（默认True）
        self.generation_mode: Optional[str] = None  # 生成模式: single_style_multi/multi_style/hybrid
        self.generation_count: int = 5  # 生成数量（默认5张）
        self.selected_styles: List[str] = []  # 多风格模式下选择的风格列表

        # 文档处理相关字段
        self.uploaded_file_type: Optional[str] = None  # 上传的文件类型（image/pdf/word/ppt）
        self.extracted_images: List[str] = []  # 从文档提取的图片路径列表
        self.selected_image_index: Optional[int] = None  # 用户选择的图片索引

    def reset(self):
        """重置上下文"""
        self.__init__()

    def update_product_info(self, product_info: Dict[str, Any]):
        """更新产品信息"""
        self.product_info = product_info

    def update_style_config(self, style_config: Dict[str, Any]):
        """更新风格配置"""
        self.style_config = style_config

    def update_generation_params(self, params: Dict[str, Any]):
        """更新生成参数"""
        self.generation_params = params

    def add_result(self, result: Dict[str, Any]):
        """添加生成结果"""
        self.results.append(result)

    def add_feedback(self, feedback: str):
        """添加用户反馈"""
        self.feedback_history.append(feedback)

    def add_adjustment(self, key: str, value: Any):
        """添加调整参数"""
        self.adjustments[key] = value

    def add_conversation(self, role: str, content: str):
        """添加对话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })

    def get_recent_conversation(self, limit: int = 5) -> List[Dict[str, str]]:
        """获取最近的对话历史"""
        return self.conversation_history[-limit:]

    def add_design_requirement(self, requirement: str):
        """添加设计要求"""
        if requirement not in self.design_requirements:
            self.design_requirements.append(requirement)

    def get_persistent_context(self) -> str:
        """获取持久化上下文（重要信息摘要）"""
        context_parts = []

        # 产品信息
        if self.product_info:
            context_parts.append(f"产品信息：{json.dumps(self.product_info, ensure_ascii=False)}")

        # 设计要求
        if self.design_requirements:
            context_parts.append(f"设计要求：{', '.join(self.design_requirements)}")

        # 风格配置
        if self.style_config:
            context_parts.append(f"选择风格：{self.style_config.get('name', 'N/A')}")

        return "\n".join(context_parts)

    def get_summary(self) -> Dict[str, Any]:
        """获取上下文摘要"""
        return {
            "state": self.state.value,
            "has_product_info": self.product_info is not None,
            "has_style_config": self.style_config is not None,
            "results_count": len(self.results),
            "feedback_count": len(self.feedback_history)
        }


# 预设风格库
STYLE_PRESETS = {
    "科技感": {
        "scene": "现代科技办公空间,简约玻璃幕墙,智能设备环境",
        "lighting": "明亮的LED灯光,清爽的蓝白色光效,通透的科技感光线",
        "colors": "浅蓝色+白色+浅灰色,荧光蓝点缀,整体明亮清爽",
        "atmosphere": "专业、现代、智能、高效、清爽",
        "icon": "🔷",
        "description": "现代、智能、清爽"
    },
    "简约商务": {
        "scene": "高端商务办公室,大理石台面,极简空间",
        "lighting": "柔和自然光,45度角斜射,明暗对比克制",
        "colors": "黑白灰+品牌色,低饱和度配色",
        "atmosphere": "专业、高端、克制、精致",
        "icon": "💼",
        "description": "高端、克制、精致"
    },
    "自然清新": {
        "scene": "自然采光空间,绿植环境,木质元素",
        "lighting": "温暖自然光,柔和漫射,清晨或午后光线",
        "colors": "绿色+白色+原木色,清新自然",
        "atmosphere": "健康、环保、舒适、亲和",
        "icon": "🌿",
        "description": "健康、环保、舒适"
    },
    "时尚活力": {
        "scene": "年轻活力空间,色彩丰富,现代设计感",
        "lighting": "明亮活泼光线,多彩光效,动感光影",
        "colors": "鲜艳色彩,高饱和度,撞色搭配",
        "atmosphere": "活力、年轻、创新、潮流",
        "icon": "⚡",
        "description": "活力、年轻、创新"
    },
    "高端奢华": {
        "scene": "奢华空间,金属质感,高级材质",
        "lighting": "戏剧性光影,聚光灯效果,金色暖光",
        "colors": "金色+黑色+深色系,奢华配色",
        "atmosphere": "高端、奢华、尊贵、品质",
        "icon": "👑",
        "description": "高端、奢华、尊贵"
    }
}


def get_style_preset(style_name: str) -> Optional[Dict[str, Any]]:
    """
    获取预设风格配置

    Args:
        style_name: 风格名称

    Returns:
        风格配置字典，如果不存在返回None
    """
    return STYLE_PRESETS.get(style_name)


def list_available_styles() -> List[str]:
    """
    列出所有可用的预设风格

    Returns:
        风格名称列表
    """
    return list(STYLE_PRESETS.keys())
