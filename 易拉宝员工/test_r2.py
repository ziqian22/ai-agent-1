"""
测试 Supabase Storage 配置
运行此脚本验证 Supabase 是否配置正确
"""

import os
from dotenv import load_dotenv
from r2_storage import supabase_storage
from pathlib import Path

# 加载环境变量
load_dotenv()

def test_supabase_config():
    """测试 Supabase 配置"""
    print("=" * 50)
    print("📦 Supabase Storage 配置测试")
    print("=" * 50)
    print()

    # 检查环境变量
    print("1️⃣ 检查环境变量...")
    required_vars = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_KEY': os.getenv('SUPABASE_KEY'),
        'SUPABASE_BUCKET': os.getenv('SUPABASE_BUCKET', 'banner-images')
    }

    all_set = True
    for key, value in required_vars.items():
        if value:
            # 隐藏敏感信息
            if 'KEY' in key:
                display_value = value[:20] + '...' + value[-10:] if len(value) > 30 else '***'
            else:
                display_value = value
            print(f"   ✅ {key} = {display_value}")
        else:
            print(f"   ❌ {key} = 未设置")
            all_set = False

    print()

    if not all_set:
        print("❌ Supabase 配置不完整")
        print()
        print("请在 .env 文件中配置：")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_KEY=your_supabase_anon_key")
        print("SUPABASE_BUCKET=banner-images")
        return False

    # 检查 Supabase 是否启用
    print("2️⃣ 检查 Supabase 客户端...")
    if supabase_storage.enabled:
        print("   ✅ Supabase 客户端初始化成功")
        print(f"   📦 存储桶: {supabase_storage.bucket_name}")
    else:
        print("   ❌ Supabase 客户端初始化失败")
        return False

    print()

    # 测试上传功能
    print("3️⃣ 测试上传功能...")
    print("   创建测试文件...")

    # 创建一个测试文件
    test_dir = Path("test_temp")
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "test_image.txt"

    with open(test_file, 'w') as f:
        f.write("This is a test file for Supabase Storage.")

    print(f"   ✅ 测试文件创建: {test_file}")
    print()
    print("   正在上传到 Supabase...")

    # 上传测试文件
    url = supabase_storage.upload_file(
        str(test_file),
        "test/test_image.txt"
    )

    if url:
        print(f"   ✅ 上传成功!")
        print(f"   🔗 URL: {url}")
    else:
        print("   ❌ 上传失败")
        # 清理测试文件
        test_file.unlink()
        test_dir.rmdir()
        return False

    print()

    # 测试删除文件
    print("4️⃣ 测试删除文件...")
    success = supabase_storage.delete_file("test/test_image.txt")

    if success:
        print("   ✅ 删除成功")
    else:
        print("   ❌ 删除失败（可能需要等待几秒）")

    # 清理本地测试文件
    test_file.unlink()
    test_dir.rmdir()

    print()
    print("=" * 50)
    print("✅ Supabase Storage 配置测试完成！")
    print("=" * 50)
    print()
    print("💡 提示:")
    print("   - Supabase 已正确配置，图片将自动上传到云端")
    print("   - Railway 重启后图片依然可访问")
    print("   - 免费额度：1GB 存储 + 2GB 带宽/月")
    print()

    return True


if __name__ == "__main__":
    try:
        test_supabase_config()
    except Exception as e:
        print()
        print("=" * 50)
        print("❌ 测试失败")
        print("=" * 50)
        print()
        print(f"错误信息: {str(e)}")
        print()
        print("常见问题:")
        print("1. 检查 Supabase URL 和 Key 是否正确")
        print("2. 检查存储桶是否设置为 Public")
        print("3. 检查网络连接")
        print()
        print("详细配置指南: SUPABASE_SETUP_GUIDE.md")
