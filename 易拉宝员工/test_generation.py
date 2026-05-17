"""
测试完整生成流程
"""

import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')

from banner_generator import BannerGenerator
from banner_prompt_template import generate_banner_prompt
import os
from dotenv import load_dotenv

load_dotenv()

async def test_generation():
    print("=" * 60)
    print("测试完整生成流程")
    print("=" * 60)

    # 创建生成器
    api_key = os.getenv("RUNNINGHUB_API_KEY")
    generator = BannerGenerator(api_key)

    # 测试产品信息
    product_info = {
        "product_name": "立式饮水机",
        "brand": "浩泽OZNER",
        "slogan": "健康饮水专家",
        "features": [
            "三温设计",
            "智能控制",
            "净水过滤",
            "不锈钢出水台"
        ],
        "product_type": "饮水机",
        "scenes": ["办公室", "家庭", "公共场所"],
        "style": "专业、现代、科技感",
        "main_colors": "蓝色+白色+灰色"
    }

    # 生成提示词
    prompt = generate_banner_prompt(product_info)
    print("\n生成的提示词:")
    print(prompt[:200] + "...")

    # 进度回调
    def progress_callback(message):
        print(f"  → {message}")

    # 测试完整流程
    print("\n开始生成...")
    result = await generator.generate_complete_flow(
        product_image_path="74f8c6f71010b7553325446bec13f5a5.jpg",
        prompt=prompt,
        logo_path=None,
        enable_cutout=True,
        cutout_prompt="只保留饮水机",
        aspect_ratio="9:21",
        resolution="2k",
        progress_callback=progress_callback
    )

    print("\n" + "=" * 60)
    if result["success"]:
        print("✅ 生成成功！")
        print(f"任务ID: {result['task_id']}")
        print(f"生成文件数: {len(result['result_files'])}")
        for file_path in result['result_files']:
            print(f"  - {file_path}")
    else:
        print("❌ 生成失败")
        print(f"错误: {result['error']}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_generation())
