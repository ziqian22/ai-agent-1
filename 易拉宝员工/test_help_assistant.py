"""
测试页面使用精灵助手 API
"""

import httpx
import json

# API 配置
BASE_URL = "http://localhost:8000"
HELP_CHAT_URL = f"{BASE_URL}/api/help/chat"

def test_help_chat():
    """测试帮助助手对话接口"""

    # 测试问题列表
    test_questions = [
        "你好，请介绍一下这个系统的功能",
        "如何上传产品图片？",
        "支持哪些设计风格？",
        "可以批量上传产品吗？",
        "生成需要多长时间？",
        "知识库有什么用？",
        "可以导出 PSD 文件吗？"
    ]

    history = []

    print("=" * 60)
    print("页面使用精灵助手 API 测试")
    print("=" * 60)
    print()

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}/{len(test_questions)}")
        print(f"{'='*60}")
        print(f"👤 用户: {question}")
        print()

        try:
            # 发送请求
            response = httpx.post(
                HELP_CHAT_URL,
                json={
                    "message": question,
                    "history": history
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")

                print(f"🧚‍♀️ 助手: {reply}")
                print()
                print(f"✅ 状态: 成功")
                print(f"📊 响应时间: {response.elapsed.total_seconds():.2f}秒")

                # 更新对话历史
                history.append({"role": "user", "content": question})
                history.append({"role": "assistant", "content": reply})

                # 只保留最近10条消息
                if len(history) > 10:
                    history = history[-10:]

            else:
                print(f"❌ 错误: HTTP {response.status_code}")
                print(f"📄 详情: {response.text}")

        except httpx.ConnectError:
            print("❌ 错误: 无法连接到服务器")
            print("💡 提示: 请确保后端服务已启动 (python -m uvicorn main:app --reload)")
            break

        except httpx.TimeoutException:
            print("❌ 错误: 请求超时")

        except Exception as e:
            print(f"❌ 错误: {str(e)}")

    print()
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)


def test_api_health():
    """测试 API 健康状态"""
    print("\n检查 API 健康状态...")

    try:
        response = httpx.get(f"{BASE_URL}/", timeout=5.0)
        if response.status_code == 200:
            print("✅ 后端 API 运行正常")
            print(f"📄 响应: {response.json()}")
            return True
        else:
            print(f"⚠️ 后端 API 状态异常: HTTP {response.status_code}")
            return False
    except httpx.ConnectError:
        print("❌ 无法连接到后端 API")
        print("💡 请先启动后端服务:")
        print("   cd backend")
        print("   python -m uvicorn main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║      页面使用精灵助手 - API 测试工具                    ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # 先检查 API 健康状态
    if test_api_health():
        print()
        input("按 Enter 键开始测试对话功能...")
        test_help_chat()
    else:
        print("\n⚠️ 后端服务未就绪，测试终止")
