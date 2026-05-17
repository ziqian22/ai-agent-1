"""
完整流程测试脚本
测试: 原图 → 抠图 → 易拉宝生成
"""

import httpx
import time
from pathlib import Path

# ========== 配置区 ==========
API_KEY = "0dc2458715c54ce7bbf662ecdee7977d"
BASE_URL = "https://www.runninghub.cn/openapi/v2"

# 产品图片路径
PRODUCT_IMAGE_PATH = "1_b.png"

# 产品信息(后续会用Claude Vision自动提取,现在手动填写)
PRODUCT_INFO = {
    "product_name": "勇士K6/K9即开直饮机",
    "brand": "朴道健康水专家",
    "features": [
        "高达125L/H开水量",
        "100℃开水持续出",
        "4重深度净化",
        "纳米单晶磨石釉内胆",
        "LED紫外灯过滤式杀菌"
    ],
    "description": "澎湃开水持续出,绿色节能新选择",
    "product_type": "饮水机"
}

# 抠图prompt
CUTOUT_PROMPT = "只保留饮水机"

# 易拉宝风格
BANNER_STYLE = "科技感"  # 可选: 科技感/简约商务/自然清新/时尚活力/高端奢华
# ============================


def upload_image(image_path):
    """上传图片到Running Hub"""
    print(f"\n{'='*60}")
    print(f"📤 步骤1: 上传原始图片")
    print(f"{'='*60}")

    url = f"{BASE_URL}/media/upload/binary"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    with open(image_path, 'rb') as f:
        files = {'file': f}
        response = httpx.post(url, files=files, headers=headers, timeout=30.0)

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:
            file_name = result['data']['fileName']
            print(f"✅ 上传成功: {file_name}")
            return file_name

    print(f"❌ 上传失败: {response.text}")
    return None


def cutout_product(file_name, cutout_prompt):
    """调用抠图API,去除背景和文字"""
    print(f"\n{'='*60}")
    print(f"✂️  步骤2: 抠图处理")
    print(f"{'='*60}")
    print(f"抠图提示词: {cutout_prompt}")

    url = f"{BASE_URL}/run/ai-app/1968163548209774594"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "nodeInfoList": [
            {
                "nodeId": "3",
                "fieldName": "image",
                "fieldValue": file_name,
                "description": "image"
            },
            {
                "nodeId": "126",
                "fieldName": "prompt",
                "fieldValue": cutout_prompt,
                "description": "prompt"
            }
        ],
        "instanceType": "default",
        "usePersonalQueue": "false"
    }

    response = httpx.post(url, json=payload, headers=headers, timeout=30.0)

    if response.status_code == 200:
        result = response.json()
        task_id = result.get('taskId')
        print(f"✅ 抠图任务已提交: {task_id}")

        # 等待完成
        print(f"⏳ 等待抠图完成...")
        cutout_result = wait_for_completion(task_id, "抠图")

        if cutout_result and cutout_result.get('status') == 'SUCCESS':
            results = cutout_result.get('results', [])
            if results:
                cutout_url = results[0]['url']
                print(f"✅ 抠图完成!")
                print(f"📷 抠图结果: {cutout_url}")

                # 下载抠图结果
                cutout_path = "results/cutout_product.png"
                download_image(cutout_url, cutout_path)

                return cutout_url, cutout_path

        print(f"❌ 抠图失败")
        return None, None

    print(f"❌ 抠图任务提交失败: {response.text}")
    return None, None


def generate_banner_prompt(product_info, style):
    """生成易拉宝设计prompt"""

    # 简化版风格配置
    style_configs = {
        "科技感": {
            "scene": "现代科技办公空间,简约玻璃幕墙,智能设备环境",
            "lighting": "冷色调LED灯光,蓝白色光效,科技感光线",
            "color": "蓝色+白色+灰色,科技蓝主色调",
            "atmosphere": "专业、现代、智能、高效"
        },
        "简约商务": {
            "scene": "高端商务办公室,大理石台面,极简空间",
            "lighting": "柔和自然光,45度角斜射,明暗对比克制",
            "color": "黑白灰+品牌色,低饱和度配色",
            "atmosphere": "专业、高端、克制、精致"
        },
        "自然清新": {
            "scene": "自然采光空间,绿植环境,木质元素",
            "lighting": "温暖自然光,柔和漫射,清晨或午后光线",
            "color": "绿色+白色+原木色,清新自然",
            "atmosphere": "健康、环保、舒适、亲和"
        }
    }

    config = style_configs.get(style, style_configs["科技感"])
    features_text = " | ".join(product_info['features'][:5])

    prompt = f"""设计一张专业的商业易拉宝海报,严格遵循以下要求:

【尺寸与比例】
- 输出比例: 9:21 (最接近80cm×200cm易拉宝标准尺寸)
- 分辨率: 2K高清
- 安全边距: 上下左右各预留3-5cm安全边距,重要内容不得放置在边缘区域

【产品信息】
- 品牌: {product_info.get('brand', '')}
- 产品名称: {product_info['product_name']}
- 核心卖点: {product_info.get('description', '')}
- 产品特点: {features_text}

【场景与环境】
- 场景设定: {config['scene']}
- 场景处理: 产品清晰聚焦,背景适度虚化形成景深效果,突出产品主体
- 环境氛围: {config['atmosphere']}

【光影效果】
- 光线设计: {config['lighting']}
- 要求: 高级克制的光影处理,避免过度曝光,保持专业商业摄影质感

【色彩方案】
- 主色调: {config['color']}
- 要求: 色彩和谐统一,符合品牌调性,避免过度饱和

【布局结构 - 三段式】
顶部区域(占比15-20%):
- 品牌"{product_info.get('brand', '')}"和产品名称"{product_info['product_name']}"
- 位置: 居中或左对齐,距离顶部边缘至少5cm

中部区域(占比50-60%):
- 产品图片主体展示
- 产品清晰聚焦,细节可见
- 产品与场景自然融合但保持主体突出
- 背景虚化处理,形成视觉焦点

底部区域(占比20-30%):
- 产品核心特点(3-5个)
- 使用图标+简洁文字形式
- 横向或纵向排列,清晰易读
- 距离底部边缘至少5cm

【设计原则】
1. 画面简约克制,无多余装饰元素
2. 信息层次清晰,视觉动线流畅
3. 产品为绝对视觉中心,占据画面主要位置
4. 文字清晰易读,字号层次分明
5. 整体风格: {config['atmosphere']}
6. 符合印刷标准,预留出血位和安全边距

【禁止事项】
- 不要添加无关装饰元素
- 不要让背景喧宾夺主
- 不要将重要信息放在边缘
- 不要使用过于花哨的字体
- 不要让产品图片模糊或失焦

输出一张符合专业印刷标准的易拉宝设计,确保可以直接用于80cm×200cm尺寸的印刷制作。"""

    return prompt.strip()


def generate_banner(cutout_url, prompt):
    """使用抠图后的产品图生成易拉宝"""
    print(f"\n{'='*60}")
    print(f"🎨 步骤3: 生成易拉宝")
    print(f"{'='*60}")
    print(f"使用抠图后的产品图")
    print(f"设计风格: {BANNER_STYLE}")

    url = f"{BASE_URL}/rhart-image-g-2/image-to-image"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "prompt": prompt,
        "imageUrls": [cutout_url],
        "aspectRatio": "9:21",
        "resolution": "2k"
    }

    response = httpx.post(url, json=payload, headers=headers, timeout=30.0)

    if response.status_code == 200:
        result = response.json()
        task_id = result.get('taskId')
        print(f"✅ 易拉宝任务已提交: {task_id}")

        # 等待完成
        print(f"⏳ 等待易拉宝生成...")
        banner_result = wait_for_completion(task_id, "易拉宝生成")

        if banner_result and banner_result.get('status') == 'SUCCESS':
            results = banner_result.get('results', [])
            if results:
                banner_url = results[0]['url']
                print(f"✅ 易拉宝生成完成!")
                print(f"🎉 易拉宝结果: {banner_url}")

                # 下载易拉宝
                banner_path = "results/banner_final.png"
                download_image(banner_url, banner_path)

                return banner_url, banner_path

        print(f"❌ 易拉宝生成失败")
        return None, None

    print(f"❌ 易拉宝任务提交失败: {response.text}")
    return None, None


def wait_for_completion(task_id, task_name, max_wait=600):
    """等待任务完成"""
    url = f"{BASE_URL}/query"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    start_time = time.time()

    while time.time() - start_time < max_wait:
        payload = {"taskId": task_id}
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)

        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            elapsed = int(time.time() - start_time)

            print(f"⏱️  [{elapsed}s] {task_name}状态: {status}")

            if status == 'SUCCESS':
                cost_time = result.get('usage', {}).get('taskCostTime', 'N/A')
                print(f"✅ {task_name}完成! 耗时: {cost_time}秒")
                return result

            elif status == 'FAILED':
                print(f"❌ {task_name}失败: {result.get('errorMessage')}")
                return result

        time.sleep(5)

    print(f"⏰ {task_name}超时")
    return None


def download_image(image_url, save_path):
    """下载图片"""
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)

    response = httpx.get(image_url, timeout=30.0)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"💾 已保存: {save_path}")
        return True

    print(f"❌ 下载失败")
    return False


def main():
    print("\n" + "="*60)
    print("🎨 易拉宝完整流程测试")
    print("="*60)
    print(f"产品: {PRODUCT_INFO['product_name']}")
    print(f"风格: {BANNER_STYLE}")
    print("="*60)

    # 检查图片
    if not Path(PRODUCT_IMAGE_PATH).exists():
        print(f"❌ 找不到图片: {PRODUCT_IMAGE_PATH}")
        return

    # 步骤1: 上传原图
    file_name = upload_image(PRODUCT_IMAGE_PATH)
    if not file_name:
        return

    # 步骤2: 抠图
    cutout_url, cutout_path = cutout_product(file_name, CUTOUT_PROMPT)
    if not cutout_url:
        return

    # 步骤3: 生成易拉宝prompt
    print(f"\n{'='*60}")
    print(f"📝 生成易拉宝设计prompt")
    print(f"{'='*60}")
    banner_prompt = generate_banner_prompt(PRODUCT_INFO, BANNER_STYLE)
    print(f"✅ Prompt已生成 (长度: {len(banner_prompt)}字符)")

    # 步骤4: 生成易拉宝
    banner_url, banner_path = generate_banner(cutout_url, banner_prompt)
    if not banner_url:
        return

    # 完成
    print(f"\n{'='*60}")
    print(f"🎉 完整流程测试完成!")
    print(f"{'='*60}")
    print(f"📁 结果文件:")
    print(f"  - 抠图结果: {cutout_path}")
    print(f"  - 易拉宝: {banner_path}")
    print(f"\n💡 提示: 打开results文件夹查看生成的图片")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
