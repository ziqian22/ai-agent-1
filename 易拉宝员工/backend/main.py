"""
易拉宝设计助手 - FastAPI 后端
简化版本：移除复杂状态机，让 Claude 自己控制对话流程
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import anthropic
import os
import json
import uuid
import base64
from pathlib import Path
from datetime import datetime
import sys

# 添加父目录到路径，以便导入现有模块
sys.path.append(str(Path(__file__).parent.parent))

from vision_analyzer import VisionAnalyzer
from banner_generator import BannerGenerator
from banner_prompt_template import generate_banner_prompt
from knowledge_base import KnowledgeBase
from logo_library_manager import logo_library
from conversation_state import get_style_preset  # 添加这个导入

app = FastAPI(title="易拉宝设计助手 API")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录 - 用于访问生成的图片
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)
app.mount("/results", StaticFiles(directory="results"), name="results")

# 挂载知识库文件目录 - 用于访问知识库图片
knowledge_base_dir = Path("knowledge_base")
knowledge_base_dir.mkdir(exist_ok=True)
app.mount("/knowledge_base", StaticFiles(directory="knowledge_base"), name="knowledge_base")

# 挂载 Logo 库目录 - 用于访问 Logo 图片
# Logo 库在项目根目录，需要使用绝对路径
logo_library_dir = Path(__file__).parent.parent / "logo_library"
logo_library_dir.mkdir(exist_ok=True)
app.mount("/logo_library", StaticFiles(directory=str(logo_library_dir)), name="logo_library")

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 初始化客户端
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL")
RUNNINGHUB_API_KEY = os.getenv("RUNNINGHUB_API_KEY")

if not CLAUDE_API_KEY or not RUNNINGHUB_API_KEY:
    raise ValueError("请设置 CLAUDE_API_KEY 和 RUNNINGHUB_API_KEY 环境变量")

# 初始化工具
vision_analyzer = VisionAnalyzer(CLAUDE_API_KEY, CLAUDE_BASE_URL)
banner_generator = BannerGenerator(RUNNINGHUB_API_KEY)
knowledge_base = KnowledgeBase()  # 初始化知识库

# 初始化 Claude 客户端（用于 Logo 分析）
if CLAUDE_BASE_URL:
    claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY, base_url=CLAUDE_BASE_URL)
else:
    claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# 对话历史存储（生产环境建议用 Redis）
conversations: Dict[str, Dict[str, Any]] = {}

# 生成记录存储文件
GENERATION_HISTORY_FILE = Path("generation_history.json")

# 加载生成记录
def load_generation_history() -> List[Dict[str, Any]]:
    """从文件加载生成记录"""
    if GENERATION_HISTORY_FILE.exists():
        try:
            with open(GENERATION_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载生成记录失败: {str(e)}")
            return []
    return []

# 保存生成记录
def save_generation_history(history: List[Dict[str, Any]]):
    """保存生成记录到文件"""
    try:
        print(f"[DEBUG] 开始保存生成记录,共 {len(history)} 条")
        with open(GENERATION_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] 生成记录保存成功: {GENERATION_HISTORY_FILE}")
    except Exception as e:
        print(f"[ERROR] 保存生成记录失败: {str(e)}")
        import traceback
        traceback.print_exc()

# 生成记录存储
generation_history: List[Dict[str, Any]] = load_generation_history()

# System Prompt
SYSTEM_PROMPT = """你是易拉宝设计助手,一个真正的 AI Agent。

你的核心职责:
帮助用户收集生成易拉宝所需的信息,并在信息完整后调用 API 生成易拉宝。

生成易拉宝需要的信息:
【必需】
- 产品图片 (用户会上传)
- 产品名称
- 品牌名称

【建议收集】
- 核心卖点/Slogan
- 产品特点 (3-6个)
- 适用场景
- 设计风格：系统提供6种预设风格,**向用户介绍风格时必须列出所有6种**
  1. 科技感 - 现代、智能、清爽
  2. 简约商务 - 高端、克制、精致
  3. 自然清新 - 健康、环保、舒适
  4. 时尚活力 - 活力、年轻、创新
  5. 高端奢华 - 高端、奢华、尊贵
  6. 具体场景 - 真实场景、生活化

  **关于"具体场景"风格**：
  这是一种真实场景风格,需要用户描述具体的使用场景。
  建议场景包括:
  • 商务办公室：现代商务办公室，简约办公桌，落地窗，城市景观
  • 北欧家居：北欧风格客厅，简约家具，绿植点缀，木质地板
  • 温馨家居：温馨家庭厨房或餐厅，暖色调装饰，生活气息

  用户也可以自己描述想要的场景环境(如咖啡厅、健身房、户外等)。
  当用户选择"具体场景"风格时,你需要询问用户想要什么场景,并可以推荐上述3个预设场景。

- 主色调

你的工作方式:
1. 用户上传文件后,系统会自动分析并提取信息
2. 你要主动向用户展示分析结果,并询问如何使用这些信息
3. 通过自然对话收集缺失的信息
4. 用户可以随时补充新的图片、文档或文字描述
5. 信息收集完成后,向用户展示信息摘要并**等待用户明确确认**

重要原则:
- 主动分析用户上传的文件,提取有用信息
- 向用户展示分析结果,询问是否正确,如何使用
- 不要机械地按顺序收集信息,要根据对话自然进行
- 用户可能上传产品图、参考图、文档资料,要灵活处理
- 保持对话自然流畅,像真人助手一样

如何处理用户上传的文件:
- 系统会自动分析文件并提取信息
- 你会收到分析结果
- 你要向用户展示分析结果,并询问:
  "请问您上传这个文件是想:
   1. 作为产品图,使用这些产品信息?
   2. 作为参考图,借鉴其中的设计风格?
   3. 还是其他用途?"
- 根据用户的回答,决定如何使用这些信息

⚠️ 重要：生成易拉宝的确认流程（必须严格遵守）:

第1步 - 展示信息摘要:
当信息收集完成后,你必须向用户展示完整的信息摘要,格式如下:

```
✅ 信息收集完成

让我确认一下收集到的信息:
- **产品名称**: XXX
- **品牌**: XXX
- **核心卖点**: XXX
- **产品特点**:
  1. XXX
  2. XXX
  3. XXX
- **适用场景**: XXX
- **设计风格**: XXX
- **主色调**: XXX
- **生成数量**: X张

请确认以上信息是否正确？如需修改请告诉我。
确认无误后,请点击"开始生成"按钮,我将为您生成易拉宝。
```

第2步 - 等待用户确认:
- **绝对不要**在展示摘要后立即输出 [GENERATE_BANNER]
- **必须等待**用户明确回复"确认"、"开始生成"、"没问题"等确认词语
- 如果用户提出修改,先修改信息,再重新展示摘要
- 只有在用户明确确认后,才能进入第3步

第3步 - 输出生成指令:
只有在用户明确确认后,才输出:

[GENERATE_BANNER]
{
  "product_name": "产品名称",
  "brand": "品牌名称",
  "slogan": "核心卖点",
  "features": ["特点1", "特点2", "特点3"],
  "scenes": ["场景1", "场景2"],
  "style": "科技感",
  "main_colors": "蓝色+白色",
  "num_images": 5
}
[/GENERATE_BANNER]

注意:
- num_images 是生成数量,默认5张
- 如果用户明确说要生成几张(如"生成3张"、"给我10张"),就使用用户指定的数量
- 如果用户没有说,就用默认值5

❌ 禁止行为:
- 禁止在展示信息摘要的同时输出 [GENERATE_BANNER]
- 禁止在用户未确认的情况下输出 [GENERATE_BANNER]
- 禁止跳过信息摘要直接生成

记住: 你是 Agent,要主动理解用户意图,灵活收集信息,但**必须等待用户明确确认后才能开始生成**。
"""

# 数据模型
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    type: str  # "message" | "generating" | "result"
    content: Optional[str] = None
    images: Optional[List[str]] = None
    progress: Optional[int] = None

class UploadResponse(BaseModel):
    session_id: str
    analysis: str
    product_info: Dict[str, Any]


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "message": "易拉宝设计助手 API"}


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
                extracted_images = result.get('images', [])
                if extracted_images:
                    new_product_image = extracted_images[0]
                else:
                    new_product_image = str(file_path)
            else:
                # 图片分析
                file_analysis = vision_analyzer.analyze_image(str(file_path))
                new_product_image = str(file_path)

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

            # ✅ 关键修复: 更新 session 中的产品信息和图片
            # 当用户上传新产品图片时,应该替换旧的产品信息
            session["product_info"] = file_analysis
            session["product_image"] = new_product_image
            session["file_path"] = str(file_path)

            print(f"[DEBUG] 更新 session 产品信息: {file_analysis.get('product_name', '未命名')}")
            print(f"[DEBUG] 更新 session 产品图片: {new_product_image}")

            return UploadResponse(
                session_id=session_id,
                analysis=analysis_text,
                product_info=file_analysis  # ✅ 返回新的产品信息
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
                    print(f"[DEBUG] 保存到知识库: {product_info.get('product_name', '未命名')}")
                    product_id = knowledge_base.add_product(
                        product_info=product_info,
                        image_path=product_image if product_image else str(file_path),
                        logo_path=None
                    )
                    conversations[session_id]["product_id"] = product_id
                    print(f"[DEBUG] 知识库保存成功, product_id: {product_id}")
                except Exception as e:
                    print(f"[ERROR] 保存到知识库失败: {str(e)}")
                    import traceback
                    traceback.print_exc()

            return UploadResponse(
                session_id=session_id,
                analysis=analysis_text,
                product_info=product_info
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件分析失败: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    处理对话
    """
    try:
        session_id = request.session_id
        user_message = request.message

        # 检查 session 是否存在
        if session_id not in conversations:
            raise HTTPException(status_code=404, detail="会话不存在，请先上传文件")

        session = conversations[session_id]
        history = session["history"]

        # 添加用户消息
        history.append({
            "role": "user",
            "content": user_message
        })

        # 调用 Claude
        if CLAUDE_BASE_URL:
            client = anthropic.Anthropic(api_key=CLAUDE_API_KEY, base_url=CLAUDE_BASE_URL)
            model = "claude-opus-4-7"
        else:
            client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
            model = "claude-opus-4-20250514"

        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=history
        )

        assistant_message = response.content[0].text

        # 添加助手回复
        history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # 检查是否需要生成易拉宝
        if "[GENERATE_BANNER]" in assistant_message:
            # 提取 JSON
            try:
                start = assistant_message.find("[GENERATE_BANNER]") + len("[GENERATE_BANNER]")
                end = assistant_message.find("[/GENERATE_BANNER]")
                json_str = assistant_message[start:end].strip()

                generation_params = json.loads(json_str)

                # 合并产品信息
                product_info = session["product_info"]
                product_info.update(generation_params)

                # 获取风格配置（如果有的话）
                style_config = None
                if "style" in generation_params:
                    style_name = generation_params.get("style")
                    style_config = get_style_preset(style_name)

                # 生成提示词（传入style_config）
                prompt = generate_banner_prompt(product_info, style_config)

                # 获取产品图片
                product_image = session.get("product_image")
                if not product_image:
                    return ChatResponse(
                        type="message",
                        content="抱歉，没有找到产品图片，无法生成易拉宝。请重新上传包含产品图片的文件。"
                    )

                # 获取生成数量（默认5张）
                num_images = generation_params.get("num_images", 5)
                # 确保数量在合理范围内（1-10张）
                num_images = max(1, min(10, num_images))

                # 调用生成 API
                print(f"[DEBUG] 开始生成易拉宝:")
                print(f"  - 产品图片: {product_image}")
                print(f"  - 生成数量: {num_images}")
                print(f"  - 提示词长度: {len(prompt)} 字符")

                result = await banner_generator.generate_complete_flow(
                    product_image_path=product_image,
                    prompt=prompt,
                    logo_path=None,
                    enable_cutout=True,
                    cutout_prompt=f"只保留{product_info.get('product_type', '产品')}主体",
                    aspect_ratio="9:21",
                    resolution="2k",
                    num_images=num_images
                )

                print(f"[DEBUG] 生成结果: success={result.get('success')}, error={result.get('error')}")

                if result["success"]:
                    # 转换本地文件路径为 URL
                    result_files = result["result_files"]

                    # 自动为所有易拉宝添加 Logo（只分析第一张，其他都用相同的 Logo）
                    print(f"[INFO] 开始为 {len(result_files)} 张易拉宝自动添加 Logo...")
                    final_image_urls = []
                    all_logos = logo_library.get_all_logos()

                    # 只分析第一张易拉宝
                    if len(result_files) > 0:
                        try:
                            print(f"[INFO] 分析第一张易拉宝以确定 Logo...")
                            first_banner = result_files[0]
                            analysis = analyze_banner_with_vision(first_banner, all_logos)
                            recommended_logo_id = analysis["recommended_logo"]["id"]
                            recommended_position = analysis["recommended_logo"]["position"]
                            recommended_size = analysis["recommended_logo"]["size_ratio"]

                            print(f"[INFO] 推荐 Logo: {recommended_logo_id}, 位置: {recommended_position}")
                            print(f"[INFO] 将为所有 {len(result_files)} 张易拉宝使用相同的 Logo")

                            # 获取 Logo 信息
                            logo_info = logo_library.get_logo_by_id(recommended_logo_id)
                            if not logo_info:
                                print(f"[WARNING] Logo {recommended_logo_id} 不存在，跳过 Logo 添加")
                                # 如果 Logo 不存在，所有图片都使用原图
                                for file_path in result_files:
                                    file_name = Path(file_path).name
                                    image_url = f"http://localhost:8000/results/{file_name}"
                                    final_image_urls.append(image_url)
                            else:
                                logo_path = logo_library.get_logo_path(recommended_logo_id)

                                # 为每张易拉宝添加相同的 Logo
                                from PIL import Image

                                for idx, file_path in enumerate(result_files):
                                    try:
                                        print(f"[INFO] 处理第 {idx+1}/{len(result_files)} 张易拉宝...")

                                        banner = Image.open(file_path).convert("RGBA")
                                        logo = Image.open(logo_path).convert("RGBA")

                                        # 计算 Logo 尺寸
                                        logo_width = int(banner.width * recommended_size)
                                        logo_height = int(logo.height * (logo_width / logo.width))
                                        logo_resized = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

                                        # 计算位置
                                        placement_rules = logo_library.get_placement_rules()
                                        margin_top = placement_rules["safeMarginTop"]
                                        margin_side = placement_rules["safeMarginSide"]

                                        if recommended_position == "左上角":
                                            logo_pos = (margin_side, margin_top)
                                        else:  # 右上角
                                            logo_pos = (banner.width - logo_width - margin_side, margin_top)

                                        # 合成
                                        banner.paste(logo_resized, logo_pos, logo_resized)

                                        # 保存（覆盖原文件）
                                        banner.save(file_path, "PNG")

                                        print(f"[INFO] ✅ Logo 合成完成: {Path(file_path).name}")

                                        # 生成 URL
                                        file_name = Path(file_path).name
                                        image_url = f"http://localhost:8000/results/{file_name}"
                                        final_image_urls.append(image_url)

                                    except Exception as e:
                                        print(f"[ERROR] 为易拉宝 {idx+1} 添加 Logo 失败: {str(e)}")
                                        # 如果失败，使用原图
                                        file_name = Path(file_path).name
                                        image_url = f"http://localhost:8000/results/{file_name}"
                                        final_image_urls.append(image_url)

                        except Exception as e:
                            print(f"[ERROR] 分析 Logo 失败: {str(e)}")
                            # 如果分析失败，所有图片都使用原图
                            for file_path in result_files:
                                file_name = Path(file_path).name
                                image_url = f"http://localhost:8000/results/{file_name}"
                                final_image_urls.append(image_url)

                    print(f"[INFO] ✅ 所有易拉宝 Logo 添加完成")

                    # 保存到生成记录
                    generation_record = {
                        "id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "product_name": product_info.get("product_name", "未命名产品"),
                        "brand": product_info.get("brand", ""),
                        "style": generation_params.get("style", ""),
                        "image_urls": final_image_urls,
                        "local_files": result_files,
                        "created_at": datetime.now().isoformat()
                    }
                    print(f"[DEBUG] 添加生成记录: {generation_record['id']}")
                    generation_history.append(generation_record)

                    # 持久化到文件
                    print(f"[DEBUG] 调用 save_generation_history(), 当前记录数: {len(generation_history)}")
                    save_generation_history(generation_history)

                    # 如果有关联的知识库产品,添加生成记录
                    product_id = session.get("product_id")
                    if product_id:
                        try:
                            knowledge_base.add_generation_record(
                                product_id=product_id,
                                style_name=generation_params.get("style", ""),
                                result_files=result_files,
                                user_rating=None
                            )
                        except Exception as e:
                            print(f"添加知识库生成记录失败: {str(e)}")

                    # 返回生成结果
                    return ChatResponse(
                        type="result",
                        content="✅ 易拉宝生成完成！已自动为每张图片添加合适的 Logo。",
                        images=final_image_urls
                    )
                else:
                    error_detail = result.get("error", "未知错误")
                    print(f"[ERROR] 生成失败: {error_detail}")

                    return ChatResponse(
                        type="message",
                        content=f"生成失败：{error_detail}\n\n可能的原因:\n1. API 配额不足\n2. 网络连接问题\n3. 图片处理失败\n\n请检查后台日志获取详细信息。"
                    )

            except json.JSONDecodeError as e:
                return ChatResponse(
                    type="message",
                    content=f"解析生成参数失败，请重新确认信息。错误：{str(e)}"
                )
            except Exception as e:
                return ChatResponse(
                    type="message",
                    content=f"生成易拉宝时出错：{str(e)}"
                )

        # 普通对话回复
        return ChatResponse(
            type="message",
            content=assistant_message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """获取会话信息"""
    if session_id not in conversations:
        raise HTTPException(status_code=404, detail="会话不存在")

    session = conversations[session_id]
    return {
        "session_id": session_id,
        "product_info": session.get("product_info"),
        "message_count": len(session.get("history", []))
    }


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    if session_id in conversations:
        del conversations[session_id]
        return {"message": "会话已删除"}
    raise HTTPException(status_code=404, detail="会话不存在")


# ==================== 知识库 API ====================

@app.get("/api/knowledge-base/products")
async def get_products():
    """获取所有产品"""
    try:
        products = knowledge_base.get_all_products()

        # 转换图片路径为 URL
        for product in products:
            if product.get("image_path"):
                image_path = product["image_path"]
                # 只在路径不包含 http:// 时才添加前缀
                if not image_path.startswith("http://") and not image_path.startswith("https://"):
                    # 将反斜杠转换为正斜杠
                    image_path = image_path.replace("\\", "/")
                    product["image_path"] = f"http://localhost:8000/{image_path}"

            if product.get("logo_path"):
                logo_path = product["logo_path"]
                # 只在路径不包含 http:// 时才添加前缀
                if not logo_path.startswith("http://") and not logo_path.startswith("https://"):
                    # 将反斜杠转换为正斜杠
                    logo_path = logo_path.replace("\\", "/")
                    product["logo_path"] = f"http://localhost:8000/{logo_path}"

        return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取产品列表失败: {str(e)}")


@app.get("/api/knowledge-base/products/{product_id}")
async def get_product(product_id: str):
    """获取单个产品"""
    try:
        product = knowledge_base.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="产品不存在")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取产品失败: {str(e)}")


@app.post("/api/knowledge-base/products")
async def add_product(
    product_name: str = Form(...),
    brand: str = Form(...),
    product_type: str = Form(""),
    features: str = Form(""),  # 逗号分隔
    scenes: str = Form(""),  # 逗号分隔
    image: UploadFile = File(...),
    logo: UploadFile = File(None)
):
    """添加产品到知识库"""
    try:
        # 保存上传的图片
        upload_dir = Path("temp_uploads")
        upload_dir.mkdir(exist_ok=True)

        image_path = upload_dir / f"{uuid.uuid4()}_{image.filename}"
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)

        logo_path = None
        if logo:
            logo_path = upload_dir / f"{uuid.uuid4()}_{logo.filename}"
            with open(logo_path, "wb") as f:
                content = await logo.read()
                f.write(content)

        # 构建产品信息
        product_info = {
            "product_name": product_name,
            "brand": brand,
            "product_type": product_type,
            "features": [f.strip() for f in features.split(',') if f.strip()],
            "scenes": [s.strip() for s in scenes.split(',') if s.strip()]
        }

        # 添加到知识库
        product_id = knowledge_base.add_product(
            product_info=product_info,
            image_path=str(image_path),
            logo_path=str(logo_path) if logo_path else None
        )

        return {"product_id": product_id, "message": "产品添加成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加产品失败: {str(e)}")


@app.put("/api/knowledge-base/products/{product_id}")
async def update_product(product_id: str, product_info: Dict[str, Any]):
    """更新产品信息"""
    try:
        success = knowledge_base.update_product(product_id, product_info)
        if not success:
            raise HTTPException(status_code=404, detail="产品不存在")
        return {"success": True, "message": "产品更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新产品失败: {str(e)}")


@app.delete("/api/knowledge-base/products/{product_id}")
async def delete_product(product_id: str):
    """删除产品"""
    try:
        success = knowledge_base.delete_product(product_id)
        if not success:
            raise HTTPException(status_code=404, detail="产品不存在")
        return {"success": True, "message": "产品删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除产品失败: {str(e)}")


@app.get("/api/knowledge-base/search")
async def search_products(keyword: str):
    """搜索产品"""
    try:
        products = knowledge_base.search_products(keyword)
        return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索产品失败: {str(e)}")


@app.get("/api/knowledge-base/statistics")
async def get_statistics():
    """获取统计信息"""
    try:
        stats = knowledge_base.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@app.post("/api/knowledge-base/products/{product_id}/use")
async def use_product(product_id: str):
    """使用知识库产品开始对话"""
    try:
        product = knowledge_base.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="产品不存在")

        # 创建新会话
        session_id = str(uuid.uuid4())

        # 构建产品信息描述
        product_info = product["product_info"]

        # 获取图片路径
        image_path = product.get("image_path")
        if not image_path:
            raise HTTPException(status_code=404, detail="产品没有图片")

        # 如果路径是 URL 格式，提取本地路径部分
        if image_path.startswith("http://") or image_path.startswith("https://"):
            # URL 格式: http://localhost:8000/knowledge_base/files/product_xxx/product.png
            # 提取: knowledge_base/files/product_xxx/product.png
            image_path = image_path.split("localhost:8000/")[-1]
            print(f"[DEBUG] 从 URL 提取路径: {image_path}")

        # 转换为绝对路径（使用后端目录作为基准）
        backend_dir = Path(__file__).parent
        image_path_obj = Path(image_path)
        if not image_path_obj.is_absolute():
            # 相对路径，基于后端目录解析
            image_path = str(backend_dir / image_path)

        # 检查文件是否存在
        if not Path(image_path).exists():
            print(f"[ERROR] 产品图片不存在: {image_path}")
            print(f"[DEBUG] 后端目录: {backend_dir}")
            print(f"[DEBUG] 原始路径: {product.get('image_path')}")
            raise HTTPException(status_code=404, detail=f"产品图片不存在: {image_path}")

        print(f"[DEBUG] 产品图片路径: {image_path}")

        # 构建用户消息 - 模拟用户从知识库选择了产品
        user_message = f"""[用户从知识库选择了产品]

产品信息：
- 产品名称: {product_info.get('product_name', '未知')}
- 品牌: {product_info.get('brand', '未知')}
- 产品类型: {product_info.get('product_type', '未知')}
- 核心卖点: {product_info.get('slogan', '未提供')}
- 产品特点: {', '.join(product_info.get('features', []))}
- 适用场景: {', '.join(product_info.get('scenes', []))}

产品图片已准备好。"""

        # 初始化对话历史
        conversations[session_id] = {
            "history": [
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "product_info": product_info,
            "product_image": image_path,  # 使用绝对路径
            "file_path": image_path,  # 使用绝对路径
            "product_id": product_id  # 关联知识库产品ID
        }

        print(f"[DEBUG] 创建会话 {session_id}, 产品图片: {image_path}")

        # 调用 Claude 生成初始回复
        if CLAUDE_BASE_URL:
            client = anthropic.Anthropic(api_key=CLAUDE_API_KEY, base_url=CLAUDE_BASE_URL)
            model = "claude-opus-4-7"
        else:
            client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
            model = "claude-opus-4-20250514"

        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=conversations[session_id]["history"]
        )

        initial_message = response.content[0].text

        # 添加 assistant 回复到历史
        conversations[session_id]["history"].append({
            "role": "assistant",
            "content": initial_message
        })

        return {
            "session_id": session_id,
            "product_info": product_info,
            "message": initial_message
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"使用产品失败: {str(e)}")


# ==================== 生成记录 API ====================

@app.get("/api/generation-history")
async def get_generation_history():
    """获取生成记录"""
    try:
        # 按时间倒序排列
        sorted_history = sorted(
            generation_history,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        return {"history": sorted_history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取生成记录失败: {str(e)}")


@app.delete("/api/generation-history/{record_id}")
async def delete_generation_record(record_id: str):
    """删除生成记录"""
    try:
        global generation_history
        generation_history = [r for r in generation_history if r.get("id") != record_id]

        # 持久化到文件
        save_generation_history(generation_history)

        return {"success": True, "message": "记录删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除记录失败: {str(e)}")


@app.get("/api/download-image")
async def download_image(url: str):
    """下载图片（代理下载，解决跨域问题）"""
    try:
        # 从 URL 中提取本地文件路径
        # URL 格式: http://localhost:8000/results/banner_xxx.png
        if url.startswith("http://localhost:8000/"):
            file_path = url.replace("http://localhost:8000/", "")
        else:
            file_path = url

        # 转换为绝对路径（使用后端目录作为基准）
        backend_dir = Path(__file__).parent
        full_path = Path(file_path)
        if not full_path.is_absolute():
            full_path = backend_dir / file_path

        # 检查文件是否存在
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        # 返回文件
        return FileResponse(
            path=str(full_path),
            media_type="image/png",
            filename=full_path.name
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


# ==================== Logo 相关 API ====================

@app.get("/api/logo-library")
async def get_logo_library():
    """获取 Logo 库信息"""
    try:
        return {
            "brand": logo_library.metadata["brand"],
            "logos": logo_library.get_all_logos(),
            "placementRules": logo_library.get_placement_rules(),
            "usageGuidelines": logo_library.get_usage_guidelines()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Logo 库失败: {str(e)}")


class AnalyzeBannersRequest(BaseModel):
    """分析易拉宝请求"""
    banner_urls: List[str]


@app.post("/api/analyze-banners-for-logo")
async def analyze_banners_for_logo(request: AnalyzeBannersRequest):
    """
    分析多张易拉宝，为每张推荐最合适的 Logo
    """
    try:
        banner_urls = request.banner_urls
        recommendations = []

        # 获取所有 Logo 信息
        all_logos = logo_library.get_all_logos()

        # 为每张易拉宝分析并推荐 Logo
        for banner_url in banner_urls:
            # 下载易拉宝图片
            if banner_url.startswith("http://localhost:8000/"):
                file_path = banner_url.replace("http://localhost:8000/", "")
            else:
                file_path = banner_url

            full_path = Path.cwd() / file_path

            if not full_path.exists():
                recommendations.append({
                    "banner_url": banner_url,
                    "error": "文件不存在"
                })
                continue

            # 使用 Claude Vision 分析易拉宝
            analysis = analyze_banner_with_vision(str(full_path), all_logos)

            recommendations.append({
                "banner_url": banner_url,
                "analysis": analysis["style_analysis"],
                "recommended_logo": analysis["recommended_logo"],
                "reason": analysis["reason"]
            })

        return {"recommendations": recommendations}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


def analyze_banner_with_vision(banner_path: str, logo_library_data: List[Dict]) -> Dict:
    """使用 Claude Vision 分析易拉宝并推荐 Logo"""

    # 读取易拉宝图片
    with open(banner_path, "rb") as f:
        banner_base64 = base64.b64encode(f.read()).decode()

    # 构建 Prompt
    prompt = f"""
请分析这张易拉宝的设计风格，并从以下 Logo 库中推荐最合适的一个：

## Logo 库
{json.dumps(logo_library_data, ensure_ascii=False, indent=2)}

请分析：
1. 易拉宝的主色调和配色方案
2. 设计风格（科技感/简约商务/自然清新/时尚活力/高端奢华）
3. 布局特点（产品位置、文字分布、背景颜色）
4. 推荐最合适的 Logo（ID）
5. 推荐的位置（左上角/右上角）
6. 推荐理由（50字以内）

请以 JSON 格式返回：
{{
  "style_analysis": {{
    "primary_color": "#RRGGBB",
    "style": "风格名称",
    "layout": "布局描述",
    "background_type": "light/dark/white/black"
  }},
  "recommended_logo": {{
    "id": "logo_id",
    "position": "位置",
    "size_ratio": 0.25
  }},
  "reason": "推荐理由"
}}
"""

    # 调用 Claude Vision（同步调用）
    # 根据配置选择模型
    if CLAUDE_BASE_URL:
        model = "claude-opus-4-7"
    else:
        model = "claude-3-5-sonnet-20241022"

    response = claude_client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": banner_base64
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }]
    )

    # 解析响应
    result_text = response.content[0].text

    # 尝试提取 JSON
    import re
    json_match = re.search(r'\{[\s\S]*\}', result_text)
    if json_match:
        result = json.loads(json_match.group())
    else:
        # 如果没有找到 JSON，返回默认推荐
        result = {
            "style_analysis": {
                "primary_color": "#0078D7",
                "style": "科技感",
                "layout": "标准布局",
                "background_type": "light"
            },
            "recommended_logo": {
                "id": "pudow-expert-color",
                "position": "右上角",
                "size_ratio": 0.25
            },
            "reason": "默认推荐"
        }

    return result


class ComposeLogoRequest(BaseModel):
    """合成 Logo 请求"""
    banner_url: str
    logo_id: str
    position: str = "右上角"
    size_ratio: Optional[float] = None


@app.post("/api/compose-logo")
async def compose_logo(request: ComposeLogoRequest):
    """
    将选定的 Logo 合成到易拉宝上
    """
    try:
        banner_url = request.banner_url
        logo_id = request.logo_id
        position = request.position
        size_ratio = request.size_ratio

        # 获取易拉宝文件路径
        if banner_url.startswith("http://localhost:8000/"):
            banner_path = banner_url.replace("http://localhost:8000/", "")
        else:
            banner_path = banner_url

        full_banner_path = Path.cwd() / banner_path

        if not full_banner_path.exists():
            raise HTTPException(status_code=404, detail="易拉宝文件不存在")

        # 获取 Logo 信息
        logo_info = logo_library.get_logo_by_id(logo_id)
        if not logo_info:
            raise HTTPException(status_code=404, detail="Logo 不存在")

        logo_path = logo_library.get_logo_path(logo_id)

        # 如果没有指定尺寸，使用推荐尺寸
        if size_ratio is None:
            size_ratio = logo_info["sizeRecommendation"]["preferredWidthRatio"]

        # 合成 Logo
        from PIL import Image

        # 打开图片
        banner = Image.open(str(full_banner_path)).convert("RGBA")
        logo = Image.open(logo_path).convert("RGBA")

        # 计算 Logo 尺寸
        logo_width = int(banner.width * size_ratio)
        logo_height = int(logo.height * (logo_width / logo.width))
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

        # 计算位置
        placement_rules = logo_library.get_placement_rules()
        margin = placement_rules["safeMarginSide"]

        position_map = {
            "左上角": (margin, placement_rules["safeMarginTop"]),
            "右上角": (banner.width - logo_width - margin, placement_rules["safeMarginTop"])
        }

        logo_pos = position_map.get(position, position_map["右上角"])

        # 合成
        banner.paste(logo, logo_pos, logo)

        # 保存
        output_filename = f"final_banner_{uuid.uuid4().hex}.png"
        output_path = results_dir / output_filename
        banner.save(str(output_path), "PNG")

        # 返回最终图片 URL
        final_url = f"http://localhost:8000/results/{output_filename}"

        return {
            "final_url": final_url,
            "logo_info": {
                "id": logo_id,
                "name": logo_info["displayName"],
                "position": position,
                "size_ratio": size_ratio
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合成失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=900,  # 15分钟 - 保持连接活跃时间
        timeout_graceful_shutdown=30  # 30秒 - 优雅关闭超时
    )
