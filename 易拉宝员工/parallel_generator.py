"""
并行易拉宝生成器
支持同时生成多张易拉宝，提升生成效率
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from PIL import Image


class GenerationProgress:
    """生成进度追踪器"""

    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.success_count = 0
        self.failed_count = 0
        self.results = []
        self.start_time = time.time()

    def update(self, result: Dict[str, Any]):
        """更新进度"""
        self.completed += 1
        if result.get("success"):
            self.success_count += 1
        else:
            self.failed_count += 1
        self.results.append(result)

    def get_progress_message(self) -> str:
        """获取进度消息"""
        progress_pct = (self.completed / self.total) * 100
        elapsed = int(time.time() - self.start_time)
        return f"生成进度: {progress_pct:.0f}% ({self.completed}/{self.total}) - 成功{self.success_count}张 - 已用时{elapsed}秒"

    def get_summary(self) -> str:
        """获取总结"""
        elapsed = int(time.time() - self.start_time)
        return f"生成完成！共{self.success_count}张成功，{self.failed_count}张失败，总耗时{elapsed}秒"


class ParallelBannerGenerator:
    """并行易拉宝生成器"""

    def __init__(self, banner_generator, max_workers: int = 5):
        """
        初始化并行生成器

        Args:
            banner_generator: BannerGenerator实例
            max_workers: 最大并发数
        """
        self.banner_generator = banner_generator
        self.max_workers = max_workers

    def generate_variant_prompts(self, base_prompt: str, count: int) -> List[str]:
        """
        生成变体提示词

        Args:
            base_prompt: 基础提示词
            count: 生成数量

        Returns:
            变体提示词列表
        """
        variants = []
        for i in range(count):
            variant_suffix = f"\n\n设计变体{i+1}: 在保持整体风格的基础上，探索不同的布局细节、色彩搭配和艺术元素设计。"
            variants.append(base_prompt + variant_suffix)
        return variants

    def _generate_single_banner(
        self,
        product_image_path: str,
        prompt: str,
        logo_path: Optional[str],
        index: int,
        enable_cutout: bool,
        cutout_prompt: str,
        aspect_ratio: str,
        resolution: str
    ) -> Dict[str, Any]:
        """
        生成单张易拉宝（同步方法，用于线程池）

        Args:
            product_image_path: 产品图路径
            prompt: 提示词
            logo_path: Logo路径
            index: 索引
            enable_cutout: 是否抠图
            cutout_prompt: 抠图提示词
            aspect_ratio: 宽高比
            resolution: 分辨率

        Returns:
            生成结果
        """
        try:
            start_time = time.time()

            # 1. 上传产品图
            upload_result = self.banner_generator.upload_image(product_image_path)
            if not upload_result:
                return {
                    "success": False,
                    "index": index,
                    "error": "上传图片失败"
                }

            file_name, download_url = upload_result

            # 2. 抠图（可选）
            final_image_url = download_url
            if enable_cutout:
                cutout_path = self.banner_generator.cutout_product(file_name, cutout_prompt)
                if cutout_path:
                    # 重新上传抠图结果
                    cutout_upload = self.banner_generator.upload_image(cutout_path)
                    if cutout_upload:
                        _, final_image_url = cutout_upload

            # 3. 生成易拉宝（不含Logo）
            task_id = self.banner_generator.generate_banner(
                final_image_url,
                prompt,
                aspect_ratio,
                resolution
            )

            if not task_id:
                return {
                    "success": False,
                    "index": index,
                    "error": "提交生成任务失败"
                }

            # 4. 等待生成完成
            result = self.banner_generator._wait_for_completion(task_id, f"易拉宝{index+1}")

            if not result or result.get('status') != 'SUCCESS':
                error_msg = result.get('errorMessage', '生成失败') if result else '任务超时'
                return {
                    "success": False,
                    "index": index,
                    "task_id": task_id,
                    "error": error_msg
                }

            # 5. 下载结果
            result_files = self.banner_generator.download_results(result)

            if not result_files:
                return {
                    "success": False,
                    "index": index,
                    "task_id": task_id,
                    "error": "下载结果失败"
                }

            # 6. Logo拼接（如果提供了Logo）
            final_files = []
            if logo_path and Path(logo_path).exists():
                for result_file in result_files:
                    final_file = self._compose_logo_after_generation(
                        result_file,
                        logo_path
                    )
                    if final_file:
                        final_files.append(final_file)
                    else:
                        final_files.append(result_file)  # 拼接失败，使用原图
            else:
                final_files = result_files

            elapsed = time.time() - start_time

            return {
                "success": True,
                "index": index,
                "task_id": task_id,
                "result_files": final_files,
                "elapsed": elapsed
            }

        except Exception as e:
            return {
                "success": False,
                "index": index,
                "error": str(e)
            }

    def _compose_logo_after_generation(
        self,
        banner_image_path: str,
        logo_path: str,
        top_margin_cm: float = 1.0
    ) -> Optional[str]:
        """
        在生成的易拉宝上拼接Logo

        Args:
            banner_image_path: 易拉宝图片路径
            logo_path: Logo路径
            top_margin_cm: 顶部边距(厘米)，左右无边距

        Returns:
            拼接后的图片路径
        """
        try:
            # 打开易拉宝图片
            banner = Image.open(banner_image_path).convert("RGB")
            banner_width, banner_height = banner.size

            # 打开Logo
            logo = Image.open(logo_path).convert("RGBA")

            # 计算Logo尺寸 (约为宽度的15%)
            logo_width = int(banner_width * 0.15)
            logo_height = int(logo.height * (logo_width / logo.width))
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            # 计算顶部边距像素 (1cm ≈ banner_height/200)
            top_margin_px = int((banner_height / 200) * top_margin_cm)

            # 计算位置 (右上角，左右无边距，顶部1cm边距)
            # 右侧紧贴边缘，只留少量视觉间距（约2%宽度）
            visual_padding = int(banner_width * 0.02)
            logo_x = banner_width - logo_width - visual_padding
            logo_y = top_margin_px

            # 转换为RGBA以支持透明度
            banner_rgba = banner.convert("RGBA")

            # 粘贴Logo
            banner_rgba.paste(logo, (logo_x, logo_y), logo)

            # 转回RGB
            final_banner = banner_rgba.convert("RGB")

            # 保存
            save_dir = Path("results")
            save_dir.mkdir(exist_ok=True)
            output_path = save_dir / f"final_{Path(banner_image_path).stem}_{int(time.time())}.png"
            final_banner.save(output_path, "PNG")

            return str(output_path)

        except Exception as e:
            print(f"Logo拼接失败: {str(e)}")
            return None

    async def generate_multiple_variants(
        self,
        product_image_path: str,
        base_prompt: str,
        logo_path: Optional[str],
        count: int = 5,
        enable_cutout: bool = True,
        cutout_prompt: str = "只保留产品主体",
        aspect_ratio: str = "9:21",
        resolution: str = "2k",
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        并行生成多个设计变体（单一风格）

        Args:
            product_image_path: 产品图路径
            base_prompt: 基础提示词
            logo_path: Logo路径
            count: 生成数量
            enable_cutout: 是否抠图
            cutout_prompt: 抠图提示词
            aspect_ratio: 宽高比
            resolution: 分辨率
            progress_callback: 进度回调

        Returns:
            生成结果列表
        """
        # 生成变体提示词
        variant_prompts = self.generate_variant_prompts(base_prompt, count)

        # 创建进度追踪器
        progress = GenerationProgress(count)

        if progress_callback:
            progress_callback(f"开始并行生成{count}张易拉宝...")

        # 并行执行
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = {
                executor.submit(
                    self._generate_single_banner,
                    product_image_path,
                    prompt,
                    logo_path,
                    idx,
                    enable_cutout,
                    cutout_prompt,
                    aspect_ratio,
                    resolution
                ): idx
                for idx, prompt in enumerate(variant_prompts)
            }

            # 收集结果
            for future in as_completed(futures):
                result = future.result()
                progress.update(result)
                results.append(result)

                # 进度回调
                if progress_callback:
                    if result.get("success"):
                        progress_callback(
                            f"[OK] 易拉宝{result['index']+1} 生成成功 ({result.get('elapsed', 0):.1f}秒)"
                        )
                    else:
                        progress_callback(
                            f"[ERROR] 易拉宝{result['index']+1} 生成失败: {result.get('error', '未知错误')}"
                        )

                    progress_callback(progress.get_progress_message())

        # 按index排序
        results.sort(key=lambda x: x.get("index", 0))

        if progress_callback:
            progress_callback(progress.get_summary())

        return results

    async def generate_multiple_styles(
        self,
        product_image_path: str,
        prompts_with_styles: List[tuple],  # [(prompt, style_name, count), ...]
        logo_path: Optional[str],
        enable_cutout: bool = True,
        cutout_prompt: str = "只保留产品主体",
        aspect_ratio: str = "9:21",
        resolution: str = "2k",
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        并行生成多种风格的易拉宝

        Args:
            product_image_path: 产品图路径
            prompts_with_styles: [(提示词, 风格名称, 每种风格生成数量), ...]
            logo_path: Logo路径
            enable_cutout: 是否抠图
            cutout_prompt: 抠图提示词
            aspect_ratio: 宽高比
            resolution: 分辨率
            progress_callback: 进度回调

        Returns:
            生成结果列表
        """
        # 展开所有任务
        all_tasks = []
        task_index = 0

        for prompt, style_name, count in prompts_with_styles:
            for i in range(count):
                # 为每个任务添加变体标识，确保生成不同的设计
                if count > 1:
                    # 如果同一风格生成多张，添加变体后缀
                    variant_prompt = prompt + f"\n\n设计变体{i+1}: 在保持{style_name}风格的基础上，探索不同的布局细节、色彩搭配和艺术元素设计。"
                else:
                    # 如果每种风格只生成1张，添加风格强调
                    variant_prompt = prompt + f"\n\n重要提示: 请严格按照{style_name}风格的特征进行设计，确保风格特色鲜明。"

                all_tasks.append((variant_prompt, style_name, task_index))
                task_index += 1

        total_count = len(all_tasks)

        # 创建进度追踪器
        progress = GenerationProgress(total_count)

        if progress_callback:
            progress_callback(f"开始并行生成{total_count}张易拉宝（{len(prompts_with_styles)}种风格）...")

        # 并行执行
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = {
                executor.submit(
                    self._generate_single_banner,
                    product_image_path,
                    prompt,
                    logo_path,
                    idx,
                    enable_cutout,
                    cutout_prompt,
                    aspect_ratio,
                    resolution
                ): (idx, style_name)
                for prompt, style_name, idx in all_tasks
            }

            # 收集结果
            for future in as_completed(futures):
                idx, style_name = futures[future]
                result = future.result()
                result["style_name"] = style_name  # 添加风格名称
                progress.update(result)
                results.append(result)

                # 进度回调
                if progress_callback:
                    if result.get("success"):
                        progress_callback(
                            f"[OK] {style_name} 易拉宝{result['index']+1} 生成成功 ({result.get('elapsed', 0):.1f}秒)"
                        )
                    else:
                        progress_callback(
                            f"[ERROR] {style_name} 易拉宝{result['index']+1} 生成失败: {result.get('error', '未知错误')}"
                        )

                    progress_callback(progress.get_progress_message())

        # 按index排序
        results.sort(key=lambda x: x.get("index", 0))

        if progress_callback:
            progress_callback(progress.get_summary())

        return results
