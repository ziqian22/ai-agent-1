"""
测试修改后的代码是否正常工作
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

def test_prompt_generation():
    """测试提示词生成是否正常"""

    print("=" * 80)
    print("测试修改后的代码")
    print("=" * 80)

    # 测试产品信息
    product_info = {
        "product_name": "测试产品",
        "brand": "测试品牌",
        "slogan": "测试口号",
        "features": ["特点1", "特点2", "特点3", "特点4"],
        "scenes": ["场景1", "场景2", "场景3"]
    }

    # 测试1: 不传入 style_config（使用默认）
    print("\n[测试1] 不传入 style_config")
    try:
        prompt1 = generate_banner_prompt(product_info)
        print(f"✅ 成功生成提示词 (长度: {len(prompt1)} 字符)")
        print(f"预览: {prompt1[:200]}...")
    except Exception as e:
        print(f"❌ 失败: {str(e)}")

    # 测试2: 传入 style_config（科技感）
    print("\n[测试2] 传入 style_config (科技感)")
    try:
        style_config = get_style_preset("科技感")
        if style_config:
            print(f"风格配置: {style_config}")
            prompt2 = generate_banner_prompt(product_info, style_config)
            print(f"✅ 成功生成提示词 (长度: {len(prompt2)} 字符)")

            # 检查是否包含风格特性
            if "现代科技办公空间" in prompt2:
                print("✅ 包含科技感场景")
            if "明亮的LED灯光" in prompt2:
                print("✅ 包含科技感光线")
            if "浅蓝色+白色+浅灰色" in prompt2:
                print("✅ 包含科技感色彩")
        else:
            print("❌ 无法获取风格配置")
    except Exception as e:
        print(f"❌ 失败: {str(e)}")

    # 测试3: 传入不存在的风格
    print("\n[测试3] 传入不存在的风格")
    try:
        style_config = get_style_preset("不存在的风格")
        if style_config is None:
            print("✅ 正确返回 None")
            # 使用 None 调用
            prompt3 = generate_banner_prompt(product_info, None)
            print(f"✅ 使用 None 也能正常生成 (长度: {len(prompt3)} 字符)")
        else:
            print("❌ 应该返回 None")
    except Exception as e:
        print(f"❌ 失败: {str(e)}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_prompt_generation()
