"""
测试文档分析功能
检查 PDF/Word/PPT 文件是否能正常解析
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from vision_analyzer import VisionAnalyzer

# 加载环境变量
load_dotenv()

def test_document_analysis():
    """测试文档分析功能"""

    # 初始化分析器
    api_key = os.getenv("CLAUDE_API_KEY")
    base_url = os.getenv("CLAUDE_BASE_URL")

    if not api_key:
        print("❌ 错误：未找到 CLAUDE_API_KEY 环境变量")
        return

    print("=" * 60)
    print("文档分析功能测试")
    print("=" * 60)
    print(f"API Key: {api_key[:10]}...")
    print(f"Base URL: {base_url}")
    print()

    # 创建分析器
    analyzer = VisionAnalyzer(api_key, base_url)

    # 测试连接
    print("1. 测试 API 连接...")
    if analyzer.test_connection():
        print("   [OK] API 连接正常")
    else:
        print("   [ERROR] API 连接失败")
        return

    print()

    # 检查可用的库
    print("2. 检查文档处理库...")
    try:
        import PyPDF2
        print("   [OK] PyPDF2 已安装")
    except ImportError:
        print("   [ERROR] PyPDF2 未安装 - PDF 解析不可用")

    try:
        from docx import Document
        print("   [OK] python-docx 已安装")
    except ImportError:
        print("   [ERROR] python-docx 未安装 - Word 解析不可用")

    try:
        from pptx import Presentation
        print("   [OK] python-pptx 已安装")
    except ImportError:
        print("   [ERROR] python-pptx 未安装 - PPT 解析不可用")

    print()

    # 查找测试文件
    print("3. 查找测试文件...")
    test_files = []

    # 在 temp_uploads 目录查找文档
    upload_dir = Path("temp_uploads")
    if upload_dir.exists():
        for ext in ['.pdf', '.docx', '.doc', '.pptx', '.ppt']:
            files = list(upload_dir.glob(f"*{ext}"))
            test_files.extend(files)

    if not test_files:
        print("   [WARN] 未找到测试文档文件")
        print("   提示：请将 PDF/Word/PPT 文件放到 temp_uploads 目录")
        return

    print(f"   找到 {len(test_files)} 个测试文件：")
    for f in test_files[:5]:  # 最多显示5个
        print(f"   - {f.name}")

    print()

    # 测试第一个文件
    test_file = test_files[0]
    print(f"4. 测试文档分析: {test_file.name}")
    print(f"   文件类型: {test_file.suffix}")
    print(f"   文件大小: {test_file.stat().st_size / 1024:.1f} KB")
    print()

    try:
        # 调用文档分析
        print("   开始分析...")
        result = analyzer.analyze_document(str(test_file))

        product_info = result.get('product_info', {})
        extracted_images = result.get('images', [])

        print("   [OK] 分析完成！")
        print()

        # 显示结果
        print("5. 分析结果：")
        print(f"   产品名称: {product_info.get('product_name', '未识别')}")
        print(f"   品牌: {product_info.get('brand', '未识别')}")
        print(f"   核心卖点: {product_info.get('slogan', '未识别')}")
        print(f"   产品类型: {product_info.get('product_type', '未识别')}")

        features = product_info.get('features', [])
        print(f"   产品特点数量: {len(features)}")
        if features:
            print("   特点列表:")
            for i, feature in enumerate(features[:10], 1):  # 显示前10个
                print(f"     {i}. {feature}")
            if len(features) > 10:
                print(f"     ... 还有 {len(features) - 10} 个特点")

        scenes = product_info.get('scenes', [])
        print(f"   适用场景: {', '.join(scenes) if scenes else '未识别'}")

        colors = product_info.get('colors', [])
        print(f"   主要颜色: {', '.join(colors) if colors else '未识别'}")

        print(f"   提取的图片数量: {len(extracted_images)}")
        if extracted_images:
            print("   图片列表:")
            for i, img in enumerate(extracted_images[:5], 1):
                print(f"     {i}. {img}")

        # 检查错误
        if 'error' in product_info:
            print(f"   [WARN] 错误信息: {product_info['error']}")

        print()
        print("=" * 60)
        print("测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"   [ERROR] 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_document_analysis()
