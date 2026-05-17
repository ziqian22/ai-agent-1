"""
测试易拉宝生成接口的并发限制
这是最关键的测试，因为生成接口最耗资源
"""

import httpx
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json


def test_generation_api_concurrency():
    """测试生成API的并发限制"""

    # 读取API密钥
    api_key = None
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('RUNNINGHUB_API_KEY='):
                    api_key = line.split('=')[1].strip().strip('"').strip("'")
                    break
    except FileNotFoundError:
        print("[ERROR] 未找到 .env 文件")
        return

    if not api_key:
        print("[ERROR] 未找到 RUNNINGHUB_API_KEY")
        return

    base_url = "https://www.runninghub.cn/openapi/v2"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # 先上传一张测试图片
    print("\n" + "="*60)
    print("步骤1: 上传测试图片")
    print("="*60)

    # 查找测试图片
    test_image = None
    for pattern in ["*.jpg", "*.png", "*.jpeg"]:
        images = list(Path(".").glob(pattern))
        if images:
            test_image = str(images[0])
            break

    if not test_image:
        print("[ERROR] 未找到测试图片")
        return

    print(f"使用测试图片: {test_image}")

    # 上传图片
    try:
        upload_url = f"{base_url}/media/upload/binary"
        upload_headers = {"Authorization": f"Bearer {api_key}"}

        with open(test_image, 'rb') as f:
            files = {'file': f}
            response = httpx.post(upload_url, files=files, headers=upload_headers, timeout=60.0)

        if response.status_code != 200:
            print(f"[ERROR] 上传失败: {response.status_code}")
            return

        result = response.json()
        if result.get('code') != 0:
            print(f"[ERROR] 上传失败: {result}")
            return

        image_url = result['data']['download_url']
        print(f"[OK] 上传成功: {image_url}")

    except Exception as e:
        print(f"[ERROR] 上传异常: {str(e)}")
        return

    # 测试提示词
    test_prompt = """设计一张专业的商业易拉宝海报，尺寸接近80x200cm的竖版比例。
产品: 测试产品
品牌: 测试品牌
设计要求: 简洁、专业、现代
输出比例使用9:21"""

    def submit_generation_task(index: int):
        """提交单个生成任务"""
        try:
            start_time = time.time()

            url = f"{base_url}/rhart-image-g-2/image-to-image"
            payload = {
                "prompt": test_prompt,
                "imageUrls": [image_url],
                "aspectRatio": "9:21",
                "resolution": "2k"
            }

            response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
            elapsed = time.time() - start_time

            result_data = None
            if response.status_code == 200:
                result_data = response.json()

            return {
                "index": index,
                "status_code": response.status_code,
                "elapsed": elapsed,
                "success": response.status_code == 200,
                "rate_limited": response.status_code == 429,
                "task_id": result_data.get("taskId") if result_data else None,
                "response": result_data
            }

        except Exception as e:
            return {
                "index": index,
                "success": False,
                "error": str(e)
            }

    # 测试不同并发数
    for concurrent_count in [3, 5, 7]:
        print("\n" + "="*60)
        print(f"测试: {concurrent_count}个并发生成任务")
        print("="*60)

        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
            futures = [executor.submit(submit_generation_task, i) for i in range(concurrent_count)]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                status = "[OK]" if result.get("success") else "[ERROR]"
                if result.get("rate_limited"):
                    status = "[WARN] 限流"

                task_id = result.get("task_id", "N/A")
                print(f"{status} 任务 {result['index']+1}: {result.get('elapsed', 0):.2f}秒 - TaskID: {task_id}")

        total_elapsed = time.time() - start_time

        # 统计
        success_count = sum(1 for r in results if r.get("success"))
        rate_limited_count = sum(1 for r in results if r.get("rate_limited"))
        failed_count = len(results) - success_count

        avg_elapsed = sum(r.get("elapsed", 0) for r in results if "elapsed" in r) / len(results)

        print(f"\n[STATS] 统计:")
        print(f"   总耗时: {total_elapsed:.2f}秒")
        print(f"   平均提交时间: {avg_elapsed:.2f}秒")
        print(f"   成功: {success_count}/{concurrent_count}")
        print(f"   限流: {rate_limited_count}/{concurrent_count}")
        print(f"   失败: {failed_count}/{concurrent_count}")

        if rate_limited_count > 0:
            print(f"\n[WARN] 检测到限流！建议降低并发数")

        # 保存结果
        output_file = Path("test_results") / f"generation_concurrent_{concurrent_count}_{int(time.time())}.json"
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVE] 结果已保存: {output_file}")

        # 间隔5秒再测试下一个并发数
        if concurrent_count < 7:
            print("\n等待5秒后继续下一组测试...")
            time.sleep(5)

    print("\n" + "="*60)
    print("[REPORT] 生成接口并发测试完成")
    print("="*60)


if __name__ == "__main__":
    test_generation_api_concurrency()
