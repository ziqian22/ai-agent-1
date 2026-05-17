"""
易拉宝生成器
集成完整的生成流程：上传 → 抠图 → 合成Logo → 生成易拉宝
"""

import httpx
import time
from pathlib import Path
from PIL import Image
from typing import Dict, List, Optional, Any, Callable


class BannerGenerator:
    """易拉宝生成器"""

    def __init__(self, api_key: str, base_url: str = "https://www.runninghub.cn/openapi/v2"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def upload_image(self, image_path: str, max_retries: int = 3) -> Optional[tuple]:
        """
        上传图片到Running Hub（带重试机制）

        Args:
            image_path: 图片路径
            max_retries: 最大重试次数

        Returns:
            (file_name, download_url) 或 None
        """
        url = f"{self.base_url}/media/upload/binary"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        for attempt in range(max_retries):
            try:
                print(f"[上传] 尝试上传图片 (第{attempt + 1}/{max_retries}次)...")

                with open(image_path, 'rb') as f:
                    files = {'file': f}
                    # 增加超时时间到120秒，并设置连接超时
                    response = httpx.post(
                        url,
                        files=files,
                        headers=headers,
                        timeout=httpx.Timeout(120.0, connect=30.0)
                    )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0:
                        file_name = result['data']['fileName']
                        download_url = result['data']['download_url']
                        print(f"[上传] 成功: {file_name}")
                        return file_name, download_url
                    else:
                        print(f"[上传] API返回错误: {result.get('message', '未知错误')}")
                else:
                    print(f"[上传] HTTP错误: {response.status_code}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间：2秒、4秒、6秒
                    print(f"[上传] 等待{wait_time}秒后重试...")
                    time.sleep(wait_time)

            except httpx.ConnectTimeout as e:
                print(f"[上传] 连接超时 (第{attempt + 1}次): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                else:
                    print(f"[上传] 连接超时，已达到最大重试次数")

            except httpx.ReadTimeout as e:
                print(f"[上传] 读取超时 (第{attempt + 1}次): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                else:
                    print(f"[上传] 读取超时，已达到最大重试次数")

            except httpx.RemoteProtocolError as e:
                print(f"[上传] 服务器断开连接 (第{attempt + 1}次): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 3)  # 服务器问题，等待更久
                else:
                    print(f"[上传] 服务器连接问题，已达到最大重试次数")

            except Exception as e:
                print(f"[上传] 未知错误 (第{attempt + 1}次): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                else:
                    print(f"[上传] 上传失败，已达到最大重试次数")

        return None

    def cutout_product(
        self,
        file_name: str,
        cutout_prompt: str = "只保留产品主体",
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        抠图处理

        Args:
            file_name: 已上传的文件名
            cutout_prompt: 抠图提示词
            progress_callback: 进度回调函数

        Returns:
            抠图结果URL 或 None
        """
        try:
            if progress_callback:
                progress_callback("开始抠图处理...")

            url = f"{self.base_url}/run/ai-app/1968163548209774594"

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

            response = httpx.post(url, json=payload, headers=self.headers, timeout=30.0)

            if response.status_code == 200:
                result = response.json()
                task_id = result.get('taskId')

                if progress_callback:
                    progress_callback(f"抠图任务已提交: {task_id}")

                # 等待抠图完成
                cutout_result = self._wait_for_completion(
                    task_id,
                    task_name="抠图",
                    progress_callback=progress_callback
                )

                if cutout_result and cutout_result.get('status') == 'SUCCESS':
                    results = cutout_result.get('results', [])
                    if results:
                        cutout_url = results[0]['url']

                        # 下载抠图结果
                        save_dir = Path("results")
                        save_dir.mkdir(exist_ok=True)
                        cutout_path = save_dir / f"cutout_{int(time.time())}.png"

                        response = httpx.get(cutout_url, timeout=120.0)  # 下载大文件,增加到120秒
                        if response.status_code == 200:
                            with open(cutout_path, 'wb') as f:
                                f.write(response.content)

                            if progress_callback:
                                progress_callback(f"抠图完成，已保存: {cutout_path}")

                            return str(cutout_path)

            return None

        except Exception as e:
            print(f"抠图出错: {str(e)}")
            return None

    def compose_with_logo(
        self,
        product_image_path: str,
        logo_path: str,
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        将产品图和Logo合成

        Args:
            product_image_path: 产品图路径
            logo_path: Logo路径
            progress_callback: 进度回调

        Returns:
            合成图路径 或 None
        """
        try:
            if progress_callback:
                progress_callback("开始合成产品图和Logo...")

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

            # 创建新画布
            canvas_width = product_width
            canvas_height = product_height + int(logo_height * 0.5)
            canvas = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))

            # 计算位置 - logo放在右上角，避开出血线
            safe_margin_x = int(product_width * 0.08)
            safe_margin_y = int(product_height * 0.06)

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
            save_dir = Path("results")
            save_dir.mkdir(exist_ok=True)
            output_path = save_dir / f"composed_{int(time.time())}.png"
            canvas.save(output_path, "PNG")

            if progress_callback:
                progress_callback(f"合成完成: {output_path}")

            return str(output_path)

        except Exception as e:
            print(f"合成失败: {str(e)}")
            return None

    def generate_banner(
        self,
        image_url: str,
        prompt: str,
        aspect_ratio: str = "9:21",
        resolution: str = "2k",
        progress_callback: Optional[Callable] = None,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        生成易拉宝（带重试机制）

        Args:
            image_url: 产品图URL
            prompt: 生成提示词
            aspect_ratio: 宽高比
            resolution: 分辨率
            progress_callback: 进度回调
            max_retries: 最大重试次数

        Returns:
            任务ID 或 None
        """
        url = f"{self.base_url}/rhart-image-g-2/image-to-image"

        payload = {
            "prompt": prompt,
            "imageUrls": [image_url],
            "aspectRatio": aspect_ratio,
            "resolution": resolution
        }

        for attempt in range(max_retries):
            try:
                if progress_callback:
                    if attempt == 0:
                        progress_callback("开始生成易拉宝...")
                    else:
                        progress_callback(f"重试生成 (第{attempt + 1}/{max_retries}次)...")

                response = httpx.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=httpx.Timeout(60.0, connect=30.0)
                )

                if response.status_code == 200:
                    result = response.json()
                    task_id = result.get('taskId')

                    if progress_callback:
                        progress_callback(f"生成任务已提交: {task_id}")

                    return task_id
                else:
                    print(f"[生成] HTTP错误: {response.status_code}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"[生成] 等待{wait_time}秒后重试...")
                    time.sleep(wait_time)

            except httpx.RemoteProtocolError as e:
                print(f"[生成] 服务器断开连接 (第{attempt + 1}次): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 3)

            except Exception as e:
                print(f"[生成] 错误 (第{attempt + 1}次): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)

        return None

    def query_task(self, task_id: str) -> Optional[Dict]:
        """查询任务状态"""
        try:
            url = f"{self.base_url}/query"
            payload = {"taskId": task_id}

            response = httpx.post(url, json=payload, headers=self.headers, timeout=30.0)

            if response.status_code == 200:
                return response.json()

            return None

        except Exception as e:
            print(f"查询任务出错: {str(e)}")
            return None

    def _wait_for_completion(
        self,
        task_id: str,
        task_name: str = "任务",
        max_wait: int = 900,  # 增加到15分钟
        progress_callback: Optional[Callable] = None
    ) -> Optional[Dict]:
        """等待任务完成"""
        start_time = time.time()
        check_count = 0

        while time.time() - start_time < max_wait:
            try:
                result = self.query_task(task_id)

                if not result:
                    if progress_callback:
                        progress_callback(f"⚠️ 查询任务状态失败，重试中...")
                    time.sleep(3)
                    continue

                status = result.get('status')
                elapsed = int(time.time() - start_time)
                check_count += 1

                if progress_callback:
                    # 更详细的进度信息
                    progress_msg = f"{task_name}进行中... (已等待 {elapsed}秒, 第{check_count}次检查)"
                    if elapsed > 60:
                        progress_msg += f" [{elapsed // 60}分{elapsed % 60}秒]"
                    progress_callback(progress_msg)

                if status == 'SUCCESS':
                    if progress_callback:
                        progress_callback(f"✅ {task_name}完成！(耗时 {elapsed}秒)")
                    return result

                elif status == 'FAILED':
                    error_msg = result.get('errorMessage', '未知错误')
                    if progress_callback:
                        progress_callback(f"❌ {task_name}失败: {error_msg}")
                    return result

                # 根据已等待时间调整检查间隔
                if elapsed < 30:
                    sleep_time = 3  # 前30秒每3秒检查一次
                elif elapsed < 120:
                    sleep_time = 5  # 前2分钟每5秒检查一次
                else:
                    sleep_time = 10  # 之后每10秒检查一次

                time.sleep(sleep_time)

            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ 检查状态出错: {str(e)}")
                time.sleep(5)

        if progress_callback:
            progress_callback(f"⏱️ {task_name}超时 (超过{max_wait}秒)")

        return None

    def download_results(
        self,
        task_result: Dict,
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """
        下载生成结果

        Args:
            task_result: 任务结果
            progress_callback: 进度回调

        Returns:
            下载的文件路径列表
        """
        downloaded_files = []

        try:
            results = task_result.get('results', [])

            if not results:
                return downloaded_files

            save_dir = Path("results")
            save_dir.mkdir(exist_ok=True)

            for idx, item in enumerate(results):
                image_url = item.get('url')
                if not image_url:
                    continue

                output_type = item.get('outputType', 'png')
                save_path = save_dir / f"banner_{int(time.time())}_{idx}.{output_type}"

                if progress_callback:
                    progress_callback(f"下载结果 {idx + 1}/{len(results)}...")

                response = httpx.get(image_url, timeout=120.0)  # 下载大文件,增加到120秒
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)

                    downloaded_files.append(str(save_path))

                    if progress_callback:
                        progress_callback(f"已保存: {save_path}")

            return downloaded_files

        except Exception as e:
            print(f"下载结果出错: {str(e)}")
            return downloaded_files

    async def generate_complete_flow(
        self,
        product_image_path: str,
        prompt: str,
        logo_path: Optional[str] = None,
        enable_cutout: bool = True,
        cutout_prompt: str = "只保留产品主体",
        aspect_ratio: str = "9:21",
        resolution: str = "2k",
        num_images: int = 5,  # 新增: 生成数量,默认5张
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        完整生成流程

        Args:
            product_image_path: 产品图路径
            prompt: 生成提示词
            logo_path: Logo路径（可选）
            enable_cutout: 是否启用抠图
            cutout_prompt: 抠图提示词
            aspect_ratio: 宽高比
            resolution: 分辨率
            progress_callback: 进度回调

        Returns:
            {
                "success": bool,
                "task_id": str,
                "result_files": List[str],
                "error": str
            }
        """
        try:
            # 1. 上传原始图片
            if progress_callback:
                progress_callback("上传产品图片...")

            upload_result = self.upload_image(product_image_path)
            if not upload_result:
                return {"success": False, "error": "上传图片失败"}

            file_name, download_url = upload_result

            # 2. 抠图（可选）
            final_image_path = product_image_path
            if enable_cutout:
                cutout_path = self.cutout_product(file_name, cutout_prompt, progress_callback)
                if cutout_path:
                    final_image_path = cutout_path

            # 3. 合成Logo（可选）
            if logo_path and Path(logo_path).exists():
                composed_path = self.compose_with_logo(final_image_path, logo_path, progress_callback)
                if composed_path:
                    # 上传合成后的图片
                    if progress_callback:
                        progress_callback("上传合成后的图片...")

                    upload_result = self.upload_image(composed_path)
                    if upload_result:
                        _, image_url = upload_result
                    else:
                        image_url = download_url
                else:
                    image_url = download_url
            else:
                image_url = download_url

            # 4. 并发生成多张易拉宝
            if progress_callback:
                progress_callback(f"开始生成 {num_images} 张易拉宝...")

            # 同时提交多个任务
            task_ids = []
            for i in range(num_images):
                task_id = self.generate_banner(image_url, prompt, aspect_ratio, resolution, None)
                if task_id:
                    task_ids.append(task_id)
                    if progress_callback:
                        progress_callback(f"已提交任务 {i+1}/{num_images}: {task_id}")

            if not task_ids:
                return {"success": False, "error": "所有生成任务提交失败"}

            # 5. 并行等待所有任务完成
            all_result_files = []
            for idx, task_id in enumerate(task_ids):
                if progress_callback:
                    progress_callback(f"等待任务 {idx+1}/{len(task_ids)} 完成...")

                result = self._wait_for_completion(
                    task_id,
                    f"易拉宝生成 {idx+1}/{len(task_ids)}",
                    progress_callback=progress_callback
                )

                if result and result.get('status') == 'SUCCESS':
                    # 6. 下载结果
                    result_files = self.download_results(result, progress_callback)
                    all_result_files.extend(result_files)
                else:
                    if progress_callback:
                        error_msg = result.get('errorMessage', '未知错误') if result else '任务超时'
                        progress_callback(f"⚠️ 任务 {idx+1} 失败: {error_msg}")

            if not all_result_files:
                return {"success": False, "error": "所有生成任务都失败了"}

            return {
                "success": True,
                "task_ids": task_ids,
                "result_files": all_result_files,
                "error": None
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
