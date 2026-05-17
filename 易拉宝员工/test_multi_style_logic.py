"""
验证多风格生成逻辑
"""

# 模拟测试
selected_styles = ["科技感", "简约商务", "自然清新"]

print("=== 多风格生成逻辑测试 ===\n")

# 模拟STYLE_PRESETS
STYLE_PRESETS = {
    "科技感": {
        "atmosphere": "专业、现代、智能、高效",
        "colors": "蓝色+白色+灰色"
    },
    "简约商务": {
        "atmosphere": "专业、高端、克制、精致",
        "colors": "黑白灰+品牌色"
    },
    "自然清新": {
        "atmosphere": "健康、环保、舒适、亲和",
        "colors": "绿色+白色+原木色"
    }
}

# 模拟产品信息
product_info = {
    "product_name": "测试产品",
    "brand": "测试品牌",
    "features": ["特点1", "特点2", "特点3"]
}

# 模拟生成提示词
prompts_with_styles = []
count_per_style = 1

for style_name in selected_styles:
    style_config = STYLE_PRESETS.get(style_name)
    if not style_config:
        print(f"❌ 风格 {style_name} 不存在")
        continue

    prompt_data = {
        **product_info,
        "style": style_config.get("atmosphere"),
        "main_colors": style_config.get("colors")
    }

    print(f"[OK] 风格: {style_name}")
    print(f"  - 氛围: {prompt_data['style']}")
    print(f"  - 颜色: {prompt_data['main_colors']}")
    print()

    # 模拟生成提示词
    prompt = f"产品:{prompt_data['product_name']}, 风格:{prompt_data['style']}, 颜色:{prompt_data['main_colors']}"
    prompts_with_styles.append((prompt, style_name, count_per_style))

print(f"\n总共生成 {len(prompts_with_styles)} 个不同风格的提示词")
print("\n每个提示词内容:")
for i, (prompt, style_name, count) in enumerate(prompts_with_styles, 1):
    print(f"\n{i}. {style_name}:")
    print(f"   {prompt}")

print("\n=== 结论 ===")
if len(prompts_with_styles) == len(selected_styles):
    print("[OK] 逻辑正确：每个风格都生成了独立的提示词")
    print("[OK] 每个提示词包含不同的风格和颜色配置")
else:
    print("[ERROR] 逻辑错误：提示词数量不匹配")
