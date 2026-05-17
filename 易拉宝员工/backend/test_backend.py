"""
测试脚本 - 验证后端 API 是否正常工作
"""

import sys
import os

# 设置 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_imports():
    """测试所有必要的模块是否可以导入"""
    print("测试模块导入...")

    try:
        from backend.main import app
        print("✓ backend.main 导入成功")
    except Exception as e:
        print(f"✗ backend.main 导入失败: {e}")
        return False

    try:
        from vision_analyzer import VisionAnalyzer
        print("✓ vision_analyzer 导入成功")
    except Exception as e:
        print(f"✗ vision_analyzer 导入失败: {e}")
        return False

    try:
        from banner_generator import BannerGenerator
        print("✓ banner_generator 导入成功")
    except Exception as e:
        print(f"✗ banner_generator 导入失败: {e}")
        return False

    try:
        from banner_prompt_template import generate_banner_prompt
        print("✓ banner_prompt_template 导入成功")
    except Exception as e:
        print(f"✗ banner_prompt_template 导入失败: {e}")
        return False

    return True

def test_env():
    """测试环境变量是否配置"""
    print("\n测试环境变量...")

    from dotenv import load_dotenv
    load_dotenv()

    required_vars = ['CLAUDE_API_KEY', 'RUNNINGHUB_API_KEY']
    all_ok = True

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var} 已配置")
        else:
            print(f"✗ {var} 未配置")
            all_ok = False

    return all_ok

def main():
    print("=" * 50)
    print("易拉宝AI设计助手 - 后端测试")
    print("=" * 50)

    # 测试导入
    if not test_imports():
        print("\n❌ 模块导入测试失败")
        return False

    # 测试环境变量
    if not test_env():
        print("\n⚠️  环境变量未完全配置，请检查 .env 文件")
        print("需要配置:")
        print("  - CLAUDE_API_KEY")
        print("  - RUNNINGHUB_API_KEY")
        return False

    print("\n" + "=" * 50)
    print("✅ 所有测试通过!")
    print("=" * 50)
    print("\n可以启动服务了:")
    print("  Windows: start.bat")
    print("  Linux/Mac: ./start.sh")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
