"""
Running Hub 标准模型API 测试脚本
用于测试 image-to-image API (易拉宝生成)
"""

import httpx
import time
import json
from pathlib import Path

# ========== 配置区 ==========
API_KEY = "0dc2458715c54ce7bbf662ecdee7977d"  # ⚠️ 替换成你的真实API Key
BASE_URL = "https://www.runninghub.cn/openapi/v2"

# 产品图片路径(本地文件)
PRODUCT_IMAGE_PATH = "1_b.png"  # 确保图片在当前目录下

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
- 顶部: 品牌"朴道健康水专家"和产品名称"勇士K6/K9即开直饮机"
- 中部: 产品图片居中突出展示(黑色+银色机身)
- 核心卖点: "澎湃开水持续出 绿色节能新选择"
- 特点展示: 用图标+文字展示核心特点(125L/H开水量、100℃持续出水、4重净化)
- 底部: 适用场景和技术参数
- 整体风格: 专业、健康、环保、科技感
- 主色调: 蓝色+白色+灰色,体现健康水的清洁感
- 布局: 清晰、层次分明、突出"健康水专家"定位

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
            download_url = result['data']['download_url']
            print(f"✅ 上传成功: {download_url}")
            return download_url

    print(f"❌ 上传失败: {response.text}")
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


def wait_for_completion(task_id, max_wait=600):
    """等待任务完成"""
    print(f"\n⏳ 等待生成完成...")

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
            print(f"\n✅ 生成完成! 耗时: {result.get('usage', {}).get('taskCostTime', 'N/A')}秒")
            return result

        elif status == 'FAILED':
            print(f"\n❌ 生成失败: {result.get('errorMessage')}")
            return result

        time.sleep(5)

    print(f"\n⏰ 超时(超过{max_wait}秒)")
    return None


def download_results(result, save_dir="results"):
    """下载生成的图片"""
    results = result.get('results', [])

    if not results:
        print("⚠️  没有生成结果")
        return

    Path(save_dir).mkdir(exist_ok=True)

    print(f"\n📥 下载结果...")

    for idx, item in enumerate(results):
        image_url = item.get('url')
        if not image_url:
            continue

        output_type = item.get('outputType', 'png')
        save_path = f"{save_dir}/result_{idx}.{output_type}"

        print(f"  下载: {image_url}")

        response = httpx.get(image_url, timeout=30.0)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"  ✅ 已保存: {save_path}")
        else:
            print(f"  ❌ 下载失败")

    print(f"\n🎉 完成! 结果保存在 {save_dir}/ 目录")


def main():
    print("=" * 60)
    print("Running Hub 易拉宝生成测试")
    print("=" * 60)

    # 检查配置
    if API_KEY == "your_api_key_here":
        print("❌ 请先在脚本中配置 API_KEY")
        return

    if not Path(PRODUCT_IMAGE_PATH).exists():
        print(f"❌ 找不到产品图片: {PRODUCT_IMAGE_PATH}")
        return

    # 1. 上传图片
    image_url = upload_image(PRODUCT_IMAGE_PATH)
    if not image_url:
        return

    # 2. 开始生成
    task_id = start_generation(image_url, PROMPT, ASPECT_RATIO, RESOLUTION)
    if not task_id:
        return

    # 3. 等待完成
    result = wait_for_completion(task_id)
    if not result:
        return

    # 4. 下载结果
    if result.get('status') == 'SUCCESS':
        download_results(result)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
