"""
验证修改后的多风格生成逻辑
"""

import sys
import io
from pathlib import Path

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent))

from banner_prompt_template import generate_banner_prompt
from conversation_state import get_style_preset

def test_multi_style_with_variants():
    """测试多风格生成时的提示词变体"""

    print("=" * 80)
    print("测试多风格生成的提示词变体逻辑")
    print("=" * 80)

    # 测试产品信息
    product_info = {
        "product_name": "测试产品",
        "brand": "测试品牌",
        "slogan": "测试口号",
        "features": ["特点1", "特点2", "特点3", "特点4"],
        "scenes": ["场景1", "场景2"]
    }

    # 模拟用户选择3个风格
    selected_styles = ["科技感", "简约商务", "自然清新"]

    # 模拟生成提示词
    prompts_with_styles = []
    count_per_style = 1  # 每种风格1张

    for style_name in selected_styles:
        style_config = get_style_preset(style_name)
        if not style_config:
            continue

        prompt_data = {
            **product_info,
            "style": style_config.get("atmosphere", "专业、现代"),
            "main_colors": style_config.get("colors", "蓝色+白色")
        }

        prompt = generate_banner_prompt(prompt_data, style_config)
        prompts_with_styles.append((prompt, style_name, count_per_style))

    # 模拟 parallel_generator 的逻辑
    all_tasks = []
    task_index = 0

    for prompt, style_name, count in prompts_with_styles:
        for i in range(count):
            # 新逻辑：添加变体标识
            if count > 1:
                variant_prompt = prompt + f"\n\n设计变体{i+1}: 在保持{style_name}风格的基础上，探索不同的布局细节、色彩搭配和艺术元素设计。"
            else:
                variant_prompt = prompt + f"\n\n重要提示: 请严格按照{style_name}风格的特征进行设计，确保风格特色鲜明。"

            all_tasks.append((variant_prompt, style_name, task_index))
            task_index += 1

    print(f"\n总任务数: {len(all_tasks)}")
    print(f"{'='*80}\n")

    # 显示每个任务的提示词末尾
    for idx, (prompt, style_name, task_idx) in enumerate(all_tasks):
        print(f"任务 {idx + 1}: {style_name}")
        print(f"提示词长度: {len(prompt)} 字符")
        print(f"提示词末尾（最后200字符）:")
        print("-" * 80)
        print(prompt[-200:])
        print("-" * 80)
        print()

    # 验证提示词是否不同
    print(f"{'='*80}")
    print("验证提示词差异")
    print(f"{'='*80}\n")

    if len(all_tasks) >= 2:
        prompt1 = all_tasks[0][0]
        prompt2 = all_tasks[1][0]

        if prompt1 == prompt2:
            print("❌ 警告：前两个提示词完全相同！")
        else:
            print("✅ 提示词不同")

            # 检查是否包含风格强调
            if "请严格按照" in prompt1:
                print("✅ 包含风格强调语句")
            if "请严格按照" in prompt2:
                print("✅ 包含风格强调语句")

    print(f"\n{'='*80}")
    print("测试完成")
    print(f"{'='*80}")


if __name__ == "__main__":
    test_multi_style_with_variants()
