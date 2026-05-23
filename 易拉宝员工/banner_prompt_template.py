"""
易拉宝提示词生成模板
用于根据产品信息动态生成易拉宝设计提示词
"""

import re
from typing import List, Tuple, Dict


def categorize_features(features: List[str]) -> Tuple[List[str], List[str]]:
    """
    将特点分为重点特点和普通特点

    Args:
        features: 产品特点列表

    Returns:
        (重点特点列表, 普通特点列表)
    """
    if len(features) <= 4:
        return features, []

    # 重点特点：前4个
    highlight_features = features[:4]

    # 普通特点：剩余的
    regular_features = features[4:]

    return highlight_features, regular_features


def extract_technical_params(features: List[str]) -> Dict[str, str]:
    """
    从产品特点中提取技术参数

    识别包含数值的特点作为技术参数

    Args:
        features: 产品特点列表

    Returns:
        技术参数字典 {"参数名": "参数值"}
    """
    params = {}

    # 常见参数关键词
    param_keywords = [
        '功率', '容量', '温度', '尺寸', '重量', '时间', '速度',
        '压力', '电压', '电流', '频率', '流量', '高度', '宽度',
        '长度', '厚度', '直径', '面积', '体积', '能效', '噪音'
    ]

    for feature in features:
        # 检查是否包含数字
        if re.search(r'\d', feature):
            # 尝试提取参数名和值
            for keyword in param_keywords:
                if keyword in feature:
                    # 提取参数值（包含数字的部分）
                    match = re.search(r'[\d.]+\s*[A-Za-z/%°℃]+', feature)
                    if match:
                        params[keyword] = match.group()
                    break

            # 如果没有匹配到关键词，但包含冒号或等号，也尝试提取
            if ':' in feature or '：' in feature:
                parts = re.split(r'[:：]', feature, 1)
                if len(parts) == 2:
                    param_name = parts[0].strip()
                    param_value = parts[1].strip()
                    if re.search(r'\d', param_value):
                        params[param_name] = param_value

    return params


def generate_background_description(style_config):
    """
    根据选择的风格生成背景描述

    - 如果是"具体场景风格"：使用真实场景描述
    - 其他风格：简约质感 + 产品关联元素

    Args:
        style_config: 风格配置字典，包含 scene, lighting, colors, atmosphere

    Returns:
        str: 背景描述文本
    """
    colors = style_config.get('colors', '浅蓝色+白色')
    atmosphere = style_config.get('atmosphere', '专业、清爽')

    # 检查是否是具体场景风格
    if style_config.get('is_scene_style', False):
        scene = style_config.get('scene', '现代简约空间')
        lighting = style_config.get('lighting', '柔和自然光')

        return f"""- 背景设计（真实场景）:
  * 场景: {scene}
  * 光线: {lighting}
  * 色彩: {colors}
  * 氛围: {atmosphere}
  * 要求:
    - 使用写实风格的真实场景照片作为背景
    - 场景要虚化处理，明度比前景低20-30%
    - 确保产品和文字清晰可见，背景不抢主体
    - 营造真实的使用环境氛围"""

    # 其他风格：简约质感 + 产品关联
    return f"""- 背景设计（简约质感）:
  * 氛围: {atmosphere}
  * 色彩: {colors}
  * 要求:
    - 简约克制，有质感但不抢主体
    - 可以是纯色渐变、柔和光影、或简单几何元素
    - 可选择性融入产品相关元素（如水元素、材质质感等），但要有呼吸感，不要过度堆砌
    - 避免过多装饰和复杂细节
    - 虚化处理，明度比前景低20-30%，确保文字和产品清晰"""


def generate_banner_prompt(product_info, style_config=None):
    """
    根据产品信息生成易拉宝设计提示词（专为净水产品设计）

    参数:
        product_info (dict): 产品信息字典
            - product_name: 产品名称
            - brand: 品牌名称
            - slogan: 核心卖点/口号
            - features: 产品特点列表 (list)
            - scenes: 适用场景列表 (list)
            - style: 设计风格描述（如果没有style_config）
            - main_colors: 主色调（如果没有style_config）
        style_config (dict): 风格配置字典（可选）
            - scene: 场景描述
            - lighting: 光线描述
            - colors: 颜色描述
            - atmosphere: 氛围描述

    返回:
        str: 完整的易拉宝设计提示词
    """

    # 提取产品信息
    product_name = product_info.get('product_name', '')
    brand = product_info.get('brand', '')
    slogan = product_info.get('slogan', '')
    features = product_info.get('features', [])
    scenes = product_info.get('scenes', [])

    # 如果提供了style_config，使用它；否则使用product_info中的style和main_colors
    if style_config:
        style = style_config.get('atmosphere', '专业、健康、环保、科技感')
        main_colors = style_config.get('colors', '浅蓝色+白色+浅灰色')
        background_desc = generate_background_description(style_config)
    else:
        style = product_info.get('style', '专业、健康、环保、科技感')
        main_colors = product_info.get('main_colors', '浅蓝色+白色+浅灰色')
        # 创建默认的style_config
        default_style_config = {
            'scene': '现代简约空间',
            'lighting': '柔和自然光',
            'colors': main_colors,
            'atmosphere': style
        }
        background_desc = generate_background_description(default_style_config)

    # 特点分级
    highlight_features, regular_features = categorize_features(features)

    # 提取技术参数
    technical_params = extract_technical_params(features)

    # 格式化重点特点
    highlight_text = '\n'.join([f"  {i+1}. {feature}" for i, feature in enumerate(highlight_features)])

    # 格式化普通特点（每行4个）
    regular_features_rows = []
    for i in range(0, len(regular_features), 4):
        row = regular_features[i:i+4]
        regular_features_rows.append(row)

    regular_features_text = ""
    for row in regular_features_rows:
        regular_features_text += "- " + " | ".join(row) + "\n"

    # 格式化场景列表
    scenes_text = '、'.join(scenes)

    # 格式化技术参数
    technical_params_text = ""
    if technical_params:
        technical_params_text = "\n技术参数:\n"
        for param_name, param_value in technical_params.items():
            technical_params_text += f"- {param_name}: {param_value}\n"

    # 生成完整提示词
    prompt = f"""设计一张专业的商业易拉宝海报，尺寸接近80x200cm的竖版比例。

产品: {product_name}
品牌: {brand}

设计要求:

【背景设计 - 贯穿整个画面】
{background_desc}

【顶部区域】
内容:
- 产品名称: "{product_name}"（重点）
- 核心卖点: "{slogan}"（重点）

要求:
- 产品名称和核心卖点同等重要，都要醒目突出
- 用同色系不同颜色区分两者（如深蓝+浅蓝，或蓝+青）
- 核心卖点可以使用艺术字体或特殊排版，增加设计感
- 两者不需要对齐，可以错开排列，留有呼吸感
- 避免所有元素都对齐，打破对称增加设计感

【中部区域 - 视觉焦点】
内容:
- 产品图片作为主体
- 4个核心特点:
{highlight_text}

要求:
- 产品图要清晰锐利，作为视觉中心
- 4个核心特点要醒目突出，与产品形成视觉关联
- 设计要专业、有层次感，但不要过于花哨
- 整体布局要有呼吸感，不要过于拥挤

【底部区域】

1. 其他产品特点:
{regular_features_text}
要求: 简洁清晰，图标+文字，作为补充信息。**重要：必须显示所有特点，不要遗漏任何一条。**

2. 适用场景展示:
{len(scenes)}个场景: {scenes_text}
要求:
- 使用写实风格的场景照片+文字标注
- 展示真实使用环境（办公室、医院、学校等）
- 避免插画、卡通风格
- 照片要有景深效果，色彩自然真实

3. 技术参数:
{technical_params_text if technical_params_text else "如有技术参数，以简洁形式展示"}
要求: 可以使用表格、图表等形式，保持专业美观

【整体风格】
- 风格定位: {style}
- 主色调: {main_colors}
- 设计原则:
  * 布局清晰、层次分明
  * 信息有主次，重点突出
  * 整体协调统一，有设计感和现代感
  * 避免过于呆板和单调

【印刷要求】
- 左右两侧不需要出血线，内容可以延伸到边缘
- 上下各预留1cm出血线，重要内容不要放在上下边缘1cm区域内
- 符合印刷标准，确保可直接用于80cm×200cm尺寸印刷制作
- 输出比例使用9:21(竖版易拉宝)

注意: 产品图中不包含Logo，Logo将后期添加，请不要在设计中预留Logo位置。"""

    return prompt.strip()


# ========== 产品信息模板示例 ==========

# 示例1: 勇士K6/K9直饮机
PRODUCT_EXAMPLE_1 = {
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
    "scenes": ["商务办公", "政府机关", "医院病房", "居委院校", "高铁机场"],
    "style": "专业、健康、环保、科技感",
    "main_colors": "蓝色+白色+灰色,体现健康水的清洁感"
}

# 示例2: 空白模板(复制此模板填写新产品)
PRODUCT_TEMPLATE = {
    "product_name": "产品名称",
    "brand": "品牌名称",
    "slogan": "核心卖点或口号",
    "features": [
        "特点1",
        "特点2",
        "特点3",
        "特点4",
        "特点5",
        "特点6"
    ],
    "scenes": ["场景1", "场景2", "场景3", "场景4", "场景5"],
    "style": "专业、健康、环保、科技感",  # 或: 简约商务/自然清新/时尚活力
    "main_colors": "主色调描述"
}


if __name__ == "__main__":
    # 测试生成提示词
    print("=" * 60)
    print("易拉宝提示词生成测试")
    print("=" * 60)

    prompt = generate_banner_prompt(PRODUCT_EXAMPLE_1)
    print(prompt)

    print("\n" + "=" * 60)
    print(f"提示词长度: {len(prompt)} 字符")
    print("=" * 60)
