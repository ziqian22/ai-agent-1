"""
Running Hub 标准模型API 测试脚本
用于测试完整流程: 上传 → 抠图 → 合成Logo → 易拉宝生成
"""

import httpx
import time
import json
from pathlib import Path
from PIL import Image

# ========== 配置区 ==========
API_KEY = "0dc2458715c54ce7bbf662ecdee7977d"  # ⚠️ 替换成你的真实API Key
BASE_URL = "https://www.runninghub.cn/openapi/v2"

# 产品图片路径(本地文件)
PRODUCT_IMAGE_PATH = "1_b.png"  # 确保图片在当前目录下

# Logo配置
LOGO_PATH = "PUDOW朴道健康水专家-原色.png"  # 品牌logo路径
ENABLE_LOGO = True  # 是否在生成时包含logo

# 抠图配置
ENABLE_CUTOUT = True  # 是否启用抠图功能
CUTOUT_PROMPT = "只保留饮水机"  # 抠图提示词

# 生成参数 - 针对勇士K6/K9直饮机产品优化
PROMPT = """设计一张专业的商业易拉宝海报,尺寸接近80x200cm的竖版比例。

产品: 勇士K6/K9即开直饮机
品牌: 朴道健康水专家
特点:
- 澎湃开水持续出,绿色节能新选择
- 高达125L/H开水量
- 100℃开水持续出
- 4重深度净化
- 纳米单晶磨石釉内胆,无重金属加热
- 无加热水箱设计,省滤水只烧滤1次
- LED紫外灯过滤式杀菌,24小时循环杀菌
- 涉膜可视窗设计,加热沸腾过程全程可见
- 接水高度≥38cm,适合市面大多数接水壶使用
- IOT智能云平台,全生命周期技术保障
- 10重安全防护,蒸汽超温保护、滚烫保护等

适用场景: 商务办公、政府机关、医院病房、居委院校、高铁机场

设计要求:
- 顶部(占比15%): 品牌"朴道健康水专家"和产品名称"勇士K6/K9即开直饮机"居中或左侧放置
- 右上角: 放置品牌logo(PUDOW朴道标识)
  * 重要!Logo必须完全保持原样,不做任何修改、变形、重绘
  * Logo位置在右上角,距离右边缘和顶部边缘各留出安全边距
  * Logo清晰可见,适当大小
- 中部(占比45%): 产品图片居中突出展示(黑色+银色机身)
- 核心卖点(占比5%): "澎湃开水持续出 绿色节能新选择"
  * 重要!标语必须保持完整性,每个分句在同一行显示
  * "澎湃开水持续出"为一行,"绿色节能新选择"为另一行
  * 不要把"澎湃开水"和"持续出"分成两行
- 特点展示(占比15%):
  * 分为两个层级展示:
    - 主要卖点(3-4个): 较大字号,突出显示核心数字(125L/H、100℃、4重净化、LED杀菌)
    - 次要特点(3-4个): 较小字号,补充说明(IOT智能、10重防护、可视窗、接水高度)
  * 采用网格布局,横向2-3列排列
  * 每个特点用图标+精简文字
  * 主次分明,视觉层次清晰,格式统一
- 适用场景(占比5%):
  * 5个场景的小尺寸缩略图,不要过大
  * 场景: 商务办公、政府机关、医院病房、居委院校、高铁机场
  * 每个场景照片尺寸适中,配简短文字标注
  * 横向紧凑排列,作为辅助信息展示
- 底部预留区(占比15%):
  * 重要!底部必须预留约六分之一的空白区域
  * 此区域用于后期添加联系方式、购买途径等信息
  * 保持空白,不要填充任何内容
- 整体风格: 专业、健康、环保、科技感
- 主色调: 蓝色+白色+灰色,体现健康水的清洁感
- 布局: 清晰、层次分明、主次有序、突出"健康水专家"定位

印刷要求:
- 上下左右各预留3-5cm安全边距,重要内容不得放置在边缘区域
- 符合印刷标准,预留出血位,确保可直接用于80cm×200cm尺寸印刷制作

输出比例使用9:21(最接近易拉宝的竖版比例)"""

ASPECT_RATIO = "9:21"  # 最接近80:200的比例 (原本想用2:5但API不支持)
RESOLUTION = "2k"  # 可选: 1k, 2k, 4k
# ============================


def upload_image(image_path):
    """上传图片到Running Hub"""
    print(f"📤 上传图片: {image_path}")

    url = f"{BASE_URL}/media/upload/binary"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    with open(image_path, 'rb') as f:
        files = {'file': f}
        response = httpx.post(url, files=files, headers=headers, timeout=30.0)

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:
            file_name = result['data']['fileName']
            download_url = result['data']['download_url']
            print(f"✅ 上传成功: {file_name}")
            return file_name, download_url

    print(f"❌ 上传失败: {response.text}")
    return None, None


def cutout_product(file_name, cutout_prompt):
    """调用抠图API,去除背景和文字"""
    print(f"\n✂️  开始抠图处理...")
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

        # 等待抠图完成
        print(f"⏳ 等待抠图完成...")
        cutout_result = wait_for_completion(task_id, task_name="抠图")

        if cutout_result and cutout_result.get('status') == 'SUCCESS':
            results = cutout_result.get('results', [])
            if results:
                cutout_url = results[0]['url']
                print(f"✅ 抠图完成!")
                print(f"📷 抠图结果: {cutout_url}")

                # 下载抠图结果
                save_dir = Path("results")
                save_dir.mkdir(exist_ok=True)
                cutout_path = save_dir / "cutout_product.png"

                response = httpx.get(cutout_url, timeout=30.0)
                if response.status_code == 200:
                    with open(cutout_path, 'wb') as f:
                        f.write(response.content)
                    print(f"💾 抠图已保存: {cutout_path}")

                return cutout_url

        print(f"❌ 抠图失败")
        return None

    print(f"❌ 抠图任务提交失败: {response.text}")
    return None


def compose_product_with_logo(product_image_path, logo_path, output_path="results/composed_product.png"):
    """将产品图和logo合成到一张图上"""
    print(f"\n🎨 合成产品图和logo...")

    try:
        # 打开产品图
        product = Image.open(product_image_path).convert("RGBA")
        product_width, product_height = product.size

        # 打开logo
        logo = Image.open(logo_path).convert("RGBA")

        # 计算logo大小(约为产品图宽度的18%)
        logo_width = int(product_width * 0.18)
        logo_aspect = logo.size[1] / logo.size[0]
        logo_height = int(logo_width * logo_aspect)
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

        # 创建新画布(稍微扩大以容纳logo)
        canvas_width = product_width
        canvas_height = product_height + int(logo_height * 0.5)  # 顶部留更多空间
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))

        # 计算位置 - logo放在右上角,但要避开出血线(按80x200cm易拉宝,3-5cm安全边距约占6-8%)
        # 右侧距离边缘至少8%,顶部距离边缘至少6%
        safe_margin_x = int(product_width * 0.08)  # 右侧安全边距
        safe_margin_y = int(product_height * 0.06)  # 顶部安全边距

        logo_x = canvas_width - logo_width - safe_margin_x
        logo_y = safe_margin_y

        # 产品图居中偏下
        product_x = 0
        product_y = int(logo_height * 0.5)

        # 粘贴产品图
        canvas.paste(product, (product_x, product_y), product)

        # 粘贴logo
        canvas.paste(logo, (logo_x, logo_y), logo)

        # 保存
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path, "PNG")

        print(f"✅ 合成完成: {output_path}")
        print(f"   - 产品图尺寸: {product_width}x{product_height}")
        print(f"   - Logo尺寸: {logo_width}x{logo_height}")
        print(f"   - Logo位置: 右上角,距右边缘{safe_margin_x}px,距顶部{safe_margin_y}px (避开出血线)")
        print(f"   - 合成图尺寸: {canvas_width}x{canvas_height}")

        return output_path

    except Exception as e:
        print(f"❌ 合成失败: {str(e)}")
        return None


def add_logo_to_banner(banner_path, logo_path, output_path=None):
    """在生成好的易拉宝上添加原始logo(保持logo不变形)"""
    print(f"\n🎨 在易拉宝上添加原始Logo...")

    try:
        # 打开易拉宝
        banner = Image.open(banner_path).convert("RGBA")
        banner_width, banner_height = banner.size

        # 打开logo
        logo = Image.open(logo_path).convert("RGBA")

        # 计算logo大小(约为易拉宝宽度的18%)
        logo_width = int(banner_width * 0.18)
        logo_aspect = logo.size[1] / logo.size[0]
        logo_height = int(logo_width * logo_aspect)
        logo_resized = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

        # 计算位置 - 右上角,避开出血线(8%右边距,6%顶部边距)
        safe_margin_x = int(banner_width * 0.08)
        safe_margin_y = int(banner_height * 0.06)

        logo_x = banner_width - logo_width - safe_margin_x
        logo_y = safe_margin_y

        # 粘贴logo
        banner.paste(logo_resized, (logo_x, logo_y), logo_resized)

        # 保存
        if output_path is None:
            output_path = banner_path.replace('.png', '_with_logo.png')

        banner.save(output_path, "PNG")

        print(f"✅ Logo添加完成: {output_path}")
        print(f"   - 易拉宝尺寸: {banner_width}x{banner_height}")
        print(f"   - Logo尺寸: {logo_width}x{logo_height}")
        print(f"   - Logo位置: 右上角,距右边缘{safe_margin_x}px,距顶部{safe_margin_y}px")

        return output_path

    except Exception as e:
        print(f"❌ Logo添加失败: {str(e)}")
        return None


def start_generation(image_url, prompt, aspect_ratio, resolution):
    """开始生成易拉宝"""
    print(f"\n🚀 开始生成易拉宝...")

    url = f"{BASE_URL}/rhart-image-g-2/image-to-image"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "prompt": prompt,
        "imageUrls": [image_url],
        "aspectRatio": aspect_ratio,
        "resolution": resolution
    }

    print(f"📝 Prompt: {prompt[:100]}...")  # 只显示前100字符
    print(f"📐 比例: {aspect_ratio}")
    print(f"🎨 分辨率: {resolution}")

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)

        print(f"\n🔍 响应状态码: {response.status_code}")
        print(f"🔍 响应内容: {response.text[:500]}")  # 显示前500字符

        if response.status_code == 200:
            result = response.json()
            task_id = result.get('taskId')
            print(f"✅ 任务已提交: {task_id}")
            return task_id
        else:
            print(f"❌ 提交失败: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 请求出错: {str(e)}")
        return None


def query_task(task_id):
    """查询任务状态"""
    url = f"{BASE_URL}/query"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {"taskId": task_id}
    response = httpx.post(url, json=payload, headers=headers, timeout=30.0)

    if response.status_code == 200:
        return response.json()

    return None


def wait_for_completion(task_id, task_name="生成", max_wait=600):
    """等待任务完成"""
    print(f"\n⏳ 等待{task_name}完成...")

    start_time = time.time()

    while time.time() - start_time < max_wait:
        result = query_task(task_id)

        if not result:
            print("❌ 查询失败")
            return None

        status = result.get('status')
        elapsed = int(time.time() - start_time)

        print(f"⏱️  [{elapsed}s] 状态: {status}")

        if status == 'SUCCESS':
            cost_time = result.get('usage', {}).get('taskCostTime', 'N/A')
            print(f"\n✅ {task_name}完成! 耗时: {cost_time}秒")
            return result

        elif status == 'FAILED':
            print(f"\n❌ {task_name}失败: {result.get('errorMessage')}")
            return result

        time.sleep(5)

    print(f"\n⏰ 超时(超过{max_wait}秒)")
    return None


def main():
    print("=" * 60)
    print("Running Hub 易拉宝生成测试 (含抠图+Logo)")
    print("=" * 60)

    # 检查配置
    if API_KEY == "your_api_key_here":
        print("❌ 请先在脚本中配置 API_KEY")
        return

    if not Path(PRODUCT_IMAGE_PATH).exists():
        print(f"❌ 找不到产品图片: {PRODUCT_IMAGE_PATH}")
        return

    # 1. 上传原始图片
    print(f"\n{'='*60}")
    print(f"步骤1: 上传原始图片")
    print(f"{'='*60}")
    file_name, download_url = upload_image(PRODUCT_IMAGE_PATH)
    if not file_name:
        return

    # 2. 抠图处理(可选)
    cutout_path = None
    if ENABLE_CUTOUT:
        print(f"\n{'='*60}")
        print(f"步骤2: 抠图处理")
        print(f"{'='*60}")
        cutout_url = cutout_product(file_name, CUTOUT_PROMPT)
        if cutout_url:
            cutout_path = "results/cutout_product.png"
            print(f"✅ 抠图完成")
        else:
            print(f"⚠️  抠图失败,将使用原图")
    else:
        print(f"\n⚠️  已跳过抠图步骤(ENABLE_CUTOUT=False)")

    # 3. 合成产品图和logo(可选)
    final_image_path = cutout_path if cutout_path else PRODUCT_IMAGE_PATH

    if ENABLE_LOGO:
        print(f"\n{'='*60}")
        print(f"步骤3: 合成产品图和Logo")
        print(f"{'='*60}")

        if not Path(LOGO_PATH).exists():
            print(f"⚠️  找不到Logo文件: {LOGO_PATH},跳过合成")
            image_url = download_url
        else:
            composed_path = compose_product_with_logo(final_image_path, LOGO_PATH)
            if composed_path:
                # 上传合成后的图片
                print(f"\n📤 上传合成后的图片...")
                _, composed_url = upload_image(composed_path)
                if composed_url:
                    image_url = composed_url
                    print(f"✅ 将使用合成后的图片(含Logo)生成易拉宝")
                else:
                    print(f"⚠️  上传合成图失败,使用原图")
                    image_url = download_url
            else:
                print(f"⚠️  合成失败,使用原图")
                image_url = download_url
    else:
        image_url = download_url
        print(f"\n⚠️  已跳过Logo合成(ENABLE_LOGO=False)")

    # 4. 生成易拉宝
    print(f"\n{'='*60}")
    print(f"步骤4: 生成易拉宝")
    print(f"{'='*60}")
    task_id = start_generation(image_url, PROMPT, ASPECT_RATIO, RESOLUTION)
    if not task_id:
        return

    # 5. 等待完成
    result = wait_for_completion(task_id, task_name="易拉宝生成")
    if not result:
        return

    # 6. 下载结果
    if result.get('status') == 'SUCCESS':
        results = result.get('results', [])

        if not results:
            print("⚠️  没有生成结果")
            return

        Path("results").mkdir(exist_ok=True)

        print(f"\n📥 下载结果...")

        for idx, item in enumerate(results):
            image_url = item.get('url')
            if not image_url:
                continue

            output_type = item.get('outputType', 'png')
            save_path = f"results/result_{idx}.{output_type}"

            print(f"  下载: {image_url}")

            response = httpx.get(image_url, timeout=30.0)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"  ✅ 已保存: {save_path}")
            else:
                print(f"  ❌ 下载失败")

        print(f"\n🎉 易拉宝生成完成! 结果保存在 results/ 目录")

    print("\n" + "=" * 60)
    print("🎉 完整流程测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
