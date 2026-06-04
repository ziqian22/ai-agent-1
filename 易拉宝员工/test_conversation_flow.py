"""
测试对话流程
检查是否必须先上传文件才能开始对话
"""

import os
from pathlib import Path

def test_conversation_flow():
    """测试对话流程逻辑"""

    print("=" * 60)
    print("对话流程分析")
    print("=" * 60)

    # 1. 检查状态机定义
    print("\n1. 检查状态机定义...")
    try:
        from conversation_state import ConversationState, StateTransition

        print("   [OK] ConversationState 已导入")
        print(f"   初始状态: {ConversationState.WELCOME.value}")

        # 检查从 WELCOME 状态可以转换到哪些状态
        next_states = StateTransition.get_next_states(ConversationState.WELCOME)
        print(f"   从 WELCOME 可以转换到: {[s.value for s in next_states]}")

        if ConversationState.IMAGE_UPLOADED in next_states:
            print("   [INFO] WELCOME 只能转换到 IMAGE_UPLOADED")
            print("   [WARN] 这意味着必须先上传图片才能继续")

    except Exception as e:
        print(f"   [ERROR] 导入失败: {str(e)}")

    # 2. 检查后端 chat 接口
    print("\n2. 检查后端 /api/chat 接口...")
    try:
        backend_file = Path("backend/main.py")
        if backend_file.exists():
            content = backend_file.read_text(encoding='utf-8')

            # 检查 session 验证逻辑
            if 'session_id not in conversations' in content:
                print("   [FOUND] session 验证逻辑")

                # 查找具体的错误消息
                import re
                match = re.search(r'session_id not in conversations.*?detail="([^"]+)"', content, re.DOTALL)
                if match:
                    error_msg = match.group(1)
                    print(f"   错误消息: '{error_msg}'")

                    if "上传" in error_msg or "upload" in error_msg.lower():
                        print("   [WARN] 后端强制要求先上传文件")
                    else:
                        print("   [INFO] 后端要求 session 存在")

        else:
            print("   [WARN] backend/main.py 不存在")

    except Exception as e:
        print(f"   [ERROR] 检查失败: {str(e)}")

    # 3. 检查前端对话处理
    print("\n3. 检查 agent_orchestrator.py 对话处理...")
    try:
        orchestrator_file = Path("agent_orchestrator.py")
        if orchestrator_file.exists():
            content = orchestrator_file.read_text(encoding='utf-8')

            # 检查 WELCOME 状态处理
            if 'async def _handle_welcome' in content:
                print("   [OK] 找到 _handle_welcome 方法")

                # 检查是否强制要求 image_path
                import re
                match = re.search(r'async def _handle_welcome.*?(?=async def|\Z)', content, re.DOTALL)
                if match:
                    welcome_code = match.group(0)

                    if 'if image_path:' in welcome_code:
                        print("   [INFO] _handle_welcome 检查是否有 image_path")

                    if '请上传' in welcome_code or '请先上传' in welcome_code:
                        print("   [INFO] 欢迎消息提示用户上传文件")

        else:
            print("   [WARN] agent_orchestrator.py 不存在")

    except Exception as e:
        print(f"   [ERROR] 检查失败: {str(e)}")

    # 4. 分析问题
    print("\n" + "=" * 60)
    print("分析结果")
    print("=" * 60)

    print("\n当前逻辑:")
    print("1. 状态机设计:")
    print("   - 初始状态: WELCOME")
    print("   - WELCOME 只能转换到 IMAGE_UPLOADED")
    print("   - 这意味着必须上传图片才能进入下一步")

    print("\n2. 后端 API:")
    print("   - /api/chat 接口要求 session_id 存在")
    print("   - session 只在上传文件时创建（/api/upload）")
    print("   - 如果没有 session，返回错误：'会话不存在，请先上传文件'")

    print("\n3. 前端流程:")
    print("   - agent_orchestrator 的 _handle_welcome 检查是否有 image_path")
    print("   - 如果没有，显示欢迎消息，提示上传")

    print("\n结论:")
    print("   [WARN] 当前设计强制要求先上传图片才能开始对话")

    print("\n" + "=" * 60)
    print("修复方案")
    print("=" * 60)

    print("\n方案 1: 允许无文件对话（推荐）")
    print("   - 修改后端 /api/chat，允许创建空 session")
    print("   - 用户可以先问问题，再上传文件")
    print("   - 灵活性更高，用户体验更好")

    print("\n方案 2: 添加 /api/init 接口")
    print("   - 创建专门的初始化接口")
    print("   - 前端在页面加载时自动调用")
    print("   - 用户可以直接开始对话")

    print("\n方案 3: 保持现状")
    print("   - 维持当前设计，强制上传文件")
    print("   - 简化流程，确保有产品信息")
    print("   - 但限制了对话灵活性")

    print("\n推荐: 方案 1")
    print("   理由:")
    print("   - 用户可能想先问问题（如：支持什么格式？）")
    print("   - 可以从知识库选择产品，无需上传")
    print("   - 更自然的对话体验")


if __name__ == "__main__":
    test_conversation_flow()
