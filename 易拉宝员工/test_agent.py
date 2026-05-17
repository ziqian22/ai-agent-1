"""
Agent核心功能测试脚本
测试对话流程和各个模块的集成
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 设置UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from agent_orchestrator import BannerAgent
from conversation_state import ConversationState

# 加载环境变量
load_dotenv()


async def test_agent_flow():
    """测试完整的Agent对话流程"""
    print("=" * 60)
    print("易拉宝AI Agent 核心功能测试")
    print("=" * 60)

    # 获取API密钥
    runninghub_key = os.getenv("RUNNINGHUB_API_KEY")
    claude_key = os.getenv("CLAUDE_API_KEY")
    claude_base = os.getenv("CLAUDE_BASE_URL")

    if not runninghub_key:
        print("❌ 错误：未找到RUNNINGHUB_API_KEY")
        print("请在.env文件中配置API密钥")
        return

    if not claude_key:
        print("❌ 错误：未找到CLAUDE_API_KEY")
        print("请在.env文件中配置Claude API密钥")
        return

    # 创建Agent
    print("\n【1. 初始化Agent】")
    agent = BannerAgent(
        runninghub_api_key=runninghub_key,
        claude_api_key=claude_key,
        claude_base_url=claude_base
    )
    print("✅ Agent初始化成功")

    # 测试欢迎消息
    print("\n【2. 测试欢迎消息】")
    response = await agent.process_message("", None)
    print(f"状态: {response['state']}")
    print(f"消息:\n{response['message']}")

    # 测试图片上传和分析
    print("\n【3. 测试图片分析】")
    test_image = "74f8c6f71010b7553325446bec13f5a5.jpg"

    if not Path(test_image).exists():
        print(f"⚠️ 测试图片不存在: {test_image}")
        print("跳过图片分析测试")
        return

    print(f"上传图片: {test_image}")
    response = await agent.process_message("", test_image)
    print(f"状态: {response['state']}")
    print(f"消息:\n{response['message']}")

    if response.get("product_info"):
        print("\n提取的产品信息:")
        product_info = response["product_info"]
        print(f"  产品名称: {product_info.get('product_name', 'N/A')}")
        print(f"  品牌: {product_info.get('brand', 'N/A')}")
        print(f"  产品类型: {product_info.get('product_type', 'N/A')}")
        print(f"  特点数量: {len(product_info.get('features', []))}")

    # 测试产品确认
    print("\n【4. 测试产品确认】")
    response = await agent.process_message("确认", None)
    print(f"状态: {response['state']}")
    print(f"消息:\n{response['message'][:200]}...")  # 只显示前200字符

    # 测试风格选择
    print("\n【5. 测试风格选择】")
    response = await agent.process_message("科技感", None)
    print(f"状态: {response['state']}")
    print(f"消息:\n{response['message'][:200]}...")

    # 测试意图确认
    print("\n【6. 测试意图确认】")
    response = await agent.process_message("确认", None)
    print(f"状态: {response['state']}")
    print(f"消息:\n{response['message']}")

    # 显示进度
    print("\n【7. 查看进度】")
    progress = agent.get_progress()
    print(f"进度: {progress['percentage']}%")
    print(f"当前步骤: {progress['current_step']}")
    print(f"预计剩余: {progress['eta']}")

    print("\n" + "=" * 60)
    print("✅ 核心功能测试完成")
    print("=" * 60)


async def test_vision_analyzer():
    """单独测试Vision分析器"""
    print("\n" + "=" * 60)
    print("Vision分析器独立测试")
    print("=" * 60)

    from vision_analyzer import VisionAnalyzer

    claude_key = os.getenv("CLAUDE_API_KEY")
    claude_base = os.getenv("CLAUDE_BASE_URL")

    if not claude_key:
        print("❌ 错误：未找到CLAUDE_API_KEY")
        return

    # 创建分析器
    print("\n【1. 初始化Vision分析器】")
    analyzer = VisionAnalyzer(claude_key, claude_base)
    print("✅ 分析器初始化成功")

    # 测试连接
    print("\n【2. 测试API连接】")
    if analyzer.test_connection():
        print("✅ API连接正常")
    else:
        print("❌ API连接失败")
        return

    # 测试图片分析
    test_image = "74f8c6f71010b7553325446bec13f5a5.jpg"

    if not Path(test_image).exists():
        print(f"⚠️ 测试图片不存在: {test_image}")
        return

    print(f"\n【3. 分析图片】: {test_image}")
    result = analyzer.analyze_image(test_image)

    print("\n提取的产品信息:")
    print(f"  产品名称: {result.get('product_name', 'N/A')}")
    print(f"  品牌: {result.get('brand', 'N/A')}")
    print(f"  核心卖点: {result.get('slogan', 'N/A')}")
    print(f"  产品类型: {result.get('product_type', 'N/A')}")
    print(f"  特点数量: {len(result.get('features', []))}")
    print(f"  适用场景: {', '.join(result.get('scenes', []))}")
    print(f"  主要颜色: {', '.join(result.get('colors', []))}")

    # 生成主动提问
    print("\n【4. 生成主动提问】")
    questions = analyzer.generate_questions(result)
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")

    print("\n✅ Vision分析器测试完成")


async def test_progress_tracker():
    """测试进度跟踪器"""
    print("\n" + "=" * 60)
    print("进度跟踪器测试")
    print("=" * 60)

    from progress_tracker import ProgressTracker, TaskStep
    import time

    tracker = ProgressTracker()
    tracker.start_task()

    print("\n模拟任务执行:")
    for step in TaskStep:
        tracker.start_step(step)
        print(f"\n  当前步骤: {step.value}")
        print(f"  进度: {tracker.get_progress_percentage()}%")
        print(f"  预计剩余: {tracker.get_eta()}")

        time.sleep(0.3)  # 模拟处理时间
        tracker.complete_step(step)

    print("\n最终摘要:")
    summary = tracker.get_progress_summary()
    print(f"  进度: {summary['percentage']}%")
    print(f"  步骤状态:")
    for step_info in summary['steps']:
        print(f"    {step_info['icon']} {step_info['name']}")

    print("\n✅ 进度跟踪器测试完成")


def main():
    """主测试函数"""
    import sys

    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "all"

    if test_type == "vision":
        asyncio.run(test_vision_analyzer())
    elif test_type == "progress":
        asyncio.run(test_progress_tracker())
    elif test_type == "agent":
        asyncio.run(test_agent_flow())
    else:
        # 运行所有测试
        asyncio.run(test_vision_analyzer())
        asyncio.run(test_progress_tracker())
        asyncio.run(test_agent_flow())


if __name__ == "__main__":
    main()
