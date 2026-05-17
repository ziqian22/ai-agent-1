"""
修改agent_orchestrator.py的_start_generation函数
支持多风格生成
"""

# 在_start_generation函数开始处添加以下逻辑：

async def _start_generation(self) -> Dict[str, Any]:
    """开始生成易拉宝（支持单一风格和多风格）"""
    try:
        self.progress_tracker.start_step(TaskStep.GENERATE_PROMPT)

        product_info = self.context.product_info
        image_path = self.context.uploaded_files[0]

        # 进度回调函数
        def progress_callback(message: str):
            self.progress_tracker.add_log(message)

        # 根据生成模式选择不同的生成策略
        generation_mode = self.context.generation_mode or "single_style_multi"

        if generation_mode == "single_style_multi":
            # 单一风格多方案
            style_config = self.context.style_config

            prompt_data = {
                **product_info,
                "style": style_config.get("atmosphere", "专业、现代"),
                "main_colors": style_config.get("colors", "蓝色+白色")
            }

            base_prompt = generate_banner_prompt(prompt_data)
            count = self.context.generation_count or 5

            self.progress_tracker.complete_step(TaskStep.GENERATE_PROMPT)
            self.progress_tracker.start_step(TaskStep.CALL_API)

            # 调用并行生成（单一风格）
            results = await self.parallel_generator.generate_multiple_variants(
                product_image_path=image_path,
                base_prompt=base_prompt,
                logo_path=self.context.logo_path,
                count=count,
                enable_cutout=True,
                cutout_prompt=f"只保留{product_info.get('product_type', '产品')}",
                aspect_ratio="9:21",
                resolution="2k",
                progress_callback=progress_callback
            )

        else:
            # 多风格对比 或 混合模式
            selected_styles = self.context.selected_styles or []

            if not selected_styles:
                return {
                    "message": "错误：未选择风格",
                    "state": ConversationState.WELCOME.value,
                    "quick_actions": []
                }

            # 为每个风格生成提示词
            prompts_with_styles = []
            count_per_style = self.context.generation_count or 1

            for style_name in selected_styles:
                style_config = get_style_preset(style_name)
                if not style_config:
                    continue

                prompt_data = {
                    **product_info,
                    "style": style_config.get("atmosphere", "专业、现代"),
                    "main_colors": style_config.get("colors", "蓝色+白色")
                }

                prompt = generate_banner_prompt(prompt_data)
                prompts_with_styles.append((prompt, style_name, count_per_style))

            self.progress_tracker.complete_step(TaskStep.GENERATE_PROMPT)
            self.progress_tracker.start_step(TaskStep.CALL_API)

            # 调用并行生成（多风格）
            results = await self.parallel_generator.generate_multiple_styles(
                product_image_path=image_path,
                prompts_with_styles=prompts_with_styles,
                logo_path=self.context.logo_path,
                enable_cutout=True,
                cutout_prompt=f"只保留{product_info.get('product_type', '产品')}",
                aspect_ratio="9:21",
                resolution="2k",
                progress_callback=progress_callback
            )

        self.progress_tracker.complete_step(TaskStep.CALL_API)
        self.progress_tracker.start_step(TaskStep.PROCESS_RESULT)

        # 筛选成功的结果
        success_results = [r for r in results if r.get("success")]

        # 检查成功数量（至少3张）
        if len(success_results) < 3:
            error_msg = f"生成失败过多，仅成功{len(success_results)}张（需要至少3张）"
            self.progress_tracker.add_log(error_msg, "error")

            return {
                "message": f"抱歉，生成过程中遇到问题。{error_msg}\n\n请重试或联系技术支持。",
                "state": ConversationState.WELCOME.value,
                "quick_actions": [
                    {"label": "🔄 重新生成", "value": "retry"},
                    {"label": "🏠 返回首页", "value": "home"}
                ]
            }

        # 保存所有成功的结果
        for result in success_results:
            for file_path in result.get("result_files", []):
                self.context.add_result({
                    "file_path": file_path,
                    "task_id": result.get("task_id"),
                    "url": file_path,
                    "index": result.get("index"),
                    "style_name": result.get("style_name", "未知风格")
                })

        self.progress_tracker.complete_step(TaskStep.PROCESS_RESULT)

        # 切换到展示结果状态
        self.context.state = ConversationState.SHOW_RESULTS

        # 保存到知识库（如果用户选择保存）
        if self.knowledge_base and self.context.save_to_kb and not self.context.current_product_id:
            try:
                product_id = self.knowledge_base.add_product(
                    product_info=self.context.product_info,
                    image_path=self.context.uploaded_files[0] if self.context.uploaded_files else None,
                    logo_path=self.context.logo_path
                )
                self.context.current_product_id = product_id
                self.progress_tracker.add_log(f"✅ 已保存到知识库: {product_id}")
            except Exception as e:
                self.progress_tracker.add_log(f"⚠️ 保存到知识库失败: {str(e)}", "warning")

        # 保存到知识库历史记录
        if self.knowledge_base and self.context.current_product_id:
            all_result_files = []
            for result in success_results:
                all_result_files.extend(result.get("result_files", []))

            style_names = list(set([r.get("style_name", "N/A") for r in success_results]))
            style_text = "、".join(style_names)

            self.knowledge_base.add_generation_record(
                product_id=self.context.current_product_id,
                style_name=style_text,
                result_files=all_result_files,
                user_rating=None
            )

        return {
            "message": f"生成完成！共生成{len(success_results)}张易拉宝供您选择。",
            "state": self.context.state.value,
            "results": self.context.results,
            "quick_actions": [
                {"label": "👍 满意", "value": "satisfied"},
                {"label": "🔄 重新生成", "value": "regenerate"},
                {"label": "✏️ 调整参数", "value": "adjust"}
            ]
        }

    except Exception as e:
        self.progress_tracker.add_log(f"生成失败: {str(e)}", "error")

        return {
            "message": f"抱歉，生成过程中出错了：{str(e)}\n\n请重试或联系技术支持。",
            "state": ConversationState.WELCOME.value,
            "quick_actions": [
                {"label": "🔄 重试", "value": "retry"},
                {"label": "🏠 返回首页", "value": "home"}
            ]
        }
