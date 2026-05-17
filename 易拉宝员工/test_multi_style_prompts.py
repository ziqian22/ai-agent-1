"""
验证多风格生成时，每个风格的提示词是否真的不同
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

def test_multi_style_prompts():
    """测试多风格提示词是否不同"""

    print("=" * 80)
    print("测试多风格提示词差异")
    print("=" * 80)

    # 测试产品信息
    product_info = {
        "product_name": "勇士K6/K9即开直饮机",
        "brand": "朴道健康水专家",
        "slogan": "澎湃开水持续出 绿色节能新选择",
        "features": ["高达125L/H开水量", "100℃开水持续出", "4重深度净化", "纳米单晶磨石釉内胆"],
        "scenes": ["商务办公", "政府机关", "医院病房"]
    }

    # 模拟用户选择3个风格
    selected_styles = ["科技感", "简约商务", "自然清新"]

    prompts_with_styles = []

    for style_name in selected_styles:
        style_config = get_style_preset(style_name)
        if not style_config:
            continue

        prompt_data = {
            **product_info,
            "style": style_config.get("atmosphere", "专业、现代"),
            "main_colors": style_config.get("colors", "蓝色+白色")
        }

        # 生成提示词
        prompt = generate_banner_prompt(prompt_data, style_config)
        prompts_with_styles.append((prompt, style_name, 1))

        print(f"\n{'='*80}")
        print(f"风格: {style_name}")
        print(f"{'='*80}")
        print(f"提示词长度: {len(prompt)} 字符")
        print(f"\n关键差异点:")

        # 检查背景描述
        if "现代科技办公空间" in prompt:
            print("  [场景] 现代科技办公空间")
        elif "高端商务办公室" in prompt:
            print("  [场景] 高端商务办公室")
        elif "自然采光空间" in prompt:
            print("  [场景] 自然采光空间")

        # 检查光线描述
        if "明亮的LED灯光" in prompt:
            print("  [光线] 明亮的LED灯光")
        elif "柔和自然光,45度角斜射" in prompt:
            print("  [光线] 柔和自然光,45度角斜射")
        elif "温暖自然光,柔和漫射" in prompt:
            print("  [光线] 温暖自然光,柔和漫射")

        # 检查色彩描述
        if "浅蓝色+白色+浅灰色" in prompt:
            print("  [色彩] 浅蓝色+白色+浅灰色")
        elif "黑白灰+品牌色" in prompt:
            print("  [色彩] 黑白灰+品牌色")
        elif "绿色+白色+原木色" in prompt:
            print("  [色彩] 绿色+白色+原木色")

        # 显示背景设计部分
        if "【背景设计" in prompt:
            start = prompt.find("【背景设计")
            end = prompt.find("【顶部区域")
            background_section = prompt[start:end]
            print(f"\n背景设计部分（前300字符）:")
            print("-" * 80)
            print(background_section[:300] + "...")
            print("-" * 80)

    # 比较提示词是否相同
    print(f"\n{'='*80}")
    print("提示词对比")
    print(f"{'='*80}")

    if len(prompts_with_styles) >= 2:
        prompt1 = prompts_with_styles[0][0]
        prompt2 = prompts_with_styles[1][0]

        if prompt1 == prompt2:
            print("❌ 警告：前两个提示词完全相同！")
        else:
            print("✅ 提示词不同")

            # 计算差异字符数
            diff_chars = sum(1 for a, b in zip(prompt1, prompt2) if a != b)
            print(f"   差异字符数: {diff_chars}")
            print(f"   差异百分比: {diff_chars / len(prompt1) * 100:.2f}%")

    print(f"\n{'='*80}")
    print("测试完成")
    print(f"{'='*80}")


if __name__ == "__main__":
    test_multi_style_prompts()
