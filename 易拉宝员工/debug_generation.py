"""
调试生成失败问题的工具
"""

import asyncio
import os
from dotenv import load_dotenv
from banner_generator import BannerGenerator
from banner_prompt_template import generate_banner_prompt
from pathlib import Path

load_dotenv()

async def test_generation():
    """测试生成流程"""

    # 获取 API 密钥
    api_key = os.getenv("RUNNINGHUB_API_KEY")
    if not api_key:
        print("[ERROR] 错误: 未找到 RUNNINGHUB_API_KEY")
        return

    print(f"[OK] API Key: {api_key[:10]}...")

    # 创建生成器
    generator = BannerGenerator(api_key)

    # 测试产品图片路径
    test_image = r"C:\Users\suizi\Desktop\易拉宝员工\朴道logo\PUDOW朴道健康水专家-原色.png"

    if not Path(test_image).exists():
        print(f"[ERROR] 测试图片不存在: {test_image}")
        print("请提供一个存在的产品图片路径")
        return

    print(f"[OK] 测试图片: {test_image}")

    # 进度回调
    def progress(msg):
        print(f"[进度] {msg}")

    # 测试步骤1: 上传图片
    print("\n=== 步骤1: 测试上传图片 ===")
    upload_result = generator.upload_image(test_image)

    if not upload_result:
        print("[ERROR] 上传失败")
        return

    file_name, download_url = upload_result
    print(f"[OK] 上传成功")
    print(f"   文件名: {file_name}")
    print(f"   下载URL: {download_url}")

    # 测试步骤2: 生成易拉宝
    print("\n=== 步骤2: 测试生成易拉宝 ===")

    # 简单的测试提示词
    test_prompt = """
设计一张易拉宝海报，要求：
- 产品：健康水
- 品牌：朴道
- 风格：简约、清新
- 主色调：蓝色+白色
- 尺寸：80x200cm (9:21比例)
"""

    task_id = generator.generate_banner(
        image_url=download_url,
        prompt=test_prompt,
        aspect_ratio="9:21",
        resolution="2k",
        progress_callback=progress
    )

    if not task_id:
        print("[ERROR] 提交生成任务失败")
        return

    print(f"[OK] 任务已提交: {task_id}")

    # 测试步骤3: 等待完成
    print("\n=== 步骤3: 等待生成完成 ===")

    result = generator._wait_for_completion(
        task_id,
        task_name="测试生成",
        progress_callback=progress
    )

    if not result:
        print("[ERROR] 任务超时或失败")
        return

    status = result.get('status')
    print(f"\n任务状态: {status}")

    if status == 'SUCCESS':
        print("[OK] 生成成功！")

        # 下载结果
        print("\n=== 步骤4: 下载结果 ===")
        result_files = generator.download_results(result, progress)

        if result_files:
            print(f"[OK] 下载成功，共 {len(result_files)} 个文件:")
            for f in result_files:
                print(f"   - {f}")
        else:
            print("[ERROR] 下载失败")

    elif status == 'FAILED':
        error_msg = result.get('errorMessage', '未知错误')
        print(f"[ERROR] 生成失败: {error_msg}")
        print(f"\n完整结果:")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"[WARNING] 未知状态: {status}")
        print(f"\n完整结果:")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    print("=" * 60)
    print("易拉宝生成调试工具")
    print("=" * 60)

    asyncio.run(test_generation())
