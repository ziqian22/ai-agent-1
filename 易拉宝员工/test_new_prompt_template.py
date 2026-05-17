"""
测试新的提示词模板
验证三个修改：
1. 四个特点统一规则的几何形状
2. 适用场景使用写实风格
3. 背景根据风格配置生成（专为净水产品）
"""

from banner_prompt_template import generate_banner_prompt
from conversation_state import STYLE_PRESETS, get_style_preset


def test_prompt_generation():
    """测试提示词生成"""

    # 测试产品信息
    product_info = {
        "product_name": "勇士K6/K9即开直饮机",
        "brand": "朴道健康水专家",
        "slogan": "澎湃开水持续出 绿色节能新选择",
        "features": [
            "高达125L/H开水量",
            "100℃开水持续出",
            "4重深度净化",
            "纳米单晶磨石釉内胆,无重金属加热",
            "无加热水箱设计,省滤水只烧滤1次",
            "LED紫外灯过滤式杀菌,24小时循环杀菌",
            "涉膜可视窗设计,加热沸腾过程全程可见",
            "接水高度≥38cm,适合市面大多数接水壶使用",
            "IOT智能云平台,全生命周期技术保障",
            "10重安全防护,蒸汽超温保护、滚烫保护等"
        ],
        "scenes": ["商务办公", "政府机关", "医院病房", "居委院校", "高铁机场"]
    }

    print("=" * 80)
    print("测试不同风格的提示词生成")
    print("=" * 80)

    # 测试所有预设风格
    for style_name, style_config in STYLE_PRESETS.items():
        print(f"\n{'='*80}")
        print(f"风格: {style_name}")
        print(f"{'='*80}")

        # 生成提示词
        prompt = generate_banner_prompt(product_info, style_config)

        # 检查关键修改点
        print("\n[检查] 检查修改点:")

        # 1. 检查四个特点的设计要求
        if "统一规则的几何形状" in prompt:
            print("  [OK] 四个特点使用统一规则的几何形状")
        else:
            print("  [FAIL] 未找到统一几何形状的要求")

        if "4个特点使用相同的形状和设计风格" in prompt:
            print("  [OK] 强调4个特点保持一致性")
        else:
            print("  [FAIL] 未找到一致性要求")

        # 2. 检查适用场景的风格
        if "写实风格的场景照片" in prompt:
            print("  [OK] 适用场景使用写实风格")
        else:
            print("  [FAIL] 未找到写实风格要求")

        if "插画" not in prompt or "避免插画" in prompt:
            print("  [OK] 已移除插画风格")
        else:
            print("  [FAIL] 仍然包含插画风格")

        # 3. 检查背景是否融合了风格配置
        if style_config['scene'] in prompt:
            print(f"  [OK] 背景融合了风格场景: {style_config['scene'][:30]}...")
        else:
            print("  [FAIL] 背景未融合风格场景")

        if style_config['lighting'] in prompt:
            print(f"  [OK] 背景融合了风格光线: {style_config['lighting'][:30]}...")
        else:
            print("  [FAIL] 背景未融合风格光线")

        if style_config['colors'] in prompt:
            print(f"  [OK] 背景融合了风格色彩: {style_config['colors']}")
        else:
            print("  [FAIL] 背景未融合风格色彩")

        # 4. 检查是否保留了水元素背景
        if "清澈水元素环境" in prompt:
            print("  [OK] 保留了净水产品的水元素背景")
        else:
            print("  [FAIL] 未找到水元素背景")

        print(f"\n提示词长度: {len(prompt)} 字符")

        # 显示提示词的关键部分
        print("\n[预览] 提示词预览（前500字符）:")
        print("-" * 80)
        print(prompt[:500] + "...")
        print("-" * 80)


def test_specific_sections():
    """测试特定部分的内容"""

    product_info = {
        "product_name": "测试产品",
        "brand": "测试品牌",
        "slogan": "测试口号",
        "features": ["特点1", "特点2", "特点3", "特点4", "特点5", "特点6"],
        "scenes": ["场景1", "场景2", "场景3"]
    }

    style_config = get_style_preset("科技感")
    prompt = generate_banner_prompt(product_info, style_config)

    print("\n" + "=" * 80)
    print("详细检查各个部分")
    print("=" * 80)

    # 提取中部区域部分
    if "【中部区域" in prompt:
        start = prompt.find("【中部区域")
        end = prompt.find("【底部区域")
        middle_section = prompt[start:end]

        print("\n[中部区域] 四个特点:")
        print("-" * 80)
        print(middle_section)
        print("-" * 80)

    # 提取底部区域部分
    if "【底部区域" in prompt:
        start = prompt.find("【底部区域")
        end = prompt.find("【整体风格】")
        bottom_section = prompt[start:end]

        print("\n[底部区域] 场景展示:")
        print("-" * 80)
        print(bottom_section)
        print("-" * 80)

    # 提取背景设计部分
    if "【背景设计" in prompt:
        start = prompt.find("【背景设计")
        end = prompt.find("【顶部区域")
        background_section = prompt[start:end]

        print("\n[背景设计]:")
        print("-" * 80)
        print(background_section)
        print("-" * 80)


if __name__ == "__main__":
    import sys
    import io

    # 设置输出编码为UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("\n[测试] 开始测试新的提示词模板\n")

    # 测试1: 所有风格
    test_prompt_generation()

    # 测试2: 详细检查
    test_specific_sections()

    print("\n" + "=" * 80)
    print("[完成] 测试完成")
    print("=" * 80)
