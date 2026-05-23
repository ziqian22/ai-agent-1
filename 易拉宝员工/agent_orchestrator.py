"""
Agent编排器
协调各个模块，管理对话流程，处理用户交互
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from conversation_state import (
    ConversationState,
    ConversationContext,
    StateTransition,
    STYLE_PRESETS,
    get_style_preset
)
from vision_analyzer import VisionAnalyzer
from progress_tracker import ProgressTracker, TaskStep
from banner_prompt_template import generate_banner_prompt
from runninghub_client import RunningHubClient
from test_recorder import TestRecorder
from banner_generator import BannerGenerator
from parallel_generator import ParallelBannerGenerator
from conversation_handler import ClaudeConversationHandler, is_quick_action


class BannerAgent:
    """易拉宝AI Agent - 核心编排器"""

    def __init__(
        self,
        runninghub_api_key: str,
        claude_api_key: str,
        claude_base_url: Optional[str] = None,
        runninghub_base_url: str = "https://www.runninghub.cn/openapi/v2",
        knowledge_base=None
    ):
        """
        初始化Agent

        Args:
            runninghub_api_key: Running Hub API密钥
            claude_api_key: Claude API密钥
            claude_base_url: Claude API基础URL（用于中转服务）
            runninghub_base_url: Running Hub API基础URL
            knowledge_base: 知识库实例
        """
        # 初始化上下文
        self.context = ConversationContext()

        # 初始化工具
        self.vision_analyzer = VisionAnalyzer(claude_api_key, claude_base_url)
        self.api_client = RunningHubClient(runninghub_api_key, runninghub_base_url)
        self.banner_generator = BannerGenerator(runninghub_api_key, runninghub_base_url)
        self.parallel_generator = ParallelBannerGenerator(self.banner_generator, max_workers=5)
        self.conversation_handler = ClaudeConversationHandler(claude_api_key, claude_base_url)
        self.recorder = TestRecorder()
        self.progress_tracker = ProgressTracker()
        self.knowledge_base = knowledge_base  # 知识库实例

        # 对话历史
        self.messages: List[Dict[str, Any]] = []

    async def process_message(
        self,
        user_input: str,
        image_path: Optional[str] = None,
        logo_path: Optional[str] = None,
        save_to_kb: bool = True
    ) -> Dict[str, Any]:
        """
        处理用户消息

        Args:
            user_input: 用户输入文本
            image_path: 图片路径（可选）
            logo_path: Logo路径（可选）
            save_to_kb: 是否保存到知识库（默认True）

        Returns:
            Agent响应字典
        """
        # 保存用户输入到对话历史
        if user_input:
            self.context.add_conversation("user", user_input)

        # 保存Logo路径到上下文
        if logo_path:
            self.context.logo_path = logo_path

        # 保存是否需要保存到知识库的标志
        self.context.save_to_kb = save_to_kb

        current_state = self.context.state

        if current_state == ConversationState.WELCOME:
            return await self._handle_welcome(image_path)

        elif current_state == ConversationState.IMAGE_UPLOADED:
            return await self._handle_image_analysis(image_path)

        elif current_state == ConversationState.CONFIRM_PRODUCT:
            return await self._handle_product_confirmation(user_input)

        elif current_state == ConversationState.COLLECT_STYLE:
            return await self._handle_style_selection(user_input)

        elif current_state == ConversationState.CONFIRM_INTENT:
            return await self._handle_intent_confirmation(user_input)

        elif current_state == ConversationState.SHOW_RESULTS:
            # 生成完成，等待用户反馈
            self.context.state = ConversationState.FEEDBACK
            return await self._handle_feedback(user_input)

        elif current_state == ConversationState.FEEDBACK:
            return await self._handle_feedback(user_input)

        elif current_state == ConversationState.COMPLETED:
            # 生成完成后，允许继续对话、修改或重新生成
            return await self._handle_post_generation(user_input)

        else:
            return {
                "message": "抱歉，我不确定当前应该做什么。让我们重新开始吧。",
                "state": ConversationState.WELCOME.value,
                "quick_actions": []
            }

    async def load_from_knowledge_base(self, product_id: str) -> Dict[str, Any]:
        """
        从知识库加载产品信息并快速进入生成流程

        Args:
            product_id: 产品ID

        Returns:
            Agent响应字典
        """
        if not self.knowledge_base:
            return {
                "message": "知识库未初始化",
                "state": ConversationState.WELCOME.value,
                "quick_actions": []
            }

        # 从知识库获取产品信息
        product = self.knowledge_base.get_product(product_id)

        if not product:
            return {
                "message": "产品不存在",
                "state": ConversationState.WELCOME.value,
                "quick_actions": []
            }

        # 加载产品信息到上下文
        self.context.update_product_info(product['product_info'])
        self.context.current_product_id = product_id

        # 加载图片和Logo路径
        if product.get('image_path'):
            self.context.uploaded_files.append(product['image_path'])

        if product.get('logo_path'):
            self.context.logo_path = product['logo_path']

        # 直接进入风格选择状态（跳过图片分析）
        self.context.state = ConversationState.COLLECT_STYLE

        # 格式化产品信息
        info_text = self._format_product_info(product['product_info'])

        message = f"""已从知识库加载产品信息：

{info_text}

现在请选择易拉宝的设计风格："""

        return {
            "message": message,
            "state": self.context.state.value,
            "quick_actions": [
                {"label": f"{config['icon']} {name}", "value": name}
                for name, config in STYLE_PRESETS.items()
            ],
            "product_info": product['product_info']
        }

    async def _handle_welcome(self, image_path: Optional[str] = None) -> Dict[str, Any]:
        """处理欢迎状态"""
        if image_path:
            # 用户上传了图片
            self.context.uploaded_files.append(image_path)
            self.context.state = ConversationState.IMAGE_UPLOADED

            return {
                "message": "收到您的产品图片！正在分析中，请稍候...",
                "state": self.context.state.value,
                "quick_actions": []
            }
        else:
            return {
                "message": """您好！我是易拉宝设计助手 🎨

我可以帮您：
1. 分析产品图片，提取产品信息
2. 根据您的需求设计易拉宝
3. 生成多张设计供您选择
4. 根据反馈优化设计

请上传产品图片或从知识库选择产品开始吧！""",
                "state": self.context.state.value,
                "quick_actions": []
            }

    async def _handle_image_analysis(self, image_path: Optional[str] = None) -> Dict[str, Any]:
        """处理文件分析（图片或文档）"""
        if not image_path and self.context.uploaded_files:
            image_path = self.context.uploaded_files[0]

        if not image_path:
            return {
                "message": "请先上传产品图片或文档。",
                "state": self.context.state.value,
                "quick_actions": []
            }

        try:
            # 开始分析
            self.progress_tracker.start_task()
            self.progress_tracker.start_step(TaskStep.ANALYZE_IMAGE)

            # 检测文件类型
            file_ext = Path(image_path).suffix.lower()

            if file_ext in ['.pdf', '.docx', '.doc', '.pptx', '.ppt']:
                # 文档文件，使用文档分析
                self.context.uploaded_file_type = 'document'
                self.progress_tracker.add_log(f"检测到文档文件: {file_ext}")

                analysis_result = self.vision_analyzer.analyze_document(image_path)
                product_info = analysis_result['product_info']
                extracted_images = analysis_result.get('images', [])

                self.progress_tracker.complete_step(TaskStep.ANALYZE_IMAGE)

                # 保存产品信息
                self.context.update_product_info(product_info)

                # 如果文档中有多张图片，让用户选择
                if len(extracted_images) > 1:
                    self.context.extracted_images = extracted_images
                    self.context.state = ConversationState.CONFIRM_PRODUCT

                    # 格式化产品信息
                    info_text = self._format_product_info(product_info)

                    message = f"""我从文档中识别到以下产品信息：

{info_text}

我还在文档中找到了 {len(extracted_images)} 张图片，请选择哪张是产品图："""

                    # 生成图片选择按钮
                    quick_actions = [
                        {"label": f"📷 图片 {i+1}", "value": f"select_image_{i}"}
                        for i in range(len(extracted_images))
                    ]

                    return {
                        "message": message,
                        "state": self.context.state.value,
                        "quick_actions": quick_actions,
                        "product_info": product_info,
                        "extracted_images": extracted_images
                    }

                elif len(extracted_images) == 1:
                    # 只有一张图片，直接使用
                    self.context.uploaded_files.append(extracted_images[0])
                    self.context.state = ConversationState.CONFIRM_PRODUCT

                    # 生成主动提问
                    questions = self.vision_analyzer.generate_questions(product_info)

                    # 格式化产品信息
                    info_text = self._format_product_info(product_info)

                    message = f"""我从文档中识别到以下产品信息：

{info_text}

⚠️ 请确认：
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(questions))}"""

                    return {
                        "message": message,
                        "state": self.context.state.value,
                        "quick_actions": [
                            {"label": "✅ 确认", "value": "confirm"},
                            {"label": "✏️ 修改", "value": "edit"},
                            {"label": "🔄 重新分析", "value": "reanalyze"}
                        ],
                        "product_info": product_info
                    }

                else:
                    # 文档中没有图片
                    self.context.state = ConversationState.CONFIRM_PRODUCT

                    # 格式化产品信息
                    info_text = self._format_product_info(product_info)

                    message = f"""我从文档中识别到以下产品信息：

{info_text}

⚠️ 注意：文档中没有找到产品图片，您需要单独上传产品图片才能生成易拉宝。

请确认产品信息是否正确？"""

                    return {
                        "message": message,
                        "state": self.context.state.value,
                        "quick_actions": [
                            {"label": "✅ 确认", "value": "confirm"},
                            {"label": "✏️ 修改", "value": "edit"},
                            {"label": "📤 上传产品图片", "value": "upload_image"}
                        ],
                        "product_info": product_info
                    }

            else:
                # 图片文件，使用图片分析
                self.context.uploaded_file_type = 'image'
                product_info = self.vision_analyzer.analyze_image(image_path)

                self.progress_tracker.complete_step(TaskStep.ANALYZE_IMAGE)

                # 保存产品信息
                self.context.update_product_info(product_info)

                # 生成主动提问
                questions = self.vision_analyzer.generate_questions(product_info)

                # 切换状态
                self.context.state = ConversationState.CONFIRM_PRODUCT

                # 格式化产品信息
                info_text = self._format_product_info(product_info)

                message = f"""我识别到以下产品信息：

{info_text}

⚠️ 请确认：
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(questions))}"""

                return {
                    "message": message,
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": "✅ 确认", "value": "confirm"},
                        {"label": "✏️ 修改", "value": "edit"},
                        {"label": "🔄 重新分析", "value": "reanalyze"}
                    ],
                    "product_info": product_info
                }

        except Exception as e:
            self.progress_tracker.complete_step(TaskStep.ANALYZE_IMAGE, success=False)
            self.progress_tracker.add_log(f"分析失败: {str(e)}", "error")

            return {
                "message": f"抱歉，分析文件时出错了：{str(e)}\n\n请重新上传文件或检查文件格式。",
                "state": ConversationState.WELCOME.value,
                "quick_actions": []
            }

    async def _handle_product_confirmation(self, user_input: str) -> Dict[str, Any]:
        """处理产品信息确认"""
        # 检查是否是图片选择
        if user_input.startswith("select_image_"):
            try:
                image_index = int(user_input.split("_")[-1])
                if 0 <= image_index < len(self.context.extracted_images):
                    # 用户选择了图片
                    selected_image = self.context.extracted_images[image_index]
                    self.context.uploaded_files.append(selected_image)
                    self.context.selected_image_index = image_index

                    # 生成主动提问
                    questions = self.vision_analyzer.generate_questions(self.context.product_info)

                    # 格式化产品信息
                    info_text = self._format_product_info(self.context.product_info)

                    message = f"""已选择图片 {image_index + 1}。

产品信息：
{info_text}

⚠️ 请确认：
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(questions))}"""

                    return {
                        "message": message,
                        "state": self.context.state.value,
                        "quick_actions": [
                            {"label": "✅ 确认", "value": "confirm"},
                            {"label": "✏️ 修改", "value": "edit"},
                            {"label": "🔄 重新选择图片", "value": "reselect_image"}
                        ]
                    }
            except (ValueError, IndexError):
                pass

        # 检查是否是重新选择图片
        if user_input == "reselect_image":
            if self.context.extracted_images:
                message = f"请重新选择产品图片（共 {len(self.context.extracted_images)} 张）："

                quick_actions = [
                    {"label": f"📷 图片 {i+1}", "value": f"select_image_{i}"}
                    for i in range(len(self.context.extracted_images))
                ]

                return {
                    "message": message,
                    "state": self.context.state.value,
                    "quick_actions": quick_actions
                }

        # 检查是否是快捷按钮
        quick_action = is_quick_action(user_input)

        if quick_action == "confirm":
            # 用户确认，进入风格选择
            self.context.state = ConversationState.COLLECT_STYLE

            return {
                "message": self._get_style_selection_message(),
                "state": self.context.state.value,
                "quick_actions": [
                    {"label": f"{config['icon']} {name}", "value": name}
                    for name, config in STYLE_PRESETS.items()
                ],
                "styles": STYLE_PRESETS
            }

        elif quick_action in ["edit", "reanalyze"]:
            # 用户要求修改或重新分析
            return {
                "message": "好的，请告诉我需要修改哪些信息，或者重新上传文件。",
                "state": self.context.state.value,
                "quick_actions": []
            }

        else:
            # 自由输入，使用Claude理解
            result = self.conversation_handler.understand_product_modification(
                user_input,
                self.context.product_info,
                self.context.conversation_history,  # 传递对话历史
                self.context.get_persistent_context()  # 传递持久化上下文
            )

            if result.get("intent") == "modify_product_info":
                # 应用修改
                modifications = result.get("modifications", {})
                for key, value in modifications.items():
                    if key in self.context.product_info:
                        self.context.product_info[key] = value

                # 保存设计要求
                design_requirements = result.get("design_requirements", [])
                for req in design_requirements:
                    self.context.add_design_requirement(req)

                # 格式化更新后的信息
                info_text = self._format_product_info(self.context.product_info)

                response_parts = [result.get('response', '已更新')]

                if modifications:
                    response_parts.append(f"\n\n更新后的信息：\n{info_text}")

                if design_requirements:
                    response_parts.append(f"\n\n设计要求：\n" + "\n".join(f"- {req}" for req in design_requirements))

                response_parts.append("\n\n请确认是否继续？")

                response_message = "".join(response_parts)

                # 保存Agent响应到对话历史
                self.context.add_conversation("assistant", response_message)

                return {
                    "message": response_message,
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": "✅ 继续", "value": "confirm"},
                        {"label": "✏️ 继续修改", "value": "edit"}
                    ]
                }
            elif result.get("intent") == "error":
                # API调用出错
                return {
                    "message": result.get("response", "系统错误"),
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": "✅ 不改了，继续", "value": "confirm"},
                        {"label": "🔄 重新分析", "value": "reanalyze"}
                    ]
                }
            else:
                # Claude没有识别出明确的修改意图，提示用户更具体地说明
                response_message = result.get("response", "抱歉，我没有理解您想要修改什么。")
                response_message += "\n\n请更具体地告诉我，例如：\n- 品牌改成XX\n- 产品名称是XX\n- 添加特点：XX"

                self.context.add_conversation("assistant", response_message)

                return {
                    "message": response_message,
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": "✅ 不改了，继续", "value": "confirm"},
                        {"label": "🔄 重新分析", "value": "reanalyze"}
                    ]
                }

    async def _handle_style_selection(self, user_input: str) -> Dict[str, Any]:
        """处理风格选择"""
        # 检查是否是生成模式选择（只支持单一风格）
        if user_input == "single_style_multi":
            # 保存生成模式
            self.context.generation_mode = "single_style_multi"
            self.context.generation_count = 5
            # 单一风格模式，直接进入意图确认
            self.context.state = ConversationState.CONFIRM_INTENT

            # 检查是否可以显示生成按钮
            quick_actions = []
            if self._is_ready_to_generate():
                quick_actions = [
                    {"label": "✅ 确认生成", "value": "confirm"},
                    {"label": "✏️ 修改参数", "value": "edit"}
                ]

            return {
                "message": f"已选择：单一风格生成5张设计变体\n\n{self._get_intent_confirmation_message()}",
                "state": self.context.state.value,
                "quick_actions": quick_actions
            }

        # 如果用户尝试选择多风格或混合模式，给出提示
        if user_input in ["multi_style", "hybrid"]:
            styles_text = self._get_style_list_text()

            return {
                "message": f"""抱歉，系统目前不支持一次生成多种风格。

为了保证每种风格的质量和特色，建议您：
1. 每次选择一个风格生成5张设计方案
2. 对比不同方案后，如需尝试其他风格，可以重新选择

可选风格：
{styles_text}

请选择您想要的风格：""",
                "state": self.context.state.value,
                "quick_actions": [
                    {"label": f"{config['icon']} {name}", "value": name}
                    for name, config in STYLE_PRESETS.items()
                ]
            }


        # 检查是否是快捷按钮（预设风格）
        quick_action = is_quick_action(user_input)

        # 检查是否是预设风格
        style_config = get_style_preset(user_input) or get_style_preset(quick_action) if quick_action else None

        if style_config:
            # 检查是否需要场景描述
            if style_config.get('requires_sub_selection', False):
                # 保存主风格，等待场景描述
                self.context.pending_style = user_input if not quick_action else quick_action
                self.context.state = ConversationState.COLLECT_STYLE  # 保持在风格选择状态

                suggested_scenes = style_config.get('suggested_scenes', [])
                scenes_text = '\n'.join([f"- {scene}" for scene in suggested_scenes])

                return {
                    "message": f"""您选择了「{self.context.pending_style}」风格。

请描述您想要的具体场景，例如：

{scenes_text}

您也可以自己描述想要的场景环境。""",
                    "state": self.context.state.value,
                    "quick_actions": []  # 不提供按钮，让用户自由输入
                }

            # 普通风格，直接保存
            self.context.update_style_config({
                "name": user_input if not quick_action else quick_action,
                "is_scene_style": False,
                **style_config
            })

            # 直接使用单一风格多方案模式（不再提供多风格选项）
            self.context.generation_mode = "single_style_multi"
            self.context.generation_count = 5

            # 切换到意图确认状态
            self.context.state = ConversationState.CONFIRM_INTENT

            # 检查是否可以显示生成按钮
            quick_actions = []
            if self._is_ready_to_generate():
                quick_actions = [
                    {"label": "✅ 确认生成", "value": "confirm"},
                    {"label": "✏️ 修改风格", "value": "edit"}
                ]

            return {
                "message": f"已选择风格：{user_input if not quick_action else quick_action}\n\n将为您生成5张同风格但设计细节不同的易拉宝。\n\n{self._get_intent_confirmation_message()}",
                "state": self.context.state.value,
                "quick_actions": quick_actions
            }

        else:
            # 检查是否是场景描述（用户在pending_style状态下的输入）
            if self.context.pending_style == "具体场景":
                # 使用Claude理解用户的场景描述
                scene_understanding = self.conversation_handler.understand_scene_description(
                    user_input,
                    self.context.conversation_history
                )

                # 生成场景配置
                self.context.update_style_config({
                    "name": f"具体场景 - {scene_understanding.get('scene_name', '自定义')}",
                    "is_scene_style": True,
                    "scene": scene_understanding.get('scene_description'),
                    "lighting": scene_understanding.get('lighting'),
                    "colors": scene_understanding.get('colors'),
                    "atmosphere": scene_understanding.get('atmosphere')
                })

                # 清除临时状态
                self.context.pending_style = None

                # 继续到意图确认
                self.context.generation_mode = "single_style_multi"
                self.context.generation_count = 5
                self.context.state = ConversationState.CONFIRM_INTENT

                # 检查是否可以显示生成按钮
                quick_actions = []
                if self._is_ready_to_generate():
                    quick_actions = [
                        {"label": "✅ 确认生成", "value": "confirm"},
                        {"label": "✏️ 修改场景", "value": "edit"}
                    ]

                return {
                    "message": f"已理解您的场景需求：{scene_understanding.get('scene_name')}\n\n{self._get_intent_confirmation_message()}",
                    "state": self.context.state.value,
                    "quick_actions": quick_actions
                }

            # 自由输入，使用Claude理解风格意图
            result = self.conversation_handler.understand_style_intent(
                user_input,
                self.context.conversation_history
            )

            intent = result.get("intent")
            generation_mode = result.get("generation_mode")
            selected_styles = result.get("selected_styles", [])

            if intent == "multi_style":
                # 用户想要多风格生成 - 给出提示
                styles_text = self._get_style_list_text()

                response_message = f"""抱歉，系统目前不支持一次生成多种风格。

为了保证每种风格的质量和特色，建议您：
1. 每次选择一个风格生成5张设计方案
2. 对比不同方案后，如需尝试其他风格，可以重新选择

这样可以确保每种风格都有明显的特色和足够的设计变化。

可选风格：
{styles_text}

请选择您想要的风格："""
                self.context.add_conversation("assistant", response_message)

                return {
                    "message": response_message,
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": f"{config['icon']} {name}", "value": name}
                        for name, config in STYLE_PRESETS.items()
                    ]
                }

            elif intent == "single_style" and generation_mode == "single_style_multi":
                # 用户选择单一风格，要多个方案
                style_config = result.get("style_config", {})
                self.context.update_style_config(style_config)
                self.context.generation_mode = "single_style_multi"
                self.context.generation_count = 5

                # 切换到意图确认状态
                self.context.state = ConversationState.CONFIRM_INTENT

                response_message = f"{result.get('response', '好的')}\n\n{self._get_intent_confirmation_message()}"
                self.context.add_conversation("assistant", response_message)

                # 检查是否可以显示生成按钮
                quick_actions = []
                if self._is_ready_to_generate():
                    quick_actions = [
                        {"label": "✅ 确认生成", "value": "confirm"},
                        {"label": "✏️ 修改参数", "value": "edit"}
                    ]

                return {
                    "message": response_message,
                    "state": self.context.state.value,
                    "quick_actions": quick_actions
                }

            elif intent == "single_style" and generation_mode == "ask_user":
                # 用户选择单一风格，需要询问生成模式
                style_config = result.get("style_config", {})
                self.context.update_style_config(style_config)

                response_message = f"{result.get('response', '好的')}\n\n请选择生成方式："
                self.context.add_conversation("assistant", response_message)

                return {
                    "message": response_message,
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": "🎨 单一风格多方案(推荐)", "value": "single_style_multi", "description": "生成5张同风格但设计细节不同的易拉宝"},
                        {"label": "🎭 多风格对比", "value": "multi_style", "description": "选择多种风格各生成1张进行对比"},
                        {"label": "🔀 混合模式", "value": "hybrid", "description": "选择2-3种风格，每种生成2张"}
                    ],
                    "generation_mode_selection": True
                }

            elif intent == "custom_style":
                # 用户描述自定义风格
                style_config = result.get("style_config", {})
                self.context.update_style_config(style_config)
                self.context.generation_mode = "single_style_multi"
                self.context.generation_count = 5

                # 切换到意图确认状态
                self.context.state = ConversationState.CONFIRM_INTENT

                response_message = f"{result.get('response', '已设置自定义风格')}\n\n{self._get_intent_confirmation_message()}"
                self.context.add_conversation("assistant", response_message)

                # 检查是否可以显示生成按钮
                quick_actions = []
                if self._is_ready_to_generate():
                    quick_actions = [
                        {"label": "✅ 确认生成", "value": "confirm"},
                        {"label": "✏️ 修改风格", "value": "edit"}
                    ]

                return {
                    "message": response_message,
                    "state": self.context.state.value,
                    "quick_actions": quick_actions
                }

            else:
                # 无法理解用户意图
                styles_text = self._get_style_list_text()

                response_message = f"""抱歉，我没有理解您的意图。

可选风格：
{styles_text}

请选择一个风格或描述您想要的风格。"""
                self.context.add_conversation("assistant", response_message)

                return {
                    "message": response_message,
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": f"{config['icon']} {name}", "value": name}
                        for name, config in STYLE_PRESETS.items()
                    ]
                }

    async def _handle_intent_confirmation(self, user_input: str) -> Dict[str, Any]:
        """处理意图确认"""
        user_input_lower = user_input.lower().strip()

        if user_input_lower in ["confirm", "确认", "开始生成", "生成"]:
            # 用户确认，开始生成
            self.context.state = ConversationState.GENERATING

            # 启动生成任务
            result = await self._start_generation()

            return result

        elif user_input_lower in ["change_style", "修改风格", "change_count", "修改数量"]:
            # 用户要求修改参数
            if user_input_lower in ["change_style", "修改风格"]:
                # 返回风格选择状态
                self.context.state = ConversationState.COLLECT_STYLE

                styles_text = self._get_style_list_text()

                return {
                    "message": f"""好的，请重新选择设计风格：

可选风格：
{styles_text}""",
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": f"{config['icon']} {name}", "value": name}
                        for name, config in STYLE_PRESETS.items()
                    ]
                }
            else:
                # 修改数量
                return {
                    "message": "好的，请问您想生成几张易拉宝？（建议1-5张）",
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": "1张", "value": "count_1"},
                        {"label": "3张", "value": "count_3"},
                        {"label": "5张", "value": "count_5"}
                    ]
                }

        elif user_input_lower in ["edit", "修改", "修改参数"]:
            # 用户要求修改，询问修改什么
            return {
                "message": "好的，请告诉我需要修改什么参数？",
                "state": self.context.state.value,
                "quick_actions": [
                    {"label": "修改风格", "value": "change_style"},
                    {"label": "修改数量", "value": "change_count"}
                ]
            }

        elif user_input_lower.startswith("count_"):
            # 用户选择了生成数量
            try:
                count = int(user_input_lower.split("_")[1])
                self.context.num_images = count

                # 检查是否可以显示生成按钮
                quick_actions = []
                if self._is_ready_to_generate():
                    quick_actions = [
                        {"label": "✅ 确认生成", "value": "confirm"},
                        {"label": "✏️ 修改参数", "value": "edit"}
                    ]

                return {
                    "message": f"已设置生成数量为 {count} 张。\n\n" + self._get_intent_confirmation_message(),
                    "state": self.context.state.value,
                    "quick_actions": quick_actions
                }
            except:
                pass

        else:
            # 其他输入，提示用户
            # 检查是否可以显示生成按钮
            quick_actions = []
            if self._is_ready_to_generate():
                quick_actions = [
                    {"label": "✅ 确认生成", "value": "confirm"},
                    {"label": "✏️ 修改参数", "value": "edit"}
                ]

            return {
                "message": '请回复"确认"开始生成，或告诉我需要修改的地方。',
                "state": self.context.state.value,
                "quick_actions": quick_actions
            }

    async def _start_generation(self) -> Dict[str, Any]:
        """开始生成易拉宝（支持单一风格和多风格）"""
        try:
            self.progress_tracker.start_step(TaskStep.GENERATE_PROMPT)

            product_info = self.context.product_info
            image_path = self.context.uploaded_files[0]

            # 固定使用朴道 Logo（使用相对路径）
            from pathlib import Path
            script_dir = Path(__file__).parent
            fixed_logo_path = script_dir / "朴道logo" / "PUDOW朴道健康水专家-原色.png"

            # 检查 Logo 文件是否存在
            if not fixed_logo_path.exists():
                self.progress_tracker.add_log(f"[WARNING] Logo 文件不存在: {fixed_logo_path}")
                fixed_logo_path = None
            else:
                self.progress_tracker.add_log(f"[OK] 使用固定 Logo: {fixed_logo_path}")
                fixed_logo_path = str(fixed_logo_path)

            # 进度回调函数
            def progress_callback(message: str):
                self.progress_tracker.add_log(message)

            # 根据生成模式选择不同的生成策略
            generation_mode = self.context.generation_mode or "single_style_multi"

            if generation_mode == "single_style_multi":
                # 单一风格多方案
                style_config = self.context.style_config

                prompt_data = {
                    **product_info,
                    "style": style_config.get("atmosphere", "专业、现代"),
                    "main_colors": style_config.get("colors", "蓝色+白色")
                }

                # 传入style_config参数
                base_prompt = generate_banner_prompt(prompt_data, style_config)
                count = self.context.generation_count or 5

                self.progress_tracker.complete_step(TaskStep.GENERATE_PROMPT)
                self.progress_tracker.start_step(TaskStep.CALL_API)

                # 调用并行生成（单一风格）- 使用固定 Logo
                results = await self.parallel_generator.generate_multiple_variants(
                    product_image_path=image_path,
                    base_prompt=base_prompt,
                    logo_path=fixed_logo_path,  # 使用固定 Logo
                    count=count,
                    enable_cutout=True,
                    cutout_prompt=f"只保留{product_info.get('product_type', '产品')}",
                    aspect_ratio="9:21",
                    resolution="2k",
                    progress_callback=progress_callback
                )

            else:
                # 多风格对比 或 混合模式
                selected_styles = self.context.selected_styles or []

                if not selected_styles:
                    return {
                        "message": "错误：未选择风格",
                        "state": ConversationState.WELCOME.value,
                        "quick_actions": []
                    }

                # 为每个风格生成提示词
                prompts_with_styles = []
                count_per_style = self.context.generation_count or 1

                for style_name in selected_styles:
                    style_config = get_style_preset(style_name)
                    if not style_config:
                        continue

                    prompt_data = {
                        **product_info,
                        "style": style_config.get("atmosphere", "专业、现代"),
                        "main_colors": style_config.get("colors", "蓝色+白色")
                    }

                    # 传入style_config参数
                    prompt = generate_banner_prompt(prompt_data, style_config)
                    prompts_with_styles.append((prompt, style_name, count_per_style))

                self.progress_tracker.complete_step(TaskStep.GENERATE_PROMPT)
                self.progress_tracker.start_step(TaskStep.CALL_API)

                # 调用并行生成（多风格）- 使用固定 Logo
                results = await self.parallel_generator.generate_multiple_styles(
                    product_image_path=image_path,
                    prompts_with_styles=prompts_with_styles,
                    logo_path=fixed_logo_path,  # 使用固定 Logo
                    enable_cutout=True,
                    cutout_prompt=f"只保留{product_info.get('product_type', '产品')}",
                    aspect_ratio="9:21",
                    resolution="2k",
                    progress_callback=progress_callback
                )

            self.progress_tracker.complete_step(TaskStep.CALL_API)
            self.progress_tracker.start_step(TaskStep.PROCESS_RESULT)

            # 筛选成功的结果
            success_results = [r for r in results if r.get("success")]

            # 检查成功数量（至少3张）
            if len(success_results) < 3:
                error_msg = f"生成失败过多，仅成功{len(success_results)}张（需要至少3张）"
                self.progress_tracker.add_log(error_msg, "error")

                return {
                    "message": f"抱歉，生成过程中遇到问题。{error_msg}\n\n请重试或联系技术支持。",
                    "state": ConversationState.WELCOME.value,
                    "quick_actions": [
                        {"label": "🔄 重新生成", "value": "retry"},
                        {"label": "🏠 返回首页", "value": "home"}
                    ]
                }

            # 保存所有成功的结果
            for result in success_results:
                for file_path in result.get("result_files", []):
                    self.context.add_result({
                        "file_path": file_path,
                        "task_id": result.get("task_id"),
                        "url": file_path,
                        "index": result.get("index"),
                        "style_name": result.get("style_name", "未知风格")
                    })

            self.progress_tracker.complete_step(TaskStep.PROCESS_RESULT)

            # 切换到展示结果状态
            self.context.state = ConversationState.SHOW_RESULTS

            # 保存到知识库（如果用户选择保存）
            if self.knowledge_base and self.context.save_to_kb and not self.context.current_product_id:
                try:
                    product_id = self.knowledge_base.add_product(
                        product_info=self.context.product_info,
                        image_path=self.context.uploaded_files[0] if self.context.uploaded_files else None,
                        logo_path=self.context.logo_path
                    )
                    self.context.current_product_id = product_id
                    self.progress_tracker.add_log(f"[OK] 已保存到知识库: {product_id}")
                except Exception as e:
                    self.progress_tracker.add_log(f"[WARNING] 保存到知识库失败: {str(e)}", "warning")

            # 保存到知识库历史记录
            if self.knowledge_base and self.context.current_product_id:
                all_result_files = []
                for result in success_results:
                    all_result_files.extend(result.get("result_files", []))

                style_names = list(set([r.get("style_name", "N/A") for r in success_results]))
                style_text = "、".join(style_names)

                self.knowledge_base.add_generation_record(
                    product_id=self.context.current_product_id,
                    style_name=style_text,
                    result_files=all_result_files,
                    user_rating=None
                )

            return {
                "message": f"生成完成！共生成{len(success_results)}张易拉宝供您选择。",
                "state": self.context.state.value,
                "results": self.context.results,
                "quick_actions": [
                    {"label": "👍 满意", "value": "satisfied"},
                    {"label": "🔄 重新生成", "value": "regenerate"},
                    {"label": "✏️ 调整参数", "value": "adjust"}
                ]
            }

        except Exception as e:
            self.progress_tracker.add_log(f"生成失败: {str(e)}", "error")

            return {
                "message": f"抱歉，生成过程中出错了：{str(e)}\n\n请重试或联系技术支持。",
                "state": ConversationState.WELCOME.value,
                "quick_actions": [
                    {"label": "🔄 重试", "value": "retry"},
                    {"label": "🏠 返回首页", "value": "home"}
                ]
            }

    async def _start_generation_with_adjustments(self) -> Dict[str, Any]:
        """根据用户反馈调整参数后重新生成"""
        try:
            self.progress_tracker.start_step(TaskStep.GENERATE_PROMPT)

            # 固定使用朴道 Logo（使用相对路径）
            from pathlib import Path
            script_dir = Path(__file__).parent
            fixed_logo_path = script_dir / "朴道logo" / "PUDOW朴道健康水专家-原色.png"

            # 检查 Logo 文件是否存在
            if not fixed_logo_path.exists():
                self.progress_tracker.add_log(f"[WARNING] Logo 文件不存在: {fixed_logo_path}")
                fixed_logo_path = None
            else:
                self.progress_tracker.add_log(f"[OK] 使用固定 Logo: {fixed_logo_path}")
                fixed_logo_path = str(fixed_logo_path)

            # 生成提示词
            product_info = self.context.product_info
            style_config = self.context.style_config
            adjustments = self.context.adjustments

            # 合并产品信息和风格配置
            prompt_data = {
                **product_info,
                "style": style_config.get("atmosphere", "专业、现代"),
                "main_colors": style_config.get("colors", "蓝色+白色")
            }

            # 生成基础提示词（传入style_config）
            base_prompt = generate_banner_prompt(prompt_data, style_config)

            # 应用调整
            adjusted_prompt = self._apply_adjustments_to_prompt(base_prompt, adjustments)

            self.progress_tracker.complete_step(TaskStep.GENERATE_PROMPT)
            self.progress_tracker.start_step(TaskStep.CALL_API)

            # 获取产品图片路径
            image_path = self.context.uploaded_files[0]

            # 进度回调函数
            def progress_callback(message: str):
                self.progress_tracker.add_log(message)

            # 调用完整生成流程 - 使用固定 Logo
            result = await self.banner_generator.generate_complete_flow(
                product_image_path=image_path,
                prompt=adjusted_prompt,
                logo_path=fixed_logo_path,  # 使用固定 Logo
                enable_cutout=True,
                cutout_prompt=f"只保留{product_info.get('product_type', '产品')}",
                aspect_ratio="9:21",
                resolution="2k",
                progress_callback=progress_callback
            )

            self.progress_tracker.complete_step(TaskStep.CALL_API)
            self.progress_tracker.start_step(TaskStep.PROCESS_RESULT)

            if result["success"]:
                # 清空旧结果
                self.context.results = []

                # 保存新结果到上下文
                for file_path in result["result_files"]:
                    self.context.add_result({
                        "file_path": file_path,
                        "task_id": result["task_id"],
                        "url": file_path
                    })

                self.progress_tracker.complete_step(TaskStep.PROCESS_RESULT)

                # 切换到展示结果状态
                self.context.state = ConversationState.SHOW_RESULTS

                # 保存到知识库（如果用户选择保存）
                if self.knowledge_base and self.context.save_to_kb and not self.context.current_product_id:
                    try:
                        # 保存产品信息到知识库
                        product_id = self.knowledge_base.add_product(
                            product_info=self.context.product_info,
                            image_path=self.context.uploaded_files[0] if self.context.uploaded_files else None,
                            logo_path=self.context.logo_path
                        )
                        self.context.current_product_id = product_id
                        self.progress_tracker.add_log(f"✅ 已保存到知识库: {product_id}")
                    except Exception as e:
                        self.progress_tracker.add_log(f"⚠️ 保存到知识库失败: {str(e)}", "warning")

                # 保存到知识库历史记录（_start_generation_with_adjustments）
                if self.knowledge_base and self.context.current_product_id:
                    self.knowledge_base.add_generation_record(
                        product_id=self.context.current_product_id,
                        style_name=style_config.get('name', 'N/A'),
                        result_files=result["result_files"],
                        user_rating=None
                    )

                return {
                    "message": f"✅ 根据您的反馈重新生成完成！共生成 {len(result['result_files'])} 张易拉宝。\n\n请查看右侧结果区域。",
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": "👍 满意", "value": "satisfied"},
                        {"label": "🔄 继续调整", "value": "regenerate"},
                        {"label": "💾 下载全部", "value": "download_all"}
                    ],
                    "results": self.context.results
                }
            else:
                raise Exception(result.get("error", "生成失败"))

        except Exception as e:
            self.progress_tracker.add_log(f"生成失败: {str(e)}", "error")
            self.progress_tracker.complete_step(TaskStep.CALL_API, success=False)

            return {
                "message": f"抱歉，生成时出错了：{str(e)}",
                "state": ConversationState.WELCOME.value,
                "quick_actions": [
                    {"label": "🔄 重试", "value": "retry"}
                ]
            }

    def _apply_adjustments_to_prompt(self, base_prompt: str, adjustments: Dict[str, Any]) -> str:
        """将用户反馈的调整应用到提示词"""
        adjustment_instructions = []

        if adjustments.get("brightness"):
            adjustment_instructions.append(f"亮度调整: {adjustments['brightness']}")

        if adjustments.get("colors"):
            adjustment_instructions.append(f"颜色调整: {adjustments['colors']}")

        if adjustments.get("text_size"):
            adjustment_instructions.append(f"文字大小: {adjustments['text_size']}")

        if adjustments.get("layout"):
            adjustment_instructions.append(f"布局调整: {adjustments['layout']}")

        if adjustment_instructions:
            adjustment_text = "\n".join(adjustment_instructions)
            adjusted_prompt = f"{base_prompt}\n\n【用户反馈调整】\n{adjustment_text}"
            return adjusted_prompt

        return base_prompt

    async def _handle_feedback(self, user_input: str) -> Dict[str, Any]:
        """处理用户反馈"""
        # 保存反馈
        self.context.add_feedback(user_input)

        # 检查是否是快捷按钮
        quick_action = is_quick_action(user_input)

        if quick_action == "satisfied":
            # 用户满意，切换到完成状态（但不重置，允许继续对话）
            self.context.state = ConversationState.COMPLETED

            return {
                "message": "太好了！您可以下载喜欢的设计。\n\n如果需要修改或重新生成，随时告诉我！",
                "state": self.context.state.value,
                "quick_actions": [
                    {"label": "🔄 重新生成", "value": "regenerate"},
                    {"label": "✏️ 修改设计", "value": "modify"},
                    {"label": "🆕 生成新产品", "value": "new"},
                    {"label": "📥 下载全部", "value": "download_all"}
                ]
            }

        elif quick_action == "new":
            # 生成新产品
            self.reset()
            return {
                "message": "好的！请上传新的产品图片开始设计。",
                "state": ConversationState.WELCOME.value,
                "quick_actions": []
            }

        elif quick_action == "download_all":
            # 下载全部（前端处理）
            return {
                "message": "请在右侧结果区域点击各个图片的下载按钮进行下载。",
                "state": self.context.state.value,
                "quick_actions": [
                    {"label": "🔄 生成新产品", "value": "new"}
                ]
            }

        elif quick_action == "retry":
            # 重试生成
            self.context.state = ConversationState.CONFIRM_INTENT

            # 检查是否可以显示生成按钮
            quick_actions = []
            if self._is_ready_to_generate():
                quick_actions = [
                    {"label": "✅ 确认生成", "value": "confirm"},
                    {"label": "✏️ 修改参数", "value": "edit"}
                ]

            return {
                "message": "好的，让我们重试生成。\n\n" + self._get_intent_confirmation_message(),
                "state": self.context.state.value,
                "quick_actions": quick_actions
            }

        elif quick_action == "regenerate":
            # 用户要求重新生成
            self.context.state = ConversationState.COLLECT_STYLE

            styles_text = self._get_style_list_text()

            return {
                "message": f"""好的，让我们重新选择风格。

可选风格：
{styles_text}

请选择您想要的风格：""",
                "state": self.context.state.value,
                "quick_actions": [
                    {"label": f"{config['icon']} {name}", "value": name}
                    for name, config in STYLE_PRESETS.items()
                ]
            }

        else:
            # 自由输入，使用Claude理解反馈
            result = self.conversation_handler.understand_feedback(
                user_input,
                self.context.results
            )

            intent = result.get("intent")

            if intent == "satisfied":
                self.context.state = ConversationState.COMPLETED
                return {
                    "message": result.get("response", "太好了！"),
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": "🔄 生成新产品", "value": "new"},
                        {"label": "📥 下载全部", "value": "download_all"}
                    ]
                }

            elif intent == "adjust_parameters":
                # 用户要求调整参数
                adjustments = result.get("adjustments", {})
                self.context.adjustments.update(adjustments)

                # 应用调整并重新生成
                self.context.state = ConversationState.GENERATING

                adjustment_text = "\n".join([f"- {k}: {v}" for k, v in adjustments.items()])

                # 添加提示消息
                message = f"{result.get('response', '明白了，我将根据您的反馈调整参数')}\n\n调整内容：\n{adjustment_text}\n\n正在重新生成..."

                # 启动生成任务
                generation_result = await self._start_generation_with_adjustments()

                return generation_result

            elif intent == "regenerate":
                self.context.state = ConversationState.COLLECT_STYLE
                return {
                    "message": result.get("response", "好的，让我们重新生成。"),
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": f"{config['icon']} {name}", "value": name}
                        for name, config in STYLE_PRESETS.items()
                    ]
                }

            else:
                return {
                    "message": result.get("response", "请告诉我您的想法。"),
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": "👍 满意", "value": "satisfied"},
                        {"label": "🔄 重新生成", "value": "regenerate"}
                    ]
                }

    async def _handle_post_generation(self, user_input: str) -> Dict[str, Any]:
        """处理生成完成后的对话（允许继续修改或重新生成）"""
        # 检查是否是快捷按钮
        quick_action = is_quick_action(user_input)

        if quick_action == "new":
            # 生成新产品
            self.reset()
            return {
                "message": "好的！请上传新的产品图片开始设计。",
                "state": ConversationState.WELCOME.value,
                "quick_actions": []
            }

        elif quick_action == "download_all":
            # 下载全部（前端处理）
            return {
                "message": "请在右侧结果区域点击各个图片的下载按钮进行下载。",
                "state": self.context.state.value,
                "quick_actions": [
                    {"label": "🔄 重新生成", "value": "regenerate"},
                    {"label": "✏️ 修改设计", "value": "modify"},
                    {"label": "🆕 生成新产品", "value": "new"}
                ]
            }

        elif quick_action == "regenerate":
            # 用户要求重新生成，返回风格选择
            self.context.state = ConversationState.COLLECT_STYLE

            styles_text = self._get_style_list_text()

            return {
                "message": f"""好的，让我们重新选择风格。

可选风格：
{styles_text}

请选择您想要的风格：""",
                "state": self.context.state.value,
                "quick_actions": [
                    {"label": f"{config['icon']} {name}", "value": name}
                    for name, config in STYLE_PRESETS.items()
                ]
            }

        else:
            # 自由输入，使用Claude理解用户意图
            # 判断用户是想修改产品信息还是修改设计
            result = self.conversation_handler.understand_product_modification(
                user_input,
                self.context.product_info,
                self.context.conversation_history,
                self.context.get_persistent_context()
            )

            if result.get("intent") == "modify_product_info":
                # 应用修改
                modifications = result.get("modifications", {})
                for key, value in modifications.items():
                    if key in self.context.product_info:
                        self.context.product_info[key] = value

                # 保存设计要求
                design_requirements = result.get("design_requirements", [])
                for req in design_requirements:
                    self.context.add_design_requirement(req)

                # 格式化更新后的信息
                info_text = self._format_product_info(self.context.product_info)

                response_parts = [result.get('response', '已更新')]

                if modifications:
                    response_parts.append(f"\n\n更新后的信息：\n{info_text}")

                if design_requirements:
                    response_parts.append(f"\n\n设计要求：\n" + "\n".join(f"- {req}" for req in design_requirements))

                response_parts.append("\n\n是否需要根据新的要求重新生成？")

                response_message = "".join(response_parts)

                # 保存Agent响应到对话历史
                self.context.add_conversation("assistant", response_message)

                return {
                    "message": response_message,
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": "✅ 重新生成", "value": "regenerate"},
                        {"label": "✏️ 继续修改", "value": "modify"},
                        {"label": "👍 保持当前结果", "value": "satisfied"}
                    ]
                }
            else:
                # 没有明确的修改意图，提供选项
                response_message = result.get("response", "您可以继续修改产品信息、重新生成，或者开始新的设计。")

                self.context.add_conversation("assistant", response_message)

                return {
                    "message": response_message,
                    "state": self.context.state.value,
                    "quick_actions": [
                        {"label": "🔄 重新生成", "value": "regenerate"},
                        {"label": "✏️ 修改产品信息", "value": "modify"},
                        {"label": "🆕 生成新产品", "value": "new"}
                    ]
                }

    def _format_product_info(self, product_info: Dict[str, Any]) -> str:
        """格式化产品信息为文本"""
        lines = []

        if product_info.get("product_name"):
            lines.append(f"**产品名称**: {product_info['product_name']}")

        if product_info.get("brand"):
            lines.append(f"**品牌**: {product_info['brand']}")

        if product_info.get("slogan"):
            lines.append(f"**核心卖点**: {product_info['slogan']}")

        if product_info.get("product_type"):
            lines.append(f"**产品类型**: {product_info['product_type']}")

        if product_info.get("features"):
            lines.append(f"**产品特点**:")
            for feature in product_info["features"][:5]:  # 只显示前5个
                lines.append(f"  - {feature}")
            if len(product_info["features"]) > 5:
                lines.append(f"  ... 还有 {len(product_info['features']) - 5} 个特点")

        if product_info.get("scenes"):
            lines.append(f"**适用场景**: {', '.join(product_info['scenes'])}")

        return "\n".join(lines)

    def _get_style_list_text(self) -> str:
        """生成风格列表文本"""
        style_list = []
        for i, (name, config) in enumerate(STYLE_PRESETS.items(), 1):
            style_desc = f"{i}. {config['icon']} **{name}**: {config['description']}"

            # 如果是"具体场景"风格,添加预设场景说明
            if config.get('requires_sub_selection', False):
                suggested_scenes = config.get('suggested_scenes', [])
                if suggested_scenes:
                    scenes_text = '\n   '.join([f"• {scene}" for scene in suggested_scenes])
                    style_desc += f"\n   预设场景：\n   {scenes_text}\n   （您也可以自己描述想要的场景）"

            style_list.append(style_desc)

        return '\n'.join(style_list)

    def _get_style_selection_message(self) -> str:
        """获取风格选择消息"""
        styles_text = self._get_style_list_text()

        return f"""好的！现在请选择易拉宝的设计风格：

可选风格：
{styles_text}

⚠️ 请选择：
1. 您希望生成什么风格的易拉宝？
2. 您希望生成几张图片？（建议3-5张）
3. 有特殊的颜色偏好吗？（如果没有，我会根据产品特点自动选择）

请点击下方的风格按钮，或者描述您想要的风格。"""

    def _get_intent_confirmation_message(self) -> str:
        """获取意图确认消息"""
        product_info = self.context.product_info
        style_config = self.context.style_config

        return f"""✅ 意图确认

让我确认一下您的需求：
- **产品**: {product_info.get('product_name', 'N/A')}
- **品牌**: {product_info.get('brand', 'N/A')}
- **风格**: {style_config.get('name', 'N/A')} ({style_config.get('description', 'N/A')})
- **数量**: {self.context.num_images}张
- **主色调**: {style_config.get('colors', 'N/A')}
- **尺寸**: 80x200cm (9:21比例)

⚠️ 最后确认：
1. 以上信息都正确吗？
2. 是否需要调整任何参数？
3. 确认无误后，我将开始生成，预计需要1-2分钟。

请回复"确认"开始生成，或告诉我需要修改的地方。"""

    def _is_ready_to_generate(self) -> bool:
        """检查是否已收集齐所有必要信息，可以显示"开始生成"按钮"""
        # 必须有产品信息
        if not self.context.product_info:
            return False

        # 必须有产品名称和品牌
        product_info = self.context.product_info
        if not product_info.get('product_name') or not product_info.get('brand'):
            return False

        # 必须有风格配置
        if not self.context.style_config:
            return False

        # 风格配置必须包含基本信息
        style_config = self.context.style_config
        if not style_config.get('colors') or not style_config.get('atmosphere'):
            return False

        # 必须有上传的文件
        if not self.context.uploaded_files:
            return False

        return True

    def reset(self):
        """重置Agent状态"""
        self.context.reset()
        self.messages = []
        self.progress_tracker.reset()

    def get_progress(self) -> Dict[str, Any]:
        """获取当前进度"""
        return self.progress_tracker.get_progress_summary()


# 测试代码
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # 从环境变量获取API密钥
    runninghub_key = os.getenv("RUNNINGHUB_API_KEY")
    claude_key = os.getenv("CLAUDE_API_KEY")
    claude_base = os.getenv("CLAUDE_BASE_URL")

    if not runninghub_key or not claude_key:
        print("错误：未找到必要的API密钥")
        exit(1)

    # 创建Agent
    agent = BannerAgent(
        runninghub_api_key=runninghub_key,
        claude_api_key=claude_key,
        claude_base_url=claude_base
    )

    print("=" * 60)
    print("易拉宝AI Agent 测试")
    print("=" * 60)

    # 测试欢迎消息
    async def test():
        response = await agent.process_message("", None)
        print("\n【欢迎消息】")
        print(response["message"])

    asyncio.run(test())
