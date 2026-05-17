"""
Running Hub API 限流和并发测试
测试目标：
1. 单个任务的响应时间
2. 并发请求的成功率
3. API限流阈值
4. 最佳并发数量
"""

import httpx
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from pathlib import Path
import json
from datetime import datetime


class APILimitTester:
    """API限流测试器"""

    def __init__(self, api_key: str, base_url: str = "https://www.runninghub.cn/openapi/v2"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.test_results = []

    def test_single_request(self) -> Dict[str, Any]:
        """测试单个请求的响应时间"""
        print("\n" + "="*60)
        print("测试1: 单个请求响应时间")
        print("="*60)

        try:
            start_time = time.time()

            # 测试查询接口（最轻量的接口）
            url = f"{self.base_url}/query"
            payload = {"taskId": "test_task_id"}

            response = httpx.post(url, json=payload, headers=self.headers, timeout=30.0)

            elapsed = time.time() - start_time

            result = {
                "test": "single_request",
                "status_code": response.status_code,
                "elapsed": elapsed,
                "success": response.status_code == 200
            }

            print(f"[OK] 状态码: {response.status_code}")
            print(f"[TIME] 响应时间: {elapsed:.2f}秒")

            return result

        except Exception as e:
            print(f"[ERROR] 错误: {str(e)}")
            return {
                "test": "single_request",
                "success": False,
                "error": str(e)
            }

    def test_concurrent_requests(self, concurrent_count: int) -> Dict[str, Any]:
        """测试并发请求"""
        print(f"\n" + "="*60)
        print(f"测试2: {concurrent_count}个并发请求")
        print("="*60)

        def make_request(index: int) -> Dict[str, Any]:
            """发送单个请求"""
            try:
                start_time = time.time()

                url = f"{self.base_url}/query"
                payload = {"taskId": f"test_task_{index}"}

                response = httpx.post(url, json=payload, headers=self.headers, timeout=30.0)

                elapsed = time.time() - start_time

                return {
                    "index": index,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                    "success": response.status_code == 200,
                    "rate_limited": response.status_code == 429
                }

            except Exception as e:
                return {
                    "index": index,
                    "success": False,
                    "error": str(e)
                }

        # 并发执行
        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
            futures = [executor.submit(make_request, i) for i in range(concurrent_count)]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                status = "[OK]" if result.get("success") else "[ERROR]"
                if result.get("rate_limited"):
                    status = "[WARN] 限流"

                print(f"{status} 请求 {result['index']+1}: {result.get('elapsed', 0):.2f}秒")

        total_elapsed = time.time() - start_time

        # 统计
        success_count = sum(1 for r in results if r.get("success"))
        rate_limited_count = sum(1 for r in results if r.get("rate_limited"))
        failed_count = len(results) - success_count

        avg_elapsed = sum(r.get("elapsed", 0) for r in results if "elapsed" in r) / len(results)

        print(f"\n[STATS] 统计:")
        print(f"   总耗时: {total_elapsed:.2f}秒")
        print(f"   平均响应时间: {avg_elapsed:.2f}秒")
        print(f"   成功: {success_count}/{concurrent_count}")
        print(f"   限流: {rate_limited_count}/{concurrent_count}")
        print(f"   失败: {failed_count}/{concurrent_count}")

        return {
            "test": f"concurrent_{concurrent_count}",
            "concurrent_count": concurrent_count,
            "total_elapsed": total_elapsed,
            "avg_elapsed": avg_elapsed,
            "success_count": success_count,
            "rate_limited_count": rate_limited_count,
            "failed_count": failed_count,
            "results": results
        }

    def test_upload_concurrency(self, test_image_path: str, concurrent_count: int) -> Dict[str, Any]:
        """测试上传接口的并发限制"""
        print(f"\n" + "="*60)
        print(f"测试3: {concurrent_count}个并发上传")
        print("="*60)

        if not Path(test_image_path).exists():
            print(f"[ERROR] 测试图片不存在: {test_image_path}")
            return {"test": "upload_concurrency", "success": False, "error": "测试图片不存在"}

        def upload_image(index: int) -> Dict[str, Any]:
            """上传单个图片"""
            try:
                start_time = time.time()

                url = f"{self.base_url}/media/upload/binary"
                headers = {"Authorization": f"Bearer {self.api_key}"}

                with open(test_image_path, 'rb') as f:
                    files = {'file': f}
                    response = httpx.post(url, files=files, headers=headers, timeout=60.0)

                elapsed = time.time() - start_time

                return {
                    "index": index,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                    "success": response.status_code == 200,
                    "rate_limited": response.status_code == 429
                }

            except Exception as e:
                return {
                    "index": index,
                    "success": False,
                    "error": str(e)
                }

        # 并发执行
        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
            futures = [executor.submit(upload_image, i) for i in range(concurrent_count)]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                status = "[OK]" if result.get("success") else "[ERROR]"
                if result.get("rate_limited"):
                    status = "[WARN] 限流"

                print(f"{status} 上传 {result['index']+1}: {result.get('elapsed', 0):.2f}秒")

        total_elapsed = time.time() - start_time

        # 统计
        success_count = sum(1 for r in results if r.get("success"))
        rate_limited_count = sum(1 for r in results if r.get("rate_limited"))
        failed_count = len(results) - success_count

        avg_elapsed = sum(r.get("elapsed", 0) for r in results if "elapsed" in r) / len(results)

        print(f"\n[STATS] 统计:")
        print(f"   总耗时: {total_elapsed:.2f}秒")
        print(f"   平均上传时间: {avg_elapsed:.2f}秒")
        print(f"   成功: {success_count}/{concurrent_count}")
        print(f"   限流: {rate_limited_count}/{concurrent_count}")
        print(f"   失败: {failed_count}/{concurrent_count}")

        return {
            "test": f"upload_concurrent_{concurrent_count}",
            "concurrent_count": concurrent_count,
            "total_elapsed": total_elapsed,
            "avg_elapsed": avg_elapsed,
            "success_count": success_count,
            "rate_limited_count": rate_limited_count,
            "failed_count": failed_count,
            "results": results
        }

    def test_generation_concurrency(
        self,
        test_image_url: str,
        test_prompt: str,
        concurrent_count: int
    ) -> Dict[str, Any]:
        """测试生成接口的并发限制"""
        print(f"\n" + "="*60)
        print(f"测试4: {concurrent_count}个并发生成任务")
        print("="*60)

        def submit_generation(index: int) -> Dict[str, Any]:
            """提交单个生成任务"""
            try:
                start_time = time.time()

                url = f"{self.base_url}/rhart-image-g-2/image-to-image"
                payload = {
                    "prompt": test_prompt,
                    "imageUrls": [test_image_url],
                    "aspectRatio": "9:21",
                    "resolution": "2k"
                }

                response = httpx.post(url, json=payload, headers=self.headers, timeout=30.0)

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
                    "task_id": result_data.get("taskId") if result_data else None
                }

            except Exception as e:
                return {
                    "index": index,
                    "success": False,
                    "error": str(e)
                }

        # 并发执行
        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
            futures = [executor.submit(submit_generation, i) for i in range(concurrent_count)]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                status = "[OK]" if result.get("success") else "[ERROR]"
                if result.get("rate_limited"):
                    status = "[WARN] 限流"

                task_id = result.get("task_id", "N/A")
                print(f"{status} 生成 {result['index']+1}: {result.get('elapsed', 0):.2f}秒 - TaskID: {task_id}")

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

        return {
            "test": f"generation_concurrent_{concurrent_count}",
            "concurrent_count": concurrent_count,
            "total_elapsed": total_elapsed,
            "avg_elapsed": avg_elapsed,
            "success_count": success_count,
            "rate_limited_count": rate_limited_count,
            "failed_count": failed_count,
            "results": results
        }

    def run_full_test_suite(self, test_image_path: str = None):
        """运行完整测试套件"""
        print("\n" + "="*30)
        print("Running Hub API 限流和并发测试")
        print("="*30)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        all_results = []

        # 测试1: 单个请求
        result1 = self.test_single_request()
        all_results.append(result1)
        time.sleep(2)  # 间隔2秒

        # 测试2: 不同并发数的查询请求
        for concurrent in [3, 5, 10]:
            result = self.test_concurrent_requests(concurrent)
            all_results.append(result)
            time.sleep(3)  # 间隔3秒

        # 测试3: 上传并发（如果提供了测试图片）
        if test_image_path and Path(test_image_path).exists():
            for concurrent in [3, 5]:
                result = self.test_upload_concurrency(test_image_path, concurrent)
                all_results.append(result)
                time.sleep(3)

        # 保存结果
        self.save_results(all_results)

        # 生成报告
        self.generate_report(all_results)

    def save_results(self, results: List[Dict[str, Any]]):
        """保存测试结果"""
        output_file = Path("test_results") / f"api_limit_test_{int(time.time())}.json"
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVE] 测试结果已保存: {output_file}")

    def generate_report(self, results: List[Dict[str, Any]]):
        """生成测试报告"""
        print("\n" + "="*60)
        print("[REPORT] 测试报告总结")
        print("="*60)

        # 分析并发性能
        concurrent_tests = [r for r in results if "concurrent" in r.get("test", "")]

        if concurrent_tests:
            print("\n[ANALYSIS] 并发性能分析:")
            for test in concurrent_tests:
                concurrent_count = test.get("concurrent_count", 0)
                success_rate = (test.get("success_count", 0) / concurrent_count * 100) if concurrent_count > 0 else 0
                rate_limited = test.get("rate_limited_count", 0)

                print(f"\n  并发数: {concurrent_count}")
                print(f"  成功率: {success_rate:.1f}%")
                print(f"  限流次数: {rate_limited}")
                print(f"  平均响应时间: {test.get('avg_elapsed', 0):.2f}秒")

                if rate_limited > 0:
                    print(f"  [WARN]  警告: 检测到限流，建议降低并发数")

        # 推荐配置
        print("\n[RECOMMEND] 推荐配置:")

        # 找到最佳并发数（成功率100%且最快的）
        successful_tests = [t for t in concurrent_tests if t.get("success_count") == t.get("concurrent_count")]

        if successful_tests:
            best_test = min(successful_tests, key=lambda x: x.get("avg_elapsed", float('inf')))
            print(f"  推荐并发数: {best_test.get('concurrent_count')}")
            print(f"  预期响应时间: {best_test.get('avg_elapsed', 0):.2f}秒")
        else:
            print(f"  推荐并发数: 3 (保守策略)")

        print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """主函数"""
    # 从配置文件读取API密钥
    api_key = None
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('RUNNINGHUB_API_KEY='):
                    api_key = line.split('=')[1].strip().strip('"').strip("'")
                    break

        if not api_key:
            print("[ERROR] 未找到 RUNNINGHUB_API_KEY")
            return
    except FileNotFoundError:
        print("[ERROR] 未找到 .env 文件")
        return

    # 查找测试图片
    test_image = None
    for pattern in ["*.jpg", "*.png", "*.jpeg"]:
        images = list(Path(".").glob(pattern))
        if images:
            test_image = str(images[0])
            break

    if test_image:
        print(f"[IMAGE] 使用测试图片: {test_image}")
    else:
        print("[WARNING] 未找到测试图片，将跳过上传测试")

    # 创建测试器
    tester = APILimitTester(api_key)

    # 运行测试
    tester.run_full_test_suite(test_image)


if __name__ == "__main__":
    main()
