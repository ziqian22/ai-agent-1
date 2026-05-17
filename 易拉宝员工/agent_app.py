"""
易拉宝AI Agent Streamlit界面
对话式交互界面，支持图片上传、风格选择、进度跟踪
"""

import streamlit as st
import asyncio
import os
from pathlib import Path
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

from agent_orchestrator import BannerAgent
from conversation_state import ConversationState, STYLE_PRESETS
from knowledge_base import KnowledgeBase

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="易拉宝AI设计助手",
    page_icon="🎨",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .style-card {
        padding: 1rem;
        border: 2px solid #e0e0e0;
        border-radius: 0.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    .style-card:hover {
        border-color: #1f77b4;
        background-color: #f0f8ff;
    }
    .progress-step {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 0.25rem;
    }
    .progress-step.completed {
        background-color: #d4edda;
    }
    .progress-step.running {
        background-color: #fff3cd;
    }
    .progress-step.pending {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)


# 初始化session state
def init_session_state():
    """初始化会话状态"""
    # 先初始化知识库（最优先）
    if 'knowledge_base' not in st.session_state:
        st.session_state.knowledge_base = KnowledgeBase()

    if 'agent' not in st.session_state:
        # 从环境变量或用户输入获取API密钥
        runninghub_key = os.getenv("RUNNINGHUB_API_KEY", "")
        claude_key = os.getenv("CLAUDE_API_KEY", "")
        claude_base = os.getenv("CLAUDE_BASE_URL")

        if runninghub_key and claude_key:
            st.session_state.agent = BannerAgent(
                runninghub_api_key=runninghub_key,
                claude_api_key=claude_key,
                claude_base_url=claude_base,
                knowledge_base=st.session_state.knowledge_base  # 传入知识库实例
            )
        else:
            st.session_state.agent = None

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'current_image' not in st.session_state:
        st.session_state.current_image = None

    if 'current_logo' not in st.session_state:
        st.session_state.current_logo = None

    if 'show_progress' not in st.session_state:
        st.session_state.show_progress = False

    if 'results' not in st.session_state:
        st.session_state.results = []

    if 'need_process_image' not in st.session_state:
        st.session_state.need_process_image = False

    if 'need_process_with_style' not in st.session_state:
        st.session_state.need_process_with_style = False

    if 'need_load_from_kb' not in st.session_state:
        st.session_state.need_load_from_kb = False

    if 'kb_product_id' not in st.session_state:
        st.session_state.kb_product_id = None

    if 'show_kb_manager' not in st.session_state:
        st.session_state.show_kb_manager = False

    if 'viewing_product_id' not in st.session_state:
        st.session_state.viewing_product_id = None

    if 'editing_product_id' not in st.session_state:
        st.session_state.editing_product_id = None

    if 'preset_style' not in st.session_state:
        st.session_state.preset_style = None

    if 'save_to_kb' not in st.session_state:
        st.session_state.save_to_kb = True  # 默认保存到知识库


def main():
    """主函数"""
    init_session_state()

    # 标题栏 - 添加菜单按钮
    col_title, col_restart_btn, col_kb_btn = st.columns([3, 1, 1])
    with col_title:
        st.title("🎨 易拉宝AI设计助手")
    with col_restart_btn:
        st.markdown("<br>", unsafe_allow_html=True)  # 添加一点垂直间距
        if st.button("🔄 重新开始", use_container_width=True):
            if st.session_state.agent:
                st.session_state.agent.reset()
            st.session_state.messages = []
            st.session_state.current_image = None
            st.session_state.current_logo = None
            st.session_state.results = []
            st.rerun()
    with col_kb_btn:
        st.markdown("<br>", unsafe_allow_html=True)  # 添加一点垂直间距
        if st.button("📚 知识库管理", use_container_width=True):
            st.session_state.show_kb_manager = not st.session_state.show_kb_manager
            st.rerun()

    st.markdown("---")

    # 如果没有配置Agent，显示配置界面
    if not st.session_state.agent:
        show_config_page()
        return

    # 检查是否需要处理图片
    if st.session_state.need_process_image:
        st.session_state.need_process_image = False
        asyncio.run(process_image_upload())

    # 检查是否需要处理图片并应用预设风格
    if st.session_state.need_process_with_style:
        st.session_state.need_process_with_style = False
        asyncio.run(process_image_with_preset_style())

    # 检查是否需要从知识库加载产品
    if st.session_state.need_load_from_kb:
        st.session_state.need_load_from_kb = False
        asyncio.run(process_knowledge_base_load())

    # 主布局：三栏
    col1, col2, col3 = st.columns([1, 2, 1.5])

    # 左侧栏：文件上传和快捷操作
    with col1:
        show_sidebar()

    # 中间栏：对话区
    with col2:
        show_chat_area()

    # 右侧栏：进度和结果
    with col3:
        show_progress_and_results()

    # 知识库管理界面（如果打开）
    if st.session_state.get('show_kb_manager', False):
        show_knowledge_base_manager()


def show_config_page():
    """显示配置页面"""
    st.header("⚙️ API配置")
    st.info("请先配置API密钥才能使用")

    with st.form("api_config_form"):
        runninghub_key = st.text_input(
            "Running Hub API Key",
            type="password",
            help="用于生成易拉宝的API密钥"
        )

        claude_key = st.text_input(
            "Claude API Key",
            type="password",
            help="用于图片分析的Claude API密钥"
        )

        claude_base = st.text_input(
            "Claude API Base URL (可选)",
            placeholder="https://api.anthropic.com",
            help="如果使用中转服务，请填写中转API的base_url"
        )

        submitted = st.form_submit_button("✅ 保存配置")

        if submitted:
            if not runninghub_key or not claude_key:
                st.error("请填写必要的API密钥")
            else:
                try:
                    # 创建Agent
                    agent = BannerAgent(
                        runninghub_api_key=runninghub_key,
                        claude_api_key=claude_key,
                        claude_base_url=claude_base if claude_base else None,
                        knowledge_base=st.session_state.knowledge_base  # 传入知识库实例
                    )

                    # 测试连接
                    with st.spinner("测试API连接..."):
                        if agent.vision_analyzer.test_connection():
                            st.session_state.agent = agent
                            st.success("✅ 配置成功！")
                            st.rerun()
                        else:
                            st.error("❌ Claude API连接失败，请检查配置")

                except Exception as e:
                    st.error(f"配置失败：{str(e)}")


def show_sidebar():
    """显示侧边栏"""
    st.header("📚 知识库")

    # 输入方式选择
    input_method = st.radio(
        "选择输入方式",
        ["从对话区上传", "知识库导入"],
        horizontal=True,
        key="input_method"
    )

    if input_method == "知识库导入":
        show_knowledge_base_import()
    else:
        st.info("👈 请在右侧对话区上传文件")

    st.markdown("---")

    # 显示当前状态
    if st.session_state.agent:
        st.subheader("📊 当前状态")
        current_state = st.session_state.agent.context.state
        st.info(f"状态: {current_state.value}")


def show_chat_area():
    """显示对话区"""
    st.header("💬 与AI助手对话")

    # 文件上传区域（固定在对话区上方）
    with st.container():
        uploaded_file = st.file_uploader(
            "📤 上传产品图片或文档开始分析",
            type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'pptx'],
            key="chat_file_uploader",
            help="支持图片（PNG/JPG）和文档（PDF/Word/PPT）"
        )

        if uploaded_file:
            # 自动保存并触发分析
            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)

            temp_path = temp_dir / uploaded_file.name
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.session_state.current_image = str(temp_path)

            # 检测文件类型
            file_ext = temp_path.suffix.lower()
            if file_ext in ['.pdf']:
                st.session_state.file_type = 'PDF'
            elif file_ext in ['.docx', '.doc']:
                st.session_state.file_type = 'Word'
            elif file_ext in ['.pptx', '.ppt']:
                st.session_state.file_type = 'PowerPoint'
            else:
                st.session_state.file_type = '图片'

            # 标记需要处理
            st.session_state.need_process_image = True
            st.rerun()

    # 显示已上传状态
    if st.session_state.get('current_image'):
        file_name = Path(st.session_state.current_image).name
        file_type = st.session_state.get('file_type', '文件')
        st.success(f"✅ 已上传: {file_name} ({file_type})")

        # 显示 Logo 上传（可选）
        if not st.session_state.get('current_logo'):
            with st.expander("🎨 上传品牌 Logo（可选）"):
                logo_file = st.file_uploader(
                    "品牌 Logo",
                    type=['png', 'jpg', 'jpeg'],
                    key="logo_uploader_chat",
                    help="Logo 会被合成到易拉宝右上角"
                )

                if logo_file:
                    temp_dir = Path("temp_uploads")
                    temp_dir.mkdir(exist_ok=True)

                    logo_path = temp_dir / f"logo_{logo_file.name}"
                    with open(logo_path, "wb") as f:
                        f.write(logo_file.getbuffer())

                    st.session_state.current_logo = str(logo_path)
                    st.success("✅ Logo 已上传")
                    st.rerun()
        else:
            # 显示已上传的 Logo
            if Path(st.session_state.current_logo).exists():
                col_logo, col_remove = st.columns([3, 1])
                with col_logo:
                    st.image(st.session_state.current_logo, caption="当前 Logo", width=100)
                with col_remove:
                    if st.button("🗑️ 移除"):
                        st.session_state.current_logo = None
                        st.rerun()

    st.caption("💡 支持格式：图片（PNG/JPG）、文档（PDF/Word/PPT）")

    st.markdown("---")

    # 对话历史容器
    chat_container = st.container(height=400)

    with chat_container:
        # 如果没有消息，显示欢迎消息
        if not st.session_state.messages:
            with st.chat_message("assistant"):
                st.markdown("""您好！我是易拉宝设计助手 🎨

我可以帮您：
1. 分析产品图片或文档，提取产品信息
2. 根据您的需求设计易拉宝
3. 生成多张设计供您选择
4. 根据反馈优化设计

请上传产品图片或文档开始吧！""")

        # 显示历史消息
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

                # 如果有快捷按钮
                if msg.get("quick_actions"):
                    cols = st.columns(len(msg["quick_actions"]))
                    for idx, action in enumerate(msg["quick_actions"]):
                        with cols[idx]:
                            if st.button(
                                action["label"],
                                key=f"qa_{msg.get('id', 0)}_{idx}"
                            ):
                                asyncio.run(handle_quick_action(action["value"]))

                # 如果有提取的图片预览
                if msg.get("extracted_images"):
                    st.markdown("**文档中的图片：**")
                    cols = st.columns(min(len(msg["extracted_images"]), 3))
                    for idx, img_path in enumerate(msg["extracted_images"]):
                        with cols[idx % 3]:
                            if Path(img_path).exists():
                                st.image(img_path, caption=f"图片 {idx+1}", use_column_width=True)

    # 输入区
    st.markdown("---")

    user_input = st.chat_input("输入您的需求或问题...")

    if user_input:
        asyncio.run(process_user_message(user_input))


def show_progress_and_results():
    """显示进度和结果"""
    tab1, tab2 = st.tabs(["📊 生成进度", "🎨 生成结果"])

    with tab1:
        show_progress_tab()

    with tab2:
        show_results_tab()


def show_progress_tab():
    """显示进度标签页"""
    st.subheader("当前任务进度")

    if st.session_state.show_progress and st.session_state.agent:
        progress = st.session_state.agent.get_progress()

        # 步骤指示器
        for step_info in progress["steps"]:
            status_class = step_info["status"]
            st.markdown(
                f'<div class="progress-step {status_class}">'
                f'{step_info["icon"]} {step_info["name"]}'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown("---")

        # 进度条
        progress_value = progress["percentage"]
        st.progress(progress_value / 100)
        st.caption(f"进度: {progress_value}% | 预计剩余: {progress['eta']}")

        st.markdown("---")

        # 实时日志
        with st.expander("📝 详细日志", expanded=False):
            for log in progress["logs"]:
                st.text(f"[{log['time']}] {log['message']}")
    else:
        st.info("暂无进行中的任务")


def show_results_tab():
    """显示结果标签页"""
    st.subheader("生成的易拉宝")

    if st.session_state.results:
        for idx, result in enumerate(st.session_state.results):
            with st.container(border=True):
                # 显示本地文件
                file_path = result.get("file_path", "")
                if file_path and Path(file_path).exists():
                    st.image(file_path, use_column_width=True)
                else:
                    st.warning("图片文件不存在")

                # 操作按钮
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("👍", key=f"like_{idx}", help="喜欢"):
                        st.success("已标记为喜欢")
                with col_b:
                    # 下载按钮
                    if file_path and Path(file_path).exists():
                        with open(file_path, "rb") as f:
                            st.download_button(
                                "💾 下载",
                                data=f.read(),
                                file_name=Path(file_path).name,
                                mime="image/png",
                                key=f"download_{idx}"
                            )
                with col_c:
                    if st.button("🔄", key=f"regenerate_{idx}", help="基于此重新生成"):
                        st.info("重新生成功能开发中...")
    else:
        st.info("还没有生成结果")


async def process_image_upload():
    """处理图片上传"""
    if not st.session_state.current_image:
        st.error("请先上传图片或文档")
        return

    # 添加用户消息
    file_type = st.session_state.get('file_type', '文件')
    message_content = f"我上传了{file_type}"
    if st.session_state.current_logo:
        message_content += "和品牌Logo"

    st.session_state.messages.append({
        "role": "user",
        "content": message_content,
        "id": len(st.session_state.messages)
    })

    # 显示进度
    st.session_state.show_progress = True

    # 获取是否保存到知识库的选项
    save_to_kb = st.session_state.get('save_to_kb', True)

    # 第一步：通知Agent图片已上传
    response1 = await st.session_state.agent.process_message(
        "",
        st.session_state.current_image,
        st.session_state.current_logo,
        save_to_kb=save_to_kb  # 传递保存选项
    )

    # 添加"正在分析"的消息
    message_data = {
        "role": "assistant",
        "content": response1["message"],
        "quick_actions": response1.get("quick_actions", []),
        "id": len(st.session_state.messages)
    }

    # 如果有提取的图片，添加到消息中
    if response1.get("extracted_images"):
        message_data["extracted_images"] = response1["extracted_images"]

    st.session_state.messages.append(message_data)

    # 第二步：立即触发实际分析（如果状态是IMAGE_UPLOADED）
    if response1["state"] == ConversationState.IMAGE_UPLOADED.value:
        with st.spinner("AI分析中..."):
            response2 = await st.session_state.agent.process_message(
                "",
                st.session_state.current_image,
                st.session_state.current_logo,
                save_to_kb=save_to_kb  # 传递保存选项
            )

        # 添加分析结果
        message_data2 = {
            "role": "assistant",
            "content": response2["message"],
            "quick_actions": response2.get("quick_actions", []),
            "id": len(st.session_state.messages)
        }

        # 如果有提取的图片，添加到消息中
        if response2.get("extracted_images"):
            message_data2["extracted_images"] = response2["extracted_images"]

        st.session_state.messages.append(message_data2)

    st.rerun()


async def process_image_with_preset_style():
    """处理图片上传并应用预设风格"""
    if not st.session_state.current_image:
        st.error("请先上传图片")
        return

    preset_style = st.session_state.get('preset_style')
    if not preset_style:
        st.error("未设置预设风格")
        return

    # 显示进度
    st.session_state.show_progress = True

    # 获取是否保存到知识库的选项
    save_to_kb = st.session_state.get('save_to_kb', True)

    # 第一步：通知Agent图片已上传
    response1 = await st.session_state.agent.process_message(
        "",
        st.session_state.current_image,
        st.session_state.current_logo,
        save_to_kb=save_to_kb
    )

    # 第二步：立即触发实际分析
    if response1["state"] == ConversationState.IMAGE_UPLOADED.value:
        with st.spinner("AI分析中..."):
            response2 = await st.session_state.agent.process_message(
                "",
                st.session_state.current_image,
                st.session_state.current_logo,
                save_to_kb=save_to_kb
            )

        # 添加分析结果
        st.session_state.messages.append({
            "role": "assistant",
            "content": response2["message"],
            "quick_actions": response2.get("quick_actions", []),
            "id": len(st.session_state.messages)
        })

    # 第三步：应用预设风格并开始生成
    with st.spinner(f"应用 {preset_style} 风格并生成中..."):
        # 发送风格选择消息
        response3 = await st.session_state.agent.process_message(
            f"使用{preset_style}风格"
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": response3["message"],
            "quick_actions": response3.get("quick_actions", []),
            "id": len(st.session_state.messages)
        })

        # 如果有结果，更新结果列表
        if response3.get("results"):
            st.session_state.results = response3["results"]

    # 清除预设风格标志
    st.session_state.preset_style = None

    st.rerun()


async def process_knowledge_base_load():
    """处理从知识库加载产品"""
    if not st.session_state.kb_product_id:
        st.error("未选择产品")
        return

    # 调用Agent的知识库加载方法
    try:
        with st.spinner("正在加载产品信息..."):
            response = await st.session_state.agent.load_from_knowledge_base(
                st.session_state.kb_product_id
            )

        # 添加Agent响应
        message_data = {
            "role": "assistant",
            "content": response["message"],
            "quick_actions": response.get("quick_actions", []),
            "id": len(st.session_state.messages)
        }

        st.session_state.messages.append(message_data)

        # 清除产品ID标志
        st.session_state.kb_product_id = None

    except Exception as e:
        st.error(f"加载产品信息时出错: {str(e)}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"抱歉，加载产品信息时出错了：{str(e)}\n\n请重试或联系管理员。",
            "quick_actions": [
                {"label": "🔄 重试", "value": "retry"}
            ],
            "id": len(st.session_state.messages)
        })

    st.rerun()


async def process_user_message(user_input: str):
    """处理用户消息"""
    # 添加用户消息
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "id": len(st.session_state.messages)
    })

    # 调用Agent处理
    try:
        with st.spinner("AI思考中..."):
            response = await st.session_state.agent.process_message(user_input)

        # 添加Agent响应
        message_data = {
            "role": "assistant",
            "content": response["message"],
            "quick_actions": response.get("quick_actions", []),
            "id": len(st.session_state.messages)
        }

        # 如果有提取的图片，添加到消息中
        if response.get("extracted_images"):
            message_data["extracted_images"] = response["extracted_images"]

        st.session_state.messages.append(message_data)

        # 如果进入生成状态，显示进度
        if response["state"] == ConversationState.GENERATING.value:
            st.session_state.show_progress = True

        # 如果有结果，更新结果列表
        if response.get("results"):
            st.session_state.results = response["results"]

    except Exception as e:
        st.error(f"处理消息时出错: {str(e)}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"抱歉，处理您的消息时出错了：{str(e)}\n\n请重试或联系管理员。",
            "quick_actions": [
                {"label": "🔄 重试", "value": "retry"}
            ],
            "id": len(st.session_state.messages)
        })

    st.rerun()


async def handle_quick_action(action_value: str):
    """处理快捷操作"""
    await process_user_message(action_value)


def show_knowledge_base_import():
    """显示知识库导入界面"""
    st.subheader("📚 从知识库选择")

    # 获取所有产品
    products = st.session_state.knowledge_base.get_all_products()

    if not products:
        st.info("知识库为空，请先添加产品")
        return

    # 搜索框
    search_query = st.text_input("🔍 搜索产品", placeholder="输入产品名称、品牌...")

    # 筛选产品
    if search_query:
        filtered_products = st.session_state.knowledge_base.search_products(search_query)
    else:
        filtered_products = products

    if not filtered_products:
        st.warning("没有找到匹配的产品")
        return

    # 产品选择器
    product_options = {
        f"{p['product_info'].get('product_name', 'N/A')} - {p['product_info'].get('brand', 'N/A')}": p
        for p in filtered_products
    }

    selected_name = st.selectbox(
        "选择产品",
        options=list(product_options.keys())
    )

    if selected_name:
        selected_product = product_options[selected_name]

        # 显示产品预览
        with st.expander("📋 产品信息预览", expanded=True):
            product_info = selected_product['product_info']
            st.write(f"**产品名称**: {product_info.get('product_name', 'N/A')}")
            st.write(f"**品牌**: {product_info.get('brand', 'N/A')}")
            st.write(f"**类型**: {product_info.get('product_type', 'N/A')}")

            # 显示产品图片
            if selected_product.get('image_path') and Path(selected_product['image_path']).exists():
                st.image(selected_product['image_path'], width=200)

        if st.button("✅ 使用此产品", type="primary", use_container_width=True):
            # 使用知识库快速加载流程
            st.session_state.kb_product_id = selected_product['id']
            st.session_state.need_load_from_kb = True
            st.rerun()


def show_knowledge_base_manager():
    """显示知识库管理界面"""
    st.markdown("---")
    st.header("📚 产品知识库管理")

    tab1, tab2, tab3 = st.tabs(["产品列表", "添加产品", "统计信息"])

    with tab1:
        show_product_list()

    with tab2:
        show_add_product_form()

    with tab3:
        show_statistics()


def show_product_list():
    """显示产品列表"""
    st.subheader("产品列表")

    products = st.session_state.knowledge_base.get_all_products()

    if not products:
        st.info("知识库为空")
        return

    # 搜索和筛选
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search = st.text_input("🔍 搜索", placeholder="产品名称、品牌...")

    # 筛选产品
    if search:
        filtered_products = st.session_state.knowledge_base.search_products(search)
    else:
        filtered_products = products

    # 显示产品卡片
    for product in filtered_products:
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 3, 1])

            with col1:
                # 显示产品图片
                if product.get('image_path') and Path(product['image_path']).exists():
                    st.image(product['image_path'], use_column_width=True)

            with col2:
                product_info = product['product_info']
                st.markdown(f"### {product_info.get('product_name', 'N/A')}")
                st.write(f"**品牌**: {product_info.get('brand', 'N/A')}")
                st.write(f"**类型**: {product_info.get('product_type', 'N/A')}")
                st.caption(f"创建时间: {product.get('created_at', 'N/A')}")

                # 显示历史生成记录
                history = product.get('generation_history', [])
                if history:
                    st.caption(f"📊 历史生成: {len(history)} 次")

            with col3:
                if st.button("✏️ 编辑", key=f"edit_{product['id']}"):
                    st.session_state.editing_product_id = product['id']
                    st.rerun()

                if st.button("📜 查看历史", key=f"view_{product['id']}"):
                    st.session_state.viewing_product_id = product['id']
                    st.rerun()

                if st.button("🗑️ 删除", key=f"del_{product['id']}"):
                    if st.session_state.knowledge_base.delete_product(product['id']):
                        st.success("删除成功")
                        st.rerun()

    # 如果正在编辑某个产品
    if st.session_state.get('editing_product_id'):
        show_edit_product_form(st.session_state.editing_product_id)

    # 如果正在查看某个产品的历史
    if st.session_state.get('viewing_product_id'):
        show_product_history(st.session_state.viewing_product_id)


def show_add_product_form():
    """显示添加产品表单"""
    st.subheader("添加新产品")

    with st.form("add_product_form"):
        # 基本信息
        product_name = st.text_input("产品名称*", placeholder="例如：勇士K6直饮机")
        brand = st.text_input("品牌*", placeholder="例如：朴道健康水专家")
        product_type = st.selectbox(
            "产品类型*",
            ["饮水机", "化妆品", "电子产品", "食品饮料", "家居用品", "其他"]
        )

        # 产品特点
        features = st.text_area(
            "产品特点",
            placeholder="每行一个特点\n例如：\n高达125L/H开水量\n100℃开水持续出\n4重深度净化",
            height=150
        )

        # 适用场景
        scenes = st.text_input(
            "适用场景",
            placeholder="用逗号分隔，例如：商务办公,政府机关,医院病房"
        )

        # 产品文件
        product_image = st.file_uploader(
            "产品图片",
            type=['png', 'jpg', 'jpeg'],
            help="上传产品图片"
        )

        logo_image = st.file_uploader(
            "品牌Logo（可选）",
            type=['png', 'jpg', 'jpeg'],
            help="上传品牌Logo"
        )

        # 提交按钮
        submitted = st.form_submit_button("✅ 添加到知识库", type="primary")

        if submitted:
            if not product_name or not brand:
                st.error("请填写必填项")
            else:
                # 保存上传的文件
                temp_dir = Path("temp_uploads")
                temp_dir.mkdir(exist_ok=True)

                image_path = None
                if product_image:
                    image_path = temp_dir / product_image.name
                    with open(image_path, "wb") as f:
                        f.write(product_image.getbuffer())

                logo_path = None
                if logo_image:
                    logo_path = temp_dir / logo_image.name
                    with open(logo_path, "wb") as f:
                        f.write(logo_image.getbuffer())

                # 构建产品信息
                product_info = {
                    "product_name": product_name,
                    "brand": brand,
                    "product_type": product_type,
                    "features": [f.strip() for f in features.split('\n') if f.strip()],
                    "scenes": [s.strip() for s in scenes.split(',') if s.strip()]
                }

                # 添加到知识库
                product_id = st.session_state.knowledge_base.add_product(
                    product_info,
                    str(image_path) if image_path else None,
                    str(logo_path) if logo_path else None
                )

                st.success(f"✅ 已添加产品: {product_name}")
                st.rerun()


def show_edit_product_form(product_id: str):
    """显示编辑产品表单"""
    st.markdown("---")
    st.header("✏️ 编辑产品信息")

    product = st.session_state.knowledge_base.get_product(product_id)

    if not product:
        st.error("产品不存在")
        return

    product_info = product['product_info']

    # 关闭按钮
    if st.button("❌ 取消编辑"):
        st.session_state.editing_product_id = None
        st.rerun()

    st.markdown("---")

    with st.form("edit_product_form"):
        # 基本信息
        product_name = st.text_input(
            "产品名称*",
            value=product_info.get('product_name', ''),
            placeholder="例如：勇士K6直饮机"
        )
        brand = st.text_input(
            "品牌*",
            value=product_info.get('brand', ''),
            placeholder="例如：朴道健康水专家"
        )
        product_type = st.selectbox(
            "产品类型*",
            ["饮水机", "化妆品", "电子产品", "食品饮料", "家居用品", "其他"],
            index=["饮水机", "化妆品", "电子产品", "食品饮料", "家居用品", "其他"].index(
                product_info.get('product_type', '其他')
            ) if product_info.get('product_type') in ["饮水机", "化妆品", "电子产品", "食品饮料", "家居用品", "其他"] else 5
        )

        # 产品特点
        features_text = '\n'.join(product_info.get('features', []))
        features = st.text_area(
            "产品特点",
            value=features_text,
            placeholder="每行一个特点",
            height=150
        )

        # 适用场景
        scenes_text = ', '.join(product_info.get('scenes', []))
        scenes = st.text_input(
            "适用场景",
            value=scenes_text,
            placeholder="用逗号分隔"
        )

        # 提交按钮
        submitted = st.form_submit_button("✅ 保存修改", type="primary")

        if submitted:
            if not product_name or not brand:
                st.error("请填写必填项")
            else:
                # 构建更新的产品信息
                updated_info = {
                    "product_name": product_name,
                    "brand": brand,
                    "product_type": product_type,
                    "features": [f.strip() for f in features.split('\n') if f.strip()],
                    "scenes": [s.strip() for s in scenes.split(',') if s.strip()]
                }

                # 更新产品信息
                if st.session_state.knowledge_base.update_product(product_id, updated_info):
                    st.success(f"✅ 已更新产品: {product_name}")
                    st.session_state.editing_product_id = None
                    st.rerun()
                else:
                    st.error("更新失败")



def show_statistics():
    """显示统计信息"""
    st.subheader("知识库统计")

    stats = st.session_state.knowledge_base.get_statistics()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("产品总数", stats['total_products'])

    with col2:
        st.metric("生成总数", stats['total_generations'])

    with col3:
        st.metric("产品类型", len(stats['product_types']))

    # 产品类型分布
    if stats['product_types']:
        st.markdown("---")
        st.subheader("产品类型分布")

        for product_type, count in stats['product_types'].items():
            st.write(f"**{product_type}**: {count} 个")


def show_product_history(product_id: str):
    """显示产品的历史生成记录"""
    st.markdown("---")
    st.header("📜 历史生成记录")

    product = st.session_state.knowledge_base.get_product(product_id)

    if not product:
        st.error("产品不存在")
        return

    # 显示产品信息
    product_info = product['product_info']
    st.subheader(f"{product_info.get('product_name', 'N/A')} - {product_info.get('brand', 'N/A')}")

    # 关闭按钮
    if st.button("❌ 关闭历史记录"):
        st.session_state.viewing_product_id = None
        st.rerun()

    st.markdown("---")

    # 获取历史记录
    history = product.get('generation_history', [])

    if not history:
        st.info("该产品还没有生成记录")
        return

    st.write(f"共有 {len(history)} 条历史记录")

    # 显示每条历史记录
    for idx, record in enumerate(reversed(history)):  # 最新的在前
        with st.expander(f"🎨 生成记录 #{len(history) - idx} - {record.get('style', 'N/A')} 风格", expanded=(idx == 0)):
            st.caption(f"生成时间: {record.get('created_at', 'N/A')}")

            # 显示生成的图片
            result_files = record.get('result_files', [])

            if result_files:
                cols = st.columns(min(len(result_files), 3))

                for file_idx, file_path in enumerate(result_files):
                    with cols[file_idx % 3]:
                        if Path(file_path).exists():
                            st.image(file_path, use_column_width=True)

                            # 下载按钮
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    "💾 下载",
                                    data=f.read(),
                                    file_name=Path(file_path).name,
                                    mime="image/png",
                                    key=f"download_history_{idx}_{file_idx}"
                                )
                        else:
                            st.warning("文件不存在")

                # 基于此记录重新生成
                if st.button("🔄 基于此风格重新生成", key=f"regen_{idx}"):
                    # 加载产品信息到当前会话
                    st.session_state.current_image = product.get('image_path')
                    st.session_state.current_logo = product.get('logo_path')

                    # 设置风格
                    style_name = record.get('style')
                    st.session_state.preset_style = style_name

                    # 关闭历史记录和知识库管理
                    st.session_state.viewing_product_id = None
                    st.session_state.show_kb_manager = False

                    # 重置Agent状态
                    st.session_state.agent.reset()
                    st.session_state.messages = []
                    st.session_state.results = []

                    # 添加提示消息
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"已加载产品信息，将使用 **{style_name}** 风格重新生成易拉宝。",
                        "id": 0
                    })

                    # 标记需要处理图片并应用风格
                    st.session_state.need_process_with_style = True
                    st.rerun()
            else:
                st.info("该记录没有生成文件")

            # 用户评分
            user_rating = record.get('user_rating')
            if user_rating:
                st.write(f"⭐ 用户评分: {user_rating}/5")




if __name__ == "__main__":
    main()
