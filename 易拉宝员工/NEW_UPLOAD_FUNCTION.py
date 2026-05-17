# 新的上传接口实现
# 替换 backend/main.py 中的 upload_file 函数

@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    save_to_kb: str = Form("false"),
    session_id: str = Form(None)  # 新增: 可选的 session_id
):
    """
    上传文件
    支持：图片（PNG/JPG）、文档（PDF/Word/PPT）
    参数：
        file: 上传的文件
        save_to_kb: 是否保存到知识库（默认 "false"）
        session_id: 可选,如果提供则在现有对话中追加,否则创建新对话
    """
    try:
        # 转换字符串为布尔值
        save_to_kb_bool = save_to_kb.lower() == "true"

        # 检查是否使用现有 session
        use_existing_session = session_id and session_id in conversations

        if not use_existing_session:
            # 创建新 session
            session_id = str(uuid.uuid4())

        # 保存文件
        upload_dir = Path("temp_uploads")
        upload_dir.mkdir(exist_ok=True)

        file_path = upload_dir / f"{session_id}_{file.filename}"

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 检测文件类型
        file_ext = file_path.suffix.lower()

        if use_existing_session:
            # 在现有对话中追加文件
            session = conversations[session_id]

            # 添加用户消息: 上传了文件
            session["history"].append({
                "role": "user",
                "content": f"[用户上传了文件: {file.filename}]"
            })

            # 分析文件内容
            if file_ext in ['.pdf', '.docx', '.doc', '.pptx', '.ppt']:
                # 文档分析
                result = vision_analyzer.analyze_document(str(file_path))
                file_analysis = result['product_info']
            else:
                # 图片分析
                file_analysis = vision_analyzer.analyze_image(str(file_path))

            # 构建分析结果消息,让 Claude 询问用户如何使用这些信息
            analysis_text = f"""我分析了您上传的文件 {file.filename},提取到以下信息:

**产品名称**: {file_analysis.get('product_name', '未识别')}
**品牌**: {file_analysis.get('brand', '未识别')}
**核心卖点**: {file_analysis.get('slogan', '未识别')}
**产品特点**: {', '.join(file_analysis.get('features', [])[:3])}
**适用场景**: {', '.join(file_analysis.get('scenes', []))}

请问您上传这个文件是想:
1. 作为产品图,使用这些产品信息?
2. 作为参考图,借鉴其中的设计风格?
3. 还是其他用途?

请告诉我您的想法。"""

            session["history"].append({
                "role": "assistant",
                "content": analysis_text
            })

            # 保存文件路径和分析结果供后续使用
            if "uploaded_files" not in session:
                session["uploaded_files"] = []
            session["uploaded_files"].append({
                "path": str(file_path),
                "filename": file.filename,
                "type": file_ext,
                "analysis": file_analysis
            })

            return UploadResponse(
                session_id=session_id,
                analysis=analysis_text,
                product_info=session.get("product_info", {})
            )

        else:
            # 创建新对话 - 第一次上传,自动分析
            if file_ext in ['.pdf', '.docx', '.doc', '.pptx', '.ppt']:
                # 文档分析
                result = vision_analyzer.analyze_document(str(file_path))
                product_info = result['product_info']
                extracted_images = result.get('images', [])

                if extracted_images:
                    product_image = extracted_images[0]
                else:
                    product_image = None
            else:
                # 图片分析
                product_info = vision_analyzer.analyze_image(str(file_path))
                product_image = str(file_path)
                extracted_images = []

            # 初始化对话
            conversations[session_id] = {
                "history": [],
                "product_info": product_info,
                "product_image": product_image,
                "extracted_images": extracted_images,
                "file_path": str(file_path),
                "uploaded_files": [{
                    "path": str(file_path),
                    "filename": file.filename,
                    "type": file_ext
                }]
            }

            # 生成分析结果消息
            analysis_text = f"""我已经分析了您上传的文件，识别到以下产品信息：

**产品名称**：{product_info.get('product_name', '未识别')}
**品牌**：{product_info.get('brand', '未识别')}
**核心卖点**：{product_info.get('slogan', '未识别')}
**产品特点**：
{chr(10).join(f'- {f}' for f in product_info.get('features', [])[:5])}
**适用场景**：{', '.join(product_info.get('scenes', []))}

请确认以上信息是否准确？如需修改请告诉我。"""

            # 添加到对话历史
            conversations[session_id]["history"].append({
                "role": "assistant",
                "content": analysis_text
            })

            # 如果需要保存到知识库
            product_id = None
            if save_to_kb_bool:
                try:
                    product_id = knowledge_base.add_product(
                        product_info=product_info,
                        image_path=product_image if product_image else str(file_path),
                        logo_path=None
                    )
                    conversations[session_id]["product_id"] = product_id
                except Exception as e:
                    print(f"保存到知识库失败: {str(e)}")

            return UploadResponse(
                session_id=session_id,
                analysis=analysis_text,
                product_info=product_info
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件分析失败: {str(e)}")
