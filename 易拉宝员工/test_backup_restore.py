"""
测试 Supabase 备份和恢复功能
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def test_backup_restore():
    """测试备份和恢复功能"""

    print("=" * 70)
    print("Supabase 备份和恢复功能测试")
    print("=" * 70)

    # 1. 检查 Supabase 配置
    print("\n1. 检查 Supabase 配置...")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    supabase_bucket = os.getenv('SUPABASE_BUCKET', 'banner-images')

    if supabase_url and supabase_key:
        print(f"   [OK] SUPABASE_URL: {supabase_url}")
        print(f"   [OK] SUPABASE_KEY: {supabase_key[:10]}...")
        print(f"   [OK] SUPABASE_BUCKET: {supabase_bucket}")
    else:
        print("   [ERROR] Supabase 配置不完整")
        return

    # 2. 测试导入 KnowledgeBase
    print("\n2. 测试导入 KnowledgeBase...")
    try:
        from knowledge_base import KnowledgeBase
        print("   [OK] KnowledgeBase 导入成功")
    except Exception as e:
        print(f"   [ERROR] 导入失败: {str(e)}")
        return

    # 3. 初始化 KnowledgeBase
    print("\n3. 初始化 KnowledgeBase...")
    try:
        kb = KnowledgeBase()
        print("   [OK] 初始化成功")
        print(f"   当前产品数量: {len(kb.products)}")
    except Exception as e:
        print(f"   [ERROR] 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # 4. 测试备份功能
    print("\n4. 测试手动备份...")
    try:
        kb.backup_to_supabase()
        print("   [OK] 手动备份完成")
    except Exception as e:
        print(f"   [ERROR] 备份失败: {str(e)}")
        import traceback
        traceback.print_exc()

    # 5. 测试恢复功能
    print("\n5. 测试恢复功能...")
    print("   提示: 如果本地已有数据，会跳过恢复")
    print("   要测试恢复，请先删除 knowledge_base/products.json")

    # 6. 验证文件是否存在
    print("\n6. 验证本地文件...")
    products_file = Path("knowledge_base/products.json")
    if products_file.exists():
        print(f"   [OK] products.json 存在")
        print(f"   文件大小: {products_file.stat().st_size} bytes")
    else:
        print("   [WARN] products.json 不存在")

    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)

    print("\n功能说明:")
    print("  • 启动时自动从 Supabase 恢复数据（如果本地没有）")
    print("  • 每次添加/修改产品时自动备份到 Supabase")
    print("  • Railway 重启后会自动恢复最新数据")
    print("  • 备份路径: backups/products.json")


if __name__ == "__main__":
    test_backup_restore()
