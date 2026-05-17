# 易拉宝AI Agent 完整架构规划

## Context (需求背景)

用户需要构建一个完整的易拉宝AI Agent,实现以下流程:

**输入**: 一张包含产品图和产品介绍文字的图片(如示例图片所示)

**处理流程**:
1. 自动从图片中提取产品图像(image)
2. 自动从图片中提取产品介绍文字(text)
3. 根据提取的信息生成易拉宝设计prompt
4. 调用API生成易拉宝
5. 输出多张易拉宝设计供用户选择

**输出**: 多张80x200cm尺寸的易拉宝设计图

**当前状态**:
- 已完成阶段一: Running Hub工作流测试工具
- 发现了合适的API: `rhart-image-g-2/image-to-image`
- 但还未测试该API的实际效果

---

## 完整架构设计

### 整体流程图

```
用户上传图片
    ↓
[1] Claude Vision 分析图片
    ├─ 提取产品图像区域
    ├─ 识别产品介绍文字
    └─ 理解产品特点
    ↓
[2] 智能对话收集需求
    ├─ 询问设计风格
    ├─ 询问使用场景
    └─ 确认尺寸要求
    ↓
[3] 生成易拉宝Prompt
    ├─ 结合产品信息
    ├─ 结合用户需求
    └─ 优化为专业prompt
    ↓
[4] 调用Running Hub API
    ├─ 上传产品图
    ├─ 提交生成任务
    └─ 轮询获取结果
    ↓
[5] 展示多张设计
    ├─ 用户评分
    ├─ 选择下载
    └─ 或要求重新生成
```

---

## 技术架构

### 核心模块

#### Module 1: 图像分析模块 (Claude Vision)

**文件**: `backend/image_analyzer.py`

**功能**:
- 使用Claude Sonnet 4.6的Vision能力分析上传的图片
- 识别图片中的产品区域
- 提取产品介绍文字(OCR)
- 理解产品特点和卖点

**输入**: 用户上传的产品宣传图
**输出**: 结构化的产品信息
```json
{
  "product_name": "爵士H5智能直饮机",
  "product_features": [
    "35L大容量热罐",
    "3温出水设计",
    "压缩机制冷",
    "折叠式纳米晶须前置过滤"
  ],
  "product_description": "世出名门·内外兼修，大流量出水，有冰水更沁爽",
  "use_scenarios": ["科技", "互联网", "金融", "外企等办公场所"],
  "technical_specs": {
    "产品型号": "HS005",
    "产品尺寸": "495*520*1625mm"
  }
}
```

**Claude Vision Prompt示例**:
```
分析这张产品宣传图片,提取以下信息:

1. 产品图像位置: 识别图片中产品的位置和区域
2. 产品名称: 从文字中提取产品名称
3. 产品特点: 列出所有产品卖点和特性
4. 产品描述: 提取主要的宣传语
5. 使用场景: 识别适用场景
6. 技术参数: 提取所有技术规格

以JSON格式返回,确保信息完整准确。
```

---

#### Module 2: 对话管理模块

**文件**: `backend/conversation_manager.py`

**功能**:
- 管理与用户的对话流程
- 收集用户对易拉宝设计的需求
- 确认和调整生成参数

**对话流程**:
```
1. 欢迎 → "您好!我是易拉宝设计助手"
2. 上传图片 → "请上传包含产品信息的图片"
3. 分析确认 → "我识别到产品是XXX,信息正确吗?"
4. 收集需求 → "您希望什么风格的易拉宝?"
   - 设计风格: 简约/科技/商务/活泼
   - 主色调: 蓝色/红色/绿色/品牌色
   - 使用场景: 展会/门店/活动
5. 生成确认 → "我将为您生成3张易拉宝设计"
6. 展示结果 → "这是生成的设计,您觉得如何?"
7. 反馈循环 → "需要调整吗?或生成更多?"
```

---

#### Module 3: Prompt生成模块 (核心模块)

**文件**: `backend/prompt_generator.py`

**功能**:
- 将产品信息和用户需求转换为专业的生成prompt
- 根据产品类型自动匹配合适场景
- 根据风格自适应光影效果
- 确保生成符合印刷标准的易拉宝

**用户需求确认**:
- ✅ 风格选择: 支持预设风格 + 自由描述
- ✅ 场景融合: 根据产品类型自动匹配具体场景
- ✅ 文字处理: 提取原始信息 + AI优化表达
- ✅ 安全边距: 标准印刷安全边(上下左右各3-5cm)
- ✅ 光影风格: 根据选择的风格自适应光影效果
- ✅ 产品呈现: 产品聚焦清晰 + 背景虚化烘托
- ✅ 布局结构: 三段式布局(顶部品牌+中部产品+底部特点)
- ✅ 生成数量: 一次生成多张不同效果

**预设风格库**:
```python
STYLE_PRESETS = {
    "科技感": {
        "scene_keywords": "现代科技办公空间,简约玻璃幕墙,智能设备环境",
        "lighting": "冷色调LED灯光,蓝白色光效,科技感光线",
        "color_scheme": "蓝色+白色+灰色,科技蓝主色调",
        "atmosphere": "专业、现代、智能、高效"
    },
    "简约商务": {
        "scene_keywords": "高端商务办公室,大理石台面,极简空间",
        "lighting": "柔和自然光,45度角斜射,明暗对比克制",
        "color_scheme": "黑白灰+品牌色,低饱和度配色",
        "atmosphere": "专业、高端、克制、精致"
    },
    "自然清新": {
        "scene_keywords": "自然采光空间,绿植环境,木质元素",
        "lighting": "温暖自然光,柔和漫射,清晨或午后光线",
        "color_scheme": "绿色+白色+原木色,清新自然",
        "atmosphere": "健康、环保、舒适、亲和"
    },
    "时尚活力": {
        "scene_keywords": "年轻活力空间,色彩丰富,现代设计感",
        "lighting": "明亮活泼光线,多彩光效,动感光影",
        "color_scheme": "鲜艳色彩,高饱和度,撞色搭配",
        "atmosphere": "活力、年轻、创新、潮流"
    },
    "高端奢华": {
        "scene_keywords": "奢华空间,金属质感,高级材质",
        "lighting": "戏剧性光影,聚光灯效果,金色暖光",
        "color_scheme": "金色+黑色+深色系,奢华配色",
        "atmosphere": "高端、奢华、尊贵、品质"
    }
}
```

**产品类型场景映射**:
```python
PRODUCT_SCENE_MAPPING = {
    "饮水机": {
        "办公": "现代办公室茶水间,下午3点的自然光透过百叶窗,白领正在接水",
        "家居": "北欧风格厨房,大理石台面,清晨阳光洒在水杯上",
        "公共": "医院走廊休息区,干净明亮,医护人员路过"
    },
    "化妆品": {
        "梳妆台": "精致梳妆台,柔和灯光,镜面反射,化妆品整齐摆放",
        "浴室": "现代浴室,白色瓷砖,水汽氤氲,产品放在台面",
        "卧室": "温馨卧室,床头柜,暖色灯光,舒适氛围"
    },
    "电子产品": {
        "办公桌": "简约办公桌,MacBook旁边,科技感十足",
        "客厅": "现代客厅,电视柜,智能家居环境",
        "工作室": "创意工作室,多屏幕,专业设备环境"
    },
    "食品饮料": {
        "餐桌": "精致餐桌,自然光,美食摆盘,生活气息",
        "厨房": "现代厨房,料理台,烹饪场景",
        "户外": "野餐场景,草地,阳光,休闲氛围"
    }
}
```

**Prompt生成模板**:
```python
def generate_rollup_banner_prompt(
    product_info: dict,
    user_style: str,
    custom_style_desc: str = None
) -> str:
    """
    生成易拉宝设计prompt
    
    Args:
        product_info: 从图片提取的产品信息
            {
                "product_name": "产品名称",
                "brand": "品牌名",
                "features": ["特点1", "特点2", ...],
                "description": "产品描述",
                "product_type": "产品类型(饮水机/化妆品/电子产品等)"
            }
        user_style: 用户选择的风格("科技感"/"简约商务"等)
        custom_style_desc: 用户自定义风格描述(可选)
    
    Returns:
        优化后的prompt字符串
    """
    
    # 1. 获取风格配置
    if custom_style_desc:
        # 用户自定义风格
        style_config = parse_custom_style(custom_style_desc)
    else:
        # 使用预设风格
        style_config = STYLE_PRESETS.get(user_style, STYLE_PRESETS["简约商务"])
    
    # 2. 根据产品类型选择场景
    product_type = product_info.get("product_type", "通用产品")
    scene_mapping = PRODUCT_SCENE_MAPPING.get(product_type, {})
    
    # 选择最合适的场景(默认选第一个)
    scene_desc = list(scene_mapping.values())[0] if scene_mapping else "专业商业环境"
    
    # 3. 优化产品特点文案
    features_optimized = optimize_features_text(product_info["features"])
    
    # 4. 生成完整prompt
    prompt = f"""设计一张专业的商业易拉宝海报,严格遵循以下要求:

【尺寸与比例】
- 输出比例: 9:21 (最接近80cm×200cm易拉宝标准尺寸)
- 分辨率: 2K高清
- 安全边距: 上下左右各预留3-5cm安全边距,重要内容不得放置在边缘区域

【产品信息】
- 品牌: {product_info.get('brand', '')}
- 产品名称: {product_info['product_name']}
- 核心卖点: {product_info.get('description', '')}
- 产品特点: {features_optimized}

【场景与环境】
- 场景设定: {scene_desc}
- 场景处理: 产品清晰聚焦,背景适度虚化形成景深效果,突出产品主体
- 环境氛围: {style_config['atmosphere']}

【光影效果】
- 光线设计: {style_config['lighting']}
- 要求: 高级克制的光影处理,避免过度曝光,保持专业商业摄影质感

【色彩方案】
- 主色调: {style_config['color_scheme']}
- 要求: 色彩和谐统一,符合品牌调性,避免过度饱和

【布局结构 - 三段式】
顶部区域(占比15-20%):
- 品牌logo或名称
- 产品名称
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
5. 整体风格: {style_config['atmosphere']}
6. 符合印刷标准,预留出血位和安全边距

【禁止事项】
- 不要添加无关装饰元素
- 不要让背景喧宾夺主
- 不要将重要信息放在边缘
- 不要使用过于花哨的字体
- 不要让产品图片模糊或失焦

输出一张符合专业印刷标准的易拉宝设计,确保可以直接用于80cm×200cm尺寸的印刷制作。"""

    return prompt.strip()


def optimize_features_text(features: list) -> str:
    """
    优化产品特点文案
    
    提取核心信息,优化表达方式,保持简洁有力
    """
    optimized = []
    for feature in features[:5]:  # 最多5个特点
        # 提取关键词,优化表达
        # 例如: "35L大容量热罐" → "35L超大容量"
        optimized.append(feature)
    
    return " | ".join(optimized)


def parse_custom_style(custom_desc: str) -> dict:
    """
    解析用户自定义风格描述
    
    使用Claude API理解用户描述,转换为结构化配置
    """
    # 这里可以调用Claude API来理解用户的自然语言描述
    # 暂时返回默认配置
    return STYLE_PRESETS["简约商务"]
```

**多张生成策略**:
```python
def generate_multiple_prompts(product_info: dict, user_style: str, count: int = 3) -> list:
    """
    生成多个不同变体的prompt,用于一次生成多张设计
    
    策略:
    1. 主prompt: 严格按照用户选择的风格
    2. 变体1: 调整光影角度
    3. 变体2: 调整场景细节
    4. 变体3: 调整色彩饱和度
    """
    prompts = []
    
    # 主prompt
    main_prompt = generate_rollup_banner_prompt(product_info, user_style)
    prompts.append(main_prompt)
    
    # 生成变体
    if count > 1:
        # 变体1: 不同光影
        variant1 = main_prompt.replace(
            "45度角斜射",
            "顶部柔和漫射"
        )
        prompts.append(variant1)
    
    if count > 2:
        # 变体2: 不同场景细节
        variant2 = main_prompt.replace(
            "下午3点的自然光",
            "清晨8点的柔和光线"
        )
        prompts.append(variant2)
    
    return prompts[:count]
```

---

#### Module 4: API调用模块

**文件**: `backend/api_caller.py`

**功能**:
- 封装Running Hub API调用
- 支持多种API(工作流API和标准模型API)
- 处理图片上传、任务提交、结果获取

**关键方法**:
```python
class RollupBannerGenerator:
    def __init__(self, api_key):
        self.client = RunningHubClient(api_key)
    
    def generate_from_product_image(self, product_image_path, prompt, 
                                    aspect_ratio="2:5", resolution="2k"):
        """
        使用 image-to-image API 生成易拉宝
        
        Args:
            product_image_path: 产品图片路径
            prompt: 生成prompt
            aspect_ratio: 宽高比(2:5 对应 80:200)
            resolution: 分辨率
        
        Returns:
            生成的易拉宝图片URL列表
        """
        # 1. 上传产品图
        image_url = self.client.upload_image(product_image_path)
        
        # 2. 调用 image-to-image API
        task_id = self.client.start_standard_model(
            "rhart-image-g-2/image-to-image",
            {
                "prompt": prompt,
                "imageUrls": [image_url],
                "aspectRatio": aspect_ratio,
                "resolution": resolution
            }
        )
        
        # 3. 等待完成
        result = self.client.wait_for_completion(task_id)
        
        # 4. 返回结果
        return [r['url'] for r in result.get('results', [])]
```

---

#### Module 5: 结果管理模块

**文件**: `backend/result_manager.py`

**功能**:
- 管理生成的易拉宝结果
- 支持用户评分和反馈
- 根据反馈调整参数重新生成

---

## API选择建议

### 方案对比

#### 方案A: 使用 `rhart-image-g-2/image-to-image` (推荐)

**优点**:
- ✅ 直接支持图生图
- ✅ 可以自定义比例(2:5 = 80:200)
- ✅ prompt可以控制设计风格
- ✅ 可以要求生成文案

**缺点**:
- ⚠️ 还未测试实际效果
- ⚠️ 可能需要多次调整prompt才能达到理想效果

**适用场景**: 
- 需要基于产品图生成完整易拉宝
- 需要AI自动生成文案和布局

#### 方案B: 使用工作流API

**优点**:
- ✅ 可以精确控制每个节点
- ✅ 可以自定义工作流

**缺点**:
- ❌ 需要找到或创建合适的工作流
- ❌ 配置复杂

**适用场景**:
- 需要精确控制生成过程
- 有特定的设计模板

---

## 实施建议

### 阶段划分

#### 阶段一: API测试与验证 (当前阶段)

**目标**: 验证 `image-to-image` API是否适合易拉宝生成

**步骤**:
1. 使用 `test_standard_api.py` 测试API
2. 准备几张产品图
3. 尝试不同的prompt
4. 评估生成效果

**验证标准**:
- 能否生成2:5比例的图片
- 生成的易拉宝是否专业
- 文案是否合理
- 产品图是否突出

**如果效果好** → 进入阶段二
**如果效果不好** → 寻找其他工作流API

---

#### 阶段二: 集成Claude Vision

**目标**: 实现自动提取产品信息

**步骤**:
1. 集成Claude API
2. 实现图像分析功能
3. 测试信息提取准确性
4. 优化提取prompt

**关键文件**:
- `backend/image_analyzer.py` - 图像分析
- `backend/product_extractor.py` - 信息提取

---

#### 阶段三: 构建完整Agent

**目标**: 实现端到端的易拉宝生成流程

**步骤**:
1. 实现对话管理
2. 集成prompt生成
3. 连接API调用
4. 构建Web界面
5. 端到端测试

**关键文件**:
- `backend/agent.py` - 主Agent逻辑
- `backend/conversation_manager.py` - 对话管理
- `backend/prompt_generator.py` - Prompt生成
- `frontend/` - Web界面

---

## 项目目录结构(完整版)

```
易拉宝AI Agent/
├── backend/
│   ├── image_analyzer.py          # Claude Vision图像分析
│   ├── product_extractor.py       # 产品信息提取
│   ├── conversation_manager.py    # 对话管理
│   ├── prompt_generator.py        # Prompt生成
│   ├── api_caller.py              # API调用封装
│   ├── result_manager.py          # 结果管理
│   ├── agent.py                   # 主Agent逻辑
│   └── runninghub_client.py       # Running Hub客户端(已有)
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── AgentChat.tsx      # Agent对话界面
│   │   ├── components/
│   │   │   ├── ImageUploader.tsx  # 图片上传
│   │   │   ├── ChatInterface.tsx  # 对话界面
│   │   │   └── ResultGallery.tsx  # 结果展示
│   │   └── App.tsx
│   └── package.json
├── test_standard_api.py           # API测试脚本(已有)
├── config.py                      # 配置
├── .env                           # 环境变量
└── README.md
```

---

## 实施计划

### 阶段一: Prompt模板开发与测试 (优先级最高)

**目标**: 开发并验证Prompt生成模板的效果

**步骤**:

1. **创建 `prompt_generator.py`**
   - 实现风格预设库
   - 实现产品场景映射
   - 实现prompt生成函数
   - 实现多变体生成策略

2. **修改 `test_standard_api.py`**
   - 集成prompt_generator模块
   - 支持选择不同风格测试
   - 支持一次生成多张(调用API多次)

3. **测试不同风格效果**
   - 使用同一张产品图
   - 测试5种预设风格
   - 对比生成效果
   - 记录最佳实践

4. **优化Prompt模板**
   - 根据测试结果调整模板
   - 优化场景描述
   - 优化光影描述
   - 确保安全边距生效

**验证标准**:
- ✅ 生成的易拉宝比例正确(9:21)
- ✅ 产品清晰聚焦,背景虚化
- ✅ 三段式布局清晰
- ✅ 预留了安全边距
- ✅ 不同风格有明显差异
- ✅ 画面简约无多余装饰

---

### 阶段二: 集成Claude Vision (图像分析)

**目标**: 实现自动从产品图中提取信息

**步骤**:

1. **创建 `image_analyzer.py`**
   - 集成Claude API
   - 实现图像分析功能
   - 提取产品名称、特点、类型
   - 识别产品图像区域

2. **创建 `product_extractor.py`**
   - OCR文字提取
   - 产品类型识别
   - 信息结构化输出

3. **测试信息提取准确性**
   - 准备10张不同产品图
   - 测试提取准确率
   - 优化提取prompt

**验证标准**:
- ✅ 产品名称提取准确率>90%
- ✅ 产品特点提取完整
- ✅ 产品类型识别正确
- ✅ 处理时间<5秒

---

### 阶段三: 对话管理系统

**目标**: 实现与用户的智能对话

**步骤**:

1. **创建 `conversation_manager.py`**
   - 实现对话状态机
   - 实现风格选择对话
   - 实现信息确认对话
   - 实现反馈收集对话

2. **设计对话流程**
   ```
   1. 欢迎 → 引导上传图片
   2. 分析 → 展示提取的信息
   3. 确认 → 用户确认或修正
   4. 风格 → 选择预设或自定义
   5. 生成 → 显示进度
   6. 展示 → 多张结果
   7. 反馈 → 评分或重新生成
   ```

3. **实现风格选择界面**
   - 5个预设风格卡片
   - 自定义风格输入框
   - 风格预览示例

**验证标准**:
- ✅ 对话流程自然流畅
- ✅ 用户可以随时修正信息
- ✅ 风格选择直观易懂
- ✅ 支持中断和重新开始

---

### 阶段四: 完整Agent集成

**目标**: 将所有模块集成为完整的Agent

**步骤**:

1. **创建 `agent.py` (主控制器)**
   ```python
   class RollupBannerAgent:
       def __init__(self):
           self.image_analyzer = ImageAnalyzer()
           self.conversation_manager = ConversationManager()
           self.prompt_generator = PromptGenerator()
           self.api_caller = RollupBannerGenerator()
       
       async def process_user_input(self, user_message, image=None):
           # 主处理逻辑
           pass
   ```

2. **实现端到端流程**
   - 图片上传 → 分析
   - 信息确认 → 对话
   - 风格选择 → 生成
   - 结果展示 → 反馈

3. **构建Web界面**
   - 使用Streamlit或React
   - 聊天式交互界面
   - 图片上传组件
   - 结果展示画廊

**验证标准**:
- ✅ 端到端流程无缝衔接
- ✅ 用户体验流畅
- ✅ 错误处理完善
- ✅ 生成速度可接受(<2分钟)

---

### 阶段五: 优化与部署

**目标**: 优化性能,准备部署

**步骤**:

1. **性能优化**
   - 缓存已分析的产品信息
   - 并发生成多张图片
   - 优化API调用次数

2. **用户体验优化**
   - 添加生成进度提示
   - 支持历史记录
   - 支持收藏和分享

3. **部署准备**
   - Docker容器化
   - 环境变量配置
   - 日志和监控

---

## 验证计划

### 端到端测试流程

**测试场景1: 饮水机产品**
1. 上传饮水机产品图
2. Agent自动提取信息
3. 用户选择"科技感"风格
4. 生成3张易拉宝
5. 验证效果

**测试场景2: 化妆品产品**
1. 上传化妆品产品图
2. Agent自动提取信息
3. 用户选择"高端奢华"风格
4. 生成3张易拉宝
5. 验证效果

**测试场景3: 自定义风格**
1. 上传任意产品图
2. Agent自动提取信息
3. 用户自定义风格描述
4. 生成3张易拉宝
5. 验证效果

### 评估标准

**技术指标**:
- 信息提取准确率: >90%
- 生成成功率: >95%
- 平均生成时间: <2分钟
- 用户满意度: >80%

**设计质量**:
- 比例正确性: 100%
- 安全边距: 100%符合
- 产品突出度: 主观评分>4/5
- 设计专业度: 主观评分>4/5

---

## 下一步行动

### 立即开始 (当前任务)

1. **创建 `prompt_generator.py`**
   - 实现完整的prompt生成模板
   - 包含5种预设风格
   - 包含产品场景映射

2. **修改 `test_standard_api.py`**
   - 集成prompt_generator
   - 添加风格选择功能
   - 测试不同风格效果

3. **验证Prompt模板**
   - 使用现有的产品图测试
   - 对比不同风格的生成效果
   - 优化模板参数

### 后续规划

**如果Prompt模板效果好**:
→ 进入阶段二,集成Claude Vision

**如果需要调整**:
→ 继续优化Prompt模板,直到效果满意

---

## 关键技术点

### 1. Claude Vision 图像分析

**能力**:
- ✅ 识别图片中的产品
- ✅ 提取文字信息(OCR)
- ✅ 理解产品特点
- ✅ 分析使用场景

**限制**:
- 需要清晰的图片
- 复杂布局可能需要多次调整prompt

### 2. Prompt工程

**关键要素**:
- 明确的尺寸要求(80x200cm, 2:5比例)
- 详细的产品信息
- 清晰的设计风格描述
- 布局要求(顶部、中部、底部)

**优化策略**:
- 收集成功案例的prompt
- A/B测试不同prompt
- 根据用户反馈迭代

### 3. 多轮生成策略

**策略**:
- 首次生成: 3张不同风格
- 用户选择: 基于喜欢的风格
- 再次生成: 微调参数生成更多

---

## 成本估算

### API调用成本

**每次生成**:
- 图片上传: 免费
- Claude Vision分析: ~$0.01
- image-to-image生成: 根据Running Hub定价
- 总计: 需要查看Running Hub具体定价

**优化建议**:
- 缓存已分析的产品信息
- 批量生成减少调用次数

---

## 风险与应对

### 风险1: API效果不理想

**应对**:
- 准备备选方案(其他工作流)
- 考虑组合多个API
- 或自建工作流

### 风险2: 信息提取不准确

**应对**:
- 提供手动修正功能
- 优化Claude Vision prompt
- 收集反馈持续改进

### 风险3: 生成速度慢

**应对**:
- 异步处理
- 显示进度提示
- 允许用户继续其他操作

---

## 总结

**核心流程**: 图片 → Claude分析 → 对话收集 → 生成Prompt → API调用 → 多张结果

**关键决策点**: 先测试 `image-to-image` API效果

**建议**: 
1. 立即测试API
2. 根据效果决定后续方案
3. 逐步构建完整Agent

**预期效果**: 
用户只需上传一张产品宣传图,Agent自动完成分析、设计、生成,输出多张专业易拉宝设计。
