# 易拉宝AI Agent交互系统设计方案

## Context (背景)

用户已经完成了易拉宝生成的基础功能（抠图、Logo合成、API调用），现在需要构建一个**交互式Agent系统**，让用户只需上传一张产品宣传图，Agent就能自动完成：
1. 提取产品信息（图像+文字）
2. 通过对话收集设计需求
3. 生成易拉宝设计
4. 支持多轮优化

**核心需求**：
- 用户上传图片 → Agent自动识别产品信息
- Agent通过对话确认信息、收集风格偏好
- 自动生成多张易拉宝供选择
- 支持反馈和重新生成

**现有基础**：
- ✅ Running Hub API客户端（runninghub_client.py）
- ✅ 完整的生成流程（抠图→合成→生成）
- ✅ 提示词模板系统（banner_prompt_template.py）
- ✅ Streamlit Web界面（app.py）
- ✅ 测试记录系统（test_recorder.py）

---

## 核心需求确认（2024-05-16 更新）

基于用户最新反馈，明确以下关键需求：

### Agent能力范围（Claude Opus 4.7）
- ✅ **对话管理和流程控制** - 理解用户意图，引导完整流程
- ✅ **图片和文档分析** - 使用Vision能力分析图片、PDF、Word、PPT
- ✅ **提示词生成和优化** - 根据产品信息和用户需求生成专业提示词
- ✅ **反馈理解和参数调整** - 理解用户反馈，智能调整生成参数
- ✅ **主动提问** - 需要任何信息时及时向用户提问
- ✅ **意图确认** - 开始生成前进行用户意图确认

### API配置
- ✅ **支持中转API** - 用户使用Claude API中转服务
- ✅ **自定义配置** - 支持自定义base_url和api_key

### 知识库内容
- ✅ **原始文件** - 保存用户上传的图片、PDF、Word、PPT
- ✅ **结构化信息** - 产品名称、品牌、特点、场景等提取的数据
- ✅ **历史生成记录** - 该产品的历史易拉宝、使用的参数、用户评分

### 批量处理和风格选择
- ✅ **完整批量功能** - 支持选择多个产品
- ✅ **灵活风格设置** - 以用户需求为准：
  - 如果用户确定某一风格 → 生成多张同风格的变体
  - 如果用户未指定 → 可以为每个产品单独设置风格
- ✅ **并行生成** - 调研是否支持同时并行生成多张图片以节省时间

### 下载功能
- ✅ **单张下载** - 支持选择单独下载某一张图片
- ✅ **批量下载** - 支持一键下载所有图片
- ✅ **按产品分组下载** - 批量处理时按产品分组下载

### 交互方式
- ✅ **语音+文字输入** - 支持语音识别和文字输入
- ✅ **文件上传** - 支持从本地上传或从知识库导入
- ✅ **同步到知识库** - 本地上传时可选择是否保存到知识库

### 进度展示
- ✅ **步骤指示器** - 显示当前在哪一步
- ✅ **进度条+百分比** - 显示完成进度和预计时间
- ✅ **实时日志** - 显示详细执行日志
- ❌ **动画效果** - 不需要

---

### 方案概述

采用**对话式Agent + 工具调用**架构，基于现有Streamlit界面改造，集成Claude Vision和现有API客户端。

### 核心架构

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit 界面                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  图片上传区  │  │  对话显示区  │  │  结果展示区  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Agent 编排器                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  对话状态机 (Conversation State Machine)         │  │
│  │  - IMAGE_UPLOADED: 等待图片分析                  │  │
│  │  - CONFIRM_PRODUCT: 确认产品信息                 │  │
│  │  - COLLECT_STYLE: 收集设计风格                   │  │
│  │  - GENERATING: 生成中                            │  │
│  │  - SHOW_RESULTS: 展示结果                        │  │
│  │  - FEEDBACK: 收集反馈                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                     工具层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Claude Vision│  │ Prompt生成器 │  │ API客户端    │  │
│  │ 图像识别     │  │ 模板系统     │  │ Running Hub  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 图片处理器   │  │ 记录管理器   │  │ 配置管理器   │  │
│  │ Logo合成     │  │ 历史记录     │  │ 工作流配置   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 界面效果可视化

### 主界面布局

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│  易拉宝AI设计助手 🎨                                          [设置] [帮助] [退出]  │
├──────────────┬──────────────────────────────┬──────────────────┬───────────────────┤
│              │                              │                  │                   │
│  侧边栏      │         对话区               │   进度/结果区    │   知识库管理      │
│  (250px)     │         (flex)               │   (400px)        │   (弹出/标签)     │
│              │                              │                  │                   │
│ ┌──────────┐│ ┌──────────────────────────┐ │ ┌──────────────┐│ ┌───────────────┐ │
│ │📤 输入方式││ │ 💬 与AI助手对话          │ │ │📊 生成进度   ││ │📚 产品列表    │ │
│ │          ││ │                          │ │ │              ││ │               │ │
│ │○ 本地上传││ │ Agent: 您好！我是易拉宝  │ │ │✅ 分析图片   ││ │🔍 [搜索框]    │ │
│ │● 知识库  ││ │       设计助手...        │ │ │⏳ 生成提示词 ││ │               │ │
│ │          ││ │                          │ │ │⚪ 调用API    ││ │┌─────────────┐│ │
│ ├──────────┤│ │ User: 我想生成一个饮水机 │ │ │⚪ 处理结果   ││ ││产品A        ││ │
│ │📁 文件   ││ │       的易拉宝           │ │ │              ││ ││饮水机       ││ │
│ │          ││ │                          │ │ │━━━━━━━━━━━━━││ ││[图片]       ││ │
│ │[选择文件]││ │ Agent: 好的！请上传产品  │ │ │              ││ │└─────────────┘│ │
│ │          ││ │       图片或从知识库选择 │ │ │进度: 45%     ││ │               │ │
│ │☑ 同步到  ││ │                          │ │ │剩余: 1分30秒 ││ │┌─────────────┐│ │
│ │  知识库  ││ │ [科技感] [简约] [清新]   │ │ │              ││ ││产品B        ││ │
│ │          ││ │                          │ │ │━━━━━━━━━━━━━││ ││化妆品       ││ │
│ │[🚀开始]  ││ │                          │ │ │              ││ ││[图片]       ││ │
│ │          ││ │ ▼ 滚动查看更多对话       │ │ │📝 详细日志   ││ │└─────────────┘│ │
│ ├──────────┤│ │                          │ │ │[展开]        ││ │               │ │
│ │⚡ 快捷   ││ └──────────────────────────┘ │ └──────────────┘│ │[➕ 添加产品] │ │
│ │          ││ ┌──────────────────────────┐ │ ┌──────────────┐│ └───────────────┘ │
│ │[🔄重新]  ││ │ 💬 [输入框]        [🎤] │ │ │🎨 生成结果   ││                   │
│ │[📚知识库]││ └──────────────────────────┘ │ │              ││                   │
│ │          ││                              │ │┌────────────┐││                   │
│ └──────────┘│                              │ ││[图片1]     │││                   │
│              │                              │ ││            │││                   │
│              │                              │ ││[👍][💾][🔄]│││                   │
│              │                              │ │└────────────┘││                   │
│              │                              │ │┌────────────┐││                   │
│              │                              │ ││[图片2]     │││                   │
│              │                              │ ││            │││                   │
│              │                              │ ││[👍][💾][🔄]│││                   │
│              │                              │ │└────────────┘││                   │
│              │                              │ └──────────────┘│                   │
└──────────────┴──────────────────────────────┴──────────────────┴───────────────────┘
```

### 交互流程示意

#### 场景1：本地上传文件

```
用户操作                    界面反馈                      Agent响应
────────────────────────────────────────────────────────────────────
1. 点击"选择文件"
                          → 打开文件选择器
                            支持多选
                            
2. 选择产品图片/PDF
                          → 显示文件预览
                            显示文件信息
                            
3. 勾选"同步到知识库"
                          → 复选框选中
                          
4. 点击"🚀 开始分析"
                          → 进度区显示:
                            ✅ 上传文件
                            ⏳ 分析图片...
                            
                          → 对话区显示:
                            Agent: "正在分析您的产品图片..."
                            
                          → 30秒后
                            Agent: "我识别到以下产品信息：
                                   产品名称：勇士K6直饮机
                                   品牌：朴道健康水专家
                                   特点：
                                   - 125L/H开水量
                                   - 100℃持续出水
                                   ...
                                   
                                   信息正确吗？"
                            
                            [✅ 确认] [✏️ 修改] [🔄 重新分析]
                            
5. 点击"✅ 确认"
                          → Agent: "好的！请选择设计风格："
                            
                            [🔷 科技感] [💼 简约商务] 
                            [🌿 自然清新] [⚡ 时尚活力]
                            [👑 高端奢华]
                            
6. 点击"🔷 科技感"
                          → Agent: "明白了！我将为您生成3张
                                   【科技感】风格的易拉宝。
                                   
                                   预计需要1-2分钟..."
                            
                          → 进度区显示:
                            ✅ 分析图片
                            ✅ 生成提示词
                            ⏳ 调用API (45%)
                            ⚪ 处理结果
                            
                            进度条: ████████░░░░ 45%
                            剩余时间: 1分30秒
                            
                          → 实时日志:
                            [14:23:15] 开始生成...
                            [14:23:20] 上传产品图...
                            [14:23:25] 抠图处理中...
                            [14:24:10] 合成Logo...
                            [14:24:15] 调用生成API...
                            
7. 生成完成
                          → 进度区切换到结果区:
                            🎨 生成结果
                            
                            [图片1预览]
                            [👍 喜欢] [💾 下载] [🔄 重新生成]
                            
                            [图片2预览]
                            [👍 喜欢] [💾 下载] [🔄 重新生成]
                            
                            [图片3预览]
                            [👍 喜欢] [💾 下载] [🔄 重新生成]
                            
                          → Agent: "生成完成！这是为您设计的
                                   3张易拉宝。您觉得怎么样？
                                   
                                   可以：
                                   - 选择喜欢的下载
                                   - 告诉我需要调整的地方
                                   - 要求生成更多变体"
```

#### 场景2：知识库导入

```
用户操作                    界面反馈                      Agent响应
────────────────────────────────────────────────────────────────────
1. 选择"知识库导入"
                          → 侧边栏显示:
                            📚 从知识库选择
                            
                            🔍 [搜索框]
                            
                            下拉列表:
                            - 勇士K6直饮机 (饮水机)
                            - 爵士H5直饮机 (饮水机)
                            - 清风Pro净化器 (电器)
                            
2. 选择"勇士K6直饮机"
                          → 显示产品预览:
                            📋 产品信息预览
                            
                            产品名称: 勇士K6直饮机
                            品牌: 朴道健康水专家
                            类型: 饮水机
                            [产品图片预览]
                            
                            [✅ 使用此产品]
                            
3. 点击"✅ 使用此产品"
                          → Agent: "已加载产品：勇士K6直饮机
                                   
                                   我看到这是一款饮水机产品。
                                   请选择设计风格..."
                            
                            [后续流程同场景1]
```

#### 场景3：语音输入

```
用户操作                    界面反馈                      Agent响应
────────────────────────────────────────────────────────────────────
1. 点击"🎤"按钮
                          → 弹出提示:
                            "🎤 请说话..."
                            [录音动画]
                            
2. 说话: "我想要科技感的风格"
                          → 语音识别中...
                          
                          → 识别结果:
                            "我想要科技感的风格"
                            
                          → 自动填入输入框并发送
                          
                          → Agent: "好的，科技感风格！
                                   我将为您生成..."
```

#### 场景4：知识库管理

```
用户操作                    界面反馈
────────────────────────────────────────────────────
1. 点击"📚 管理知识库"
                          → 右侧弹出知识库管理面板
                            或切换到知识库标签页
                            
                            ┌─────────────────────────┐
                            │ 📚 产品知识库管理       │
                            ├─────────────────────────┤
                            │ [产品列表] [添加产品]   │
                            ├─────────────────────────┤
                            │                         │
                            │ 🔍 [搜索框]             │
                            │ 类型筛选: [全部 ▼]      │
                            │                         │
                            │ ┌─────────────────────┐ │
                            │ │ 表格视图            │ │
                            │ │                     │ │
                            │ │ 产品名称 | 品牌 | 类型│ │
                            │ │ ──────────────────  │ │
                            │ │ 勇士K6  | 朴道 | 饮水│ │
                            │ │ 爵士H5  | 朴道 | 饮水│ │
                            │ │ ...                 │ │
                            │ └─────────────────────┘ │
                            │                         │
                            │ [🗑️ 删除] [📤 导出]     │
                            └─────────────────────────┘
                            
2. 点击"添加产品"标签
                          → 显示添加表单:
                            
                            ┌─────────────────────────┐
                            │ 添加新产品              │
                            ├─────────────────────────┤
                            │ 产品名称*: [输入框]     │
                            │ 品牌*:     [输入框]     │
                            │ 产品类型*: [下拉选择]   │
                            │                         │
                            │ 产品资料:               │
                            │ [选择文件] (支持多选)   │
                            │ 支持: 图片/PDF/Word/PPT │
                            │                         │
                            │ 产品特点:               │
                            │ [文本框 - 多行]         │
                            │                         │
                            │ 适用场景:               │
                            │ [输入框]                │
                            │                         │
                            │ [✅ 添加到知识库]       │
                            └─────────────────────────┘
```

### 进度显示详细设计

```
┌─────────────────────────────────────┐
│ 📊 当前任务进度                     │
├─────────────────────────────────────┤
│                                     │
│ 步骤指示器:                         │
│ ✅ 1. 分析图片                      │
│ ✅ 2. 生成提示词                    │
│ ⏳ 3. 调用API (进行中)              │
│ ⚪ 4. 处理结果                      │
│                                     │
│ ─────────────────────────────────   │
│                                     │
│ 进度条:                             │
│ ████████████░░░░░░░░ 65%            │
│                                     │
│ 预计剩余时间: 45秒                  │
│                                     │
│ ─────────────────────────────────   │
│                                     │
│ 📝 详细日志 [展开 ▼]                │
│                                     │
│ (展开后显示):                       │
│ [14:23:15] 开始任务                 │
│ [14:23:16] 上传产品图片...          │
│ [14:23:20] 上传完成                 │
│ [14:23:21] 开始抠图处理...          │
│ [14:23:45] 抠图完成                 │
│ [14:23:46] 合成Logo...              │
│ [14:23:50] 合成完成                 │
│ [14:23:51] 调用生成API...           │
│ [14:24:10] API响应中...             │
│ [14:24:35] 生成中 (65%)...          │
│                                     │
└─────────────────────────────────────┘
```

---

## 详细设计

### 1. 对话流程设计

#### 完整对话流程（含主动提问和意图确认）

```
[开始]
  ↓
用户上传图片
  ↓
Agent: "正在分析您的产品图片..."
  ↓
[状态: IMAGE_UPLOADED]
  ↓
Claude Vision 提取信息
  ↓
Agent: "我识别到以下产品信息：
       产品名称：勇士K6/K9即开直饮机
       品牌：朴道健康水专家
       核心特点：
       - 高达125L/H开水量
       - 100℃开水持续出
       - 4重深度净化
       ...
       
       ⚠️ 主动提问：
       1. 这些信息正确吗？如需修改请告诉我。
       2. 我注意到产品类型是饮水机，主要适用场景是办公环境，对吗？
       3. 产品的主要目标用户是企业客户还是个人用户？"
  ↓
[状态: CONFIRM_PRODUCT]
  ↓
用户确认或修正
  ↓
Agent: "好的！现在请选择易拉宝的设计风格：
       
       ⚠️ 主动提问：
       1. 您希望生成什么风格的易拉宝？
          - 科技感 - 现代、智能、专业
          - 简约商务 - 高端、克制、精致
          - 自然清新 - 健康、环保、舒适
          - 时尚活力 - 年轻、创新、潮流
          - 高端奢华 - 尊贵、品质、奢华
       
       2. 您希望生成几张图片？（建议3-5张）
       
       3. 有特殊的颜色偏好吗？（如果没有，我会根据产品特点自动选择）"
  ↓
[状态: COLLECT_STYLE]
  ↓
用户选择风格和数量
  ↓
Agent: "✅ 意图确认
       
       让我确认一下您的需求：
       - 产品：勇士K6/K9即开直饮机
       - 品牌：朴道健康水专家
       - 风格：科技感
       - 数量：3张
       - 主色调：蓝色+白色+灰色
       - 场景：现代办公空间
       - 尺寸：80x200cm (9:21比例)
       
       ⚠️ 最后确认：
       1. 以上信息都正确吗？
       2. 是否需要调整任何参数？
       3. 确认无误后，我将开始生成，预计需要1-2分钟。
       
       请回复"确认"开始生成，或告诉我需要修改的地方。"
  ↓
用户确认
  ↓
Agent: "收到！开始生成3张【科技感】风格的易拉宝..."
  ↓
[状态: GENERATING]
  ↓
并行调用API生成（显示进度）
  ↓
Agent: "生成完成！这是为您设计的3张易拉宝：
       
       [图片1] [图片2] [图片3]
       
       ⚠️ 主动提问：
       1. 您觉得这些设计怎么样？
       2. 有哪张特别喜欢吗？
       3. 需要调整什么地方吗？（如颜色、布局、文字等）
       4. 是否需要生成更多变体？"
  ↓
[状态: SHOW_RESULTS]
  ↓
用户反馈
  ↓
[状态: FEEDBACK]
  ↓
根据反馈决定：
  - 满意 → Agent: "太好了！您可以单独下载喜欢的图片，或一键下载全部。"
  - 需要调整 → Agent: "好的，让我根据您的反馈调整..."
  - 生成更多 → Agent: "明白，我将生成更多变体..."
```

#### Agent主动提问策略

**何时提问**：
1. **信息不完整时** - 提取的产品信息有缺失
2. **信息不确定时** - Vision识别的置信度较低
3. **需要用户决策时** - 风格选择、数量选择
4. **关键节点确认时** - 开始生成前的最终确认
5. **结果反馈时** - 询问用户满意度和改进建议

**提问原则**：
- ✅ 具体明确，避免开放式问题
- ✅ 提供选项，降低用户思考成本
- ✅ 一次不超过3个问题
- ✅ 关键决策必须确认

**示例对话**：

```
场景1：信息不完整
Agent: "我识别到产品名称是'勇士K6直饮机'，但没有找到品牌信息。
       请问品牌名称是什么？"

场景2：信息不确定
Agent: "我识别到的产品特点包括：
       - 125L/H开水量
       - 100℃持续出水
       
       但图片中还有一些文字不太清晰，请问还有其他重要特点吗？"

场景3：需要用户决策
Agent: "我看到这是一款饮水机产品。对于饮水机，通常有两种设计方向：
       1. 科技感 - 强调智能、高效、现代
       2. 自然清新 - 强调健康、环保、舒适
       
       您更倾向于哪种？或者有其他想法？"

场景4：关键节点确认
Agent: "在开始生成前，让我确认一下：
       - 产品：勇士K6直饮机
       - 风格：科技感
       - 数量：3张
       
       确认无误吗？"

场景5：结果反馈
Agent: "生成完成！请问：
       1. 整体风格符合您的预期吗？
       2. 有需要调整的地方吗？（如颜色太深、文字太小等）"
```

---

#### 状态机定义

```python
class ConversationState(Enum):
    WELCOME = "welcome"                    # 欢迎状态
    IMAGE_UPLOADED = "image_uploaded"      # 图片已上传，等待分析
    CONFIRM_PRODUCT = "confirm_product"    # 确认产品信息
    COLLECT_STYLE = "collect_style"        # 收集设计风格
    GENERATING = "generating"              # 生成中
    SHOW_RESULTS = "show_results"          # 展示结果
    FEEDBACK = "feedback"                  # 收集反馈
    COMPLETED = "completed"                # 完成
```

---

### 2. 核心模块设计

#### Module 1: Agent编排器 (agent_orchestrator.py)

**职责**：
- 管理对话状态
- 协调各工具调用
- 处理用户输入
- 生成Agent响应

**核心类**：
```python
class BannerAgent:
    def __init__(self, api_key: str, claude_api_key: str):
        self.state = ConversationState.WELCOME
        self.context = {}  # 对话上下文
        
        # 初始化工具
        self.vision_analyzer = VisionAnalyzer(claude_api_key)
        self.prompt_generator = PromptGenerator()
        self.api_client = RunningHubClient(api_key)
        self.image_processor = ImageProcessor()
        self.recorder = TestRecorder()
    
    async def process_message(self, user_input: str, image=None) -> dict:
        """
        处理用户消息
        
        Returns:
            {
                "agent_message": "Agent的回复",
                "state": "当前状态",
                "options": ["选项1", "选项2"],  # 可选
                "results": [...]  # 生成结果（如果有）
            }
        """
        if self.state == ConversationState.WELCOME:
            return self._handle_welcome(image)
        
        elif self.state == ConversationState.IMAGE_UPLOADED:
            return await self._handle_image_analysis(image)
        
        elif self.state == ConversationState.CONFIRM_PRODUCT:
            return self._handle_product_confirmation(user_input)
        
        elif self.state == ConversationState.COLLECT_STYLE:
            return self._handle_style_selection(user_input)
        
        elif self.state == ConversationState.FEEDBACK:
            return self._handle_feedback(user_input)
    
    async def _handle_image_analysis(self, image):
        """分析图片，提取产品信息"""
        # 调用Claude Vision
        product_info = await self.vision_analyzer.analyze(image)
        
        # 保存到上下文
        self.context['product_info'] = product_info
        
        # 切换状态
        self.state = ConversationState.CONFIRM_PRODUCT
        
        # 生成确认消息
        return {
            "agent_message": self._format_product_confirmation(product_info),
            "state": self.state.value,
            "options": ["确认", "修改产品名称", "修改特点", "重新分析"]
        }
```

---

#### Module 2: 产品信息提取器 (vision_analyzer.py)

**职责**：
- 使用Claude Opus 4.7 Vision分析产品图片
- 提取结构化产品信息
- OCR文字识别
- 支持多种文件格式（PDF、Word、PPT）

**核心功能**：
```python
class VisionAnalyzer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-opus-4-20250514"  # Claude Opus 4.7
    
    async def analyze(self, image_path: str) -> dict:
        """
        使用Claude Opus 4.7分析产品图片
        
        Returns:
            {
                "product_name": "产品名称",
                "brand": "品牌名称",
                "slogan": "核心卖点",
                "features": ["特点1", "特点2", ...],
                "product_type": "产品类型",
                "scenes": ["适用场景1", "场景2", ...],
                "colors": ["主要颜色1", "颜色2"]
            }
        """
        # 读取图片
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # 构建Vision prompt
        prompt = """分析这张产品宣传图片，提取以下信息：

1. **产品名称**：完整的产品型号或名称
2. **品牌名称**：品牌或公司名称
3. **核心卖点**：主要的宣传语或口号（一句话）
4. **产品特点**：列出所有产品卖点和特性（每条独立）
5. **产品类型**：判断产品类别（如：饮水机、化妆品、电子产品等）
6. **适用场景**：产品适合使用的场景（如：办公室、家庭、医院等）
7. **主要颜色**：产品的主要颜色

请以JSON格式返回，确保信息完整准确。

示例格式：
{
  "product_name": "勇士K6/K9即开直饮机",
  "brand": "朴道健康水专家",
  "slogan": "澎湃开水持续出 绿色节能新选择",
  "features": [
    "高达125L/H开水量",
    "100℃开水持续出",
    "4重深度净化"
  ],
  "product_type": "饮水机",
  "scenes": ["商务办公", "政府机关", "医院病房"],
  "colors": ["黑色", "银色"]
}"""
        
        # 调用Claude Opus 4.7 Vision API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )
        
        # 解析JSON响应
        result_text = response.content[0].text
        product_info = json.loads(result_text)
        
        return product_info
    
    async def analyze_document(self, file_path: str, file_type: str) -> dict:
        """
        分析PDF、Word、PPT等文档
        
        Args:
            file_path: 文件路径
            file_type: 文件类型 (pdf/docx/pptx)
        
        Returns:
            提取的产品信息
        """
        # 根据文件类型提取文本和图片
        if file_type == 'pdf':
            text, images = self._extract_from_pdf(file_path)
        elif file_type == 'docx':
            text, images = self._extract_from_word(file_path)
        elif file_type == 'pptx':
            text, images = self._extract_from_ppt(file_path)
        
        # 使用Claude Opus 4.7分析文本和图片
        prompt = f"""分析以下产品文档内容，提取产品信息：

文档文本：
{text}

请提取产品名称、品牌、特点、适用场景等信息，以JSON格式返回。"""
        
        # 构建消息（包含文本和图片）
        content = [{"type": "text", "text": prompt}]
        
        # 添加图片（如果有）
        for img_data in images[:5]:  # 最多5张图片
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_data
                }
            })
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": content}]
        )
        
        result_text = response.content[0].text
        product_info = json.loads(result_text)
        
        return product_info
```

---

#### Module 3: Streamlit界面设计 (agent_app.py)

**界面布局**：采用四栏布局

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        易拉宝AI设计助手 🎨                               │
├──────────────┬──────────────────────┬──────────────────┬───────────────┤
│              │                      │                  │               │
│  侧边栏      │    对话区            │   进度/结果区    │  知识库管理   │
│  (固定)      │    (主交互)          │   (动态显示)     │  (标签页)     │
│              │                      │                  │               │
│ • 文件上传   │  💬 Agent对话        │  📊 生成进度     │  📚 产品库    │
│ • 知识库导入 │  🎤 语音输入         │  🎨 结果展示     │  ➕ 添加产品  │
│ • 快捷操作   │  ⚡ 快捷按钮         │  📥 下载管理     │  🔍 搜索筛选  │
│              │                      │                  │               │
└──────────────┴──────────────────────┴──────────────────┴───────────────┘
```

**详细界面设计**：

```python
import streamlit as st
from agent_orchestrator import BannerAgent
from knowledge_base import KnowledgeBase
import speech_recognition as sr

# 页面配置
st.set_page_config(
    page_title="易拉宝AI设计助手",
    page_icon="🎨",
    layout="wide"
)

# 初始化
if 'agent' not in st.session_state:
    st.session_state.agent = BannerAgent(
        api_key=st.secrets["RUNNING_HUB_API_KEY"],
        claude_api_key=st.secrets["CLAUDE_API_KEY"]
    )

if 'knowledge_base' not in st.session_state:
    st.session_state.knowledge_base = KnowledgeBase()

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'current_progress' not in st.session_state:
    st.session_state.current_progress = None

# ============ 主布局 ============
# 侧边栏
with st.sidebar:
    st.header("📤 输入产品信息")
    
    # 输入方式选择
    input_method = st.radio(
        "选择输入方式",
        ["本地上传", "知识库导入"],
        horizontal=True
    )
    
    if input_method == "本地上传":
        st.subheader("上传文件")
        
        # 支持多种文件格式
        uploaded_files = st.file_uploader(
            "选择产品文件",
            type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'pptx'],
            accept_multiple_files=True,
            help="支持图片、PDF、Word、PPT等格式"
        )
        
        if uploaded_files:
            st.success(f"已选择 {len(uploaded_files)} 个文件")
            
            # 预览
            for file in uploaded_files:
                with st.expander(f"📄 {file.name}"):
                    if file.type.startswith('image'):
                        st.image(file, use_column_width=True)
                    else:
                        st.info(f"文件类型: {file.type}")
            
            # 是否同步到知识库
            sync_to_kb = st.checkbox(
                "同步到知识库",
                value=True,
                help="将此产品信息保存到知识库，方便下次使用"
            )
            
            if st.button("🚀 开始分析", type="primary", use_container_width=True):
                # 处理文件
                for file in uploaded_files:
                    temp_path = f"temp/{file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(file.getbuffer())
                    
                    # 如果需要同步到知识库
                    if sync_to_kb:
                        st.session_state.knowledge_base.add_product_file(temp_path)
                
                # 调用Agent分析
                st.session_state.agent.start_analysis(uploaded_files)
                st.rerun()
    
    else:  # 知识库导入
        st.subheader("从知识库选择")
        
        # 获取知识库产品列表
        products = st.session_state.knowledge_base.get_all_products()
        
        if products:
            # 搜索框
            search_query = st.text_input("🔍 搜索产品", placeholder="输入产品名称...")
            
            # 筛选产品
            filtered_products = [
                p for p in products 
                if not search_query or search_query.lower() in p['name'].lower()
            ]
            
            # 产品选择器
            selected_product = st.selectbox(
                "选择产品",
                options=filtered_products,
                format_func=lambda p: f"{p['name']} ({p['type']})"
            )
            
            if selected_product:
                # 显示产品预览
                with st.expander("📋 产品信息预览", expanded=True):
                    st.write(f"**产品名称**: {selected_product['name']}")
                    st.write(f"**品牌**: {selected_product['brand']}")
                    st.write(f"**类型**: {selected_product['type']}")
                    if selected_product.get('image'):
                        st.image(selected_product['image'], width=200)
                
                if st.button("✅ 使用此产品", type="primary", use_container_width=True):
                    # 加载产品信息到Agent
                    st.session_state.agent.load_product_from_kb(selected_product)
                    st.rerun()
        else:
            st.info("知识库为空，请先添加产品")
    
    # 快捷操作
    st.markdown("---")
    st.subheader("⚡ 快捷操作")
    
    if st.button("🔄 重新开始", use_container_width=True):
        st.session_state.agent.reset()
        st.session_state.messages = []
        st.rerun()
    
    if st.button("📚 管理知识库", use_container_width=True):
        st.session_state.show_kb_manager = True
        st.rerun()

# ============ 主内容区 ============
col1, col2 = st.columns([3, 2])

# 左侧：对话区
with col1:
    st.header("💬 与AI助手对话")
    
    # 对话历史容器
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
                # 如果有快捷按钮
                if msg.get("quick_actions"):
                    cols = st.columns(len(msg["quick_actions"]))
                    for idx, action in enumerate(msg["quick_actions"]):
                        with cols[idx]:
                            if st.button(action["label"], key=f"qa_{msg['id']}_{idx}"):
                                # 处理快捷操作
                                st.session_state.agent.handle_quick_action(action["value"])
                                st.rerun()
    
    # 输入区
    st.markdown("---")
    
    # 语音+文字输入
    input_col1, input_col2 = st.columns([4, 1])
    
    with input_col1:
        user_input = st.chat_input("输入您的需求或问题...")
    
    with input_col2:
        # 语音输入按钮
        if st.button("🎤", help="点击开始语音输入"):
            # 语音识别逻辑
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("请说话...")
                audio = recognizer.listen(source)
                try:
                    text = recognizer.recognize_google(audio, language='zh-CN')
                    user_input = text
                    st.success(f"识别到: {text}")
                except:
                    st.error("语音识别失败")
    
    # 处理用户输入
    if user_input:
        # 添加用户消息
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "id": len(st.session_state.messages)
        })
        
        # 调用Agent处理
        with st.spinner("AI思考中..."):
            response = st.session_state.agent.process_message(user_input)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["message"],
                "quick_actions": response.get("quick_actions"),
                "id": len(st.session_state.messages)
            })
        
        st.rerun()

# 右侧：进度和结果区
with col2:
    # 标签页
    tab1, tab2 = st.tabs(["📊 生成进度", "🎨 生成结果"])
    
    with tab1:
        st.subheader("当前任务进度")
        
        if st.session_state.current_progress:
            progress = st.session_state.current_progress
            
            # 步骤指示器
            steps = ["分析图片", "生成提示词", "调用API", "处理结果"]
            current_step = progress.get("current_step", 0)
            
            # 显示步骤
            for idx, step in enumerate(steps):
                if idx < current_step:
                    st.success(f"✅ {step}")
                elif idx == current_step:
                    st.info(f"⏳ {step}...")
                else:
                    st.text(f"⚪ {step}")
            
            st.markdown("---")
            
            # 进度条
            progress_value = progress.get("percentage", 0)
            st.progress(progress_value / 100)
            st.caption(f"进度: {progress_value}% | 预计剩余: {progress.get('eta', 'N/A')}")
            
            st.markdown("---")
            
            # 实时日志
            with st.expander("📝 详细日志", expanded=False):
                logs = progress.get("logs", [])
                for log in logs[-10:]:  # 只显示最近10条
                    st.text(f"[{log['time']}] {log['message']}")
        else:
            st.info("暂无进行中的任务")
    
    with tab2:
        st.subheader("生成的易拉宝")
        
        if 'results' in st.session_state and st.session_state.results:
            results = st.session_state.results
            
            # 结果网格
            for idx, result in enumerate(results):
                with st.container(border=True):
                    st.image(result['url'], use_column_width=True)
                    
                    # 操作按钮
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("👍", key=f"like_{idx}", help="喜欢"):
                            st.session_state.agent.mark_favorite(result['id'])
                    with col_b:
                        if st.button("💾", key=f"download_{idx}", help="下载"):
                            # 下载逻辑
                            st.download_button(
                                "下载",
                                data=result['data'],
                                file_name=f"banner_{idx}.png",
                                mime="image/png"
                            )
                    with col_c:
                        if st.button("🔄", key=f"regenerate_{idx}", help="基于此重新生成"):
                            st.session_state.agent.regenerate_based_on(result['id'])
                            st.rerun()
        else:
            st.info("还没有生成结果")

# ============ 知识库管理页面（弹窗或独立页面）============
if st.session_state.get('show_kb_manager'):
    st.markdown("---")
    st.header("📚 产品知识库管理")
    
    kb_tab1, kb_tab2 = st.tabs(["产品列表", "添加产品"])
    
    with kb_tab1:
        # 产品列表（表格式）
        products = st.session_state.knowledge_base.get_all_products()
        
        if products:
            # 搜索和筛选
            col_search, col_filter = st.columns([3, 1])
            with col_search:
                search = st.text_input("🔍 搜索", placeholder="产品名称、品牌...")
            with col_filter:
                type_filter = st.selectbox("类型筛选", ["全部", "饮水机", "化妆品", "电子产品"])
            
            # 表格展示
            st.dataframe(
                products,
                column_config={
                    "name": "产品名称",
                    "brand": "品牌",
                    "type": "类型",
                    "created_at": st.column_config.DatetimeColumn("创建时间"),
                    "image": st.column_config.ImageColumn("预览图")
                },
                use_container_width=True
            )
            
            # 批量操作
            selected_rows = st.multiselect("选择产品进行操作", products)
            if selected_rows:
                col_del, col_export = st.columns(2)
                with col_del:
                    if st.button("🗑️ 删除选中", type="secondary"):
                        for product in selected_rows:
                            st.session_state.knowledge_base.delete_product(product['id'])
                        st.rerun()
                with col_export:
                    if st.button("📤 导出选中"):
                        # 导出为CSV
                        pass
        else:
            st.info("知识库为空")
    
    with kb_tab2:
        # 添加产品表单
        st.subheader("添加新产品")
        
        with st.form("add_product_form"):
            # 基本信息
            product_name = st.text_input("产品名称*", placeholder="例如：勇士K6直饮机")
            brand = st.text_input("品牌*", placeholder="例如：朴道健康水专家")
            product_type = st.selectbox("产品类型*", ["饮水机", "化妆品", "电子产品", "食品饮料", "其他"])
            
            # 产品文件
            product_files = st.file_uploader(
                "产品资料",
                type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'pptx'],
                accept_multiple_files=True,
                help="上传产品图片、说明书、宣传册等"
            )
            
            # 产品特点
            features = st.text_area(
                "产品特点",
                placeholder="每行一个特点\n例如：\n高达125L/H开水量\n100℃开水持续出\n4重深度净化",
                height=150
            )
            
            # 适用场景
            scenes = st.text_input(
                "适用场景",
                placeholder="用逗号分隔，例如：商务办公,政府机关,医院病房"
            )
            
            # 提交按钮
            submitted = st.form_submit_button("✅ 添加到知识库", type="primary")
            
            if submitted:
                if not product_name or not brand:
                    st.error("请填写必填项")
                else:
                    # 保存到知识库
                    product_id = st.session_state.knowledge_base.add_product({
                        "name": product_name,
                        "brand": brand,
                        "type": product_type,
                        "features": features.split('\n'),
                        "scenes": scenes.split(','),
                        "files": product_files
                    })
                    st.success(f"✅ 已添加产品: {product_name}")
                    st.rerun()
```

---

### 3. 风格选择系统

#### 预设风格库

```python
STYLE_PRESETS = {
    "科技感": {
        "scene": "现代科技办公空间,简约玻璃幕墙,智能设备环境",
        "lighting": "冷色调LED灯光,蓝白色光效,科技感光线",
        "colors": "蓝色+白色+灰色,科技蓝主色调",
        "atmosphere": "专业、现代、智能、高效",
        "icon": "🔷"
    },
    "简约商务": {
        "scene": "高端商务办公室,大理石台面,极简空间",
        "lighting": "柔和自然光,45度角斜射,明暗对比克制",
        "colors": "黑白灰+品牌色,低饱和度配色",
        "atmosphere": "专业、高端、克制、精致",
        "icon": "💼"
    },
    "自然清新": {
        "scene": "自然采光空间,绿植环境,木质元素",
        "lighting": "温暖自然光,柔和漫射,清晨或午后光线",
        "colors": "绿色+白色+原木色,清新自然",
        "atmosphere": "健康、环保、舒适、亲和",
        "icon": "🌿"
    },
    "时尚活力": {
        "scene": "年轻活力空间,色彩丰富,现代设计感",
        "lighting": "明亮活泼光线,多彩光效,动感光影",
        "colors": "鲜艳色彩,高饱和度,撞色搭配",
        "atmosphere": "活力、年轻、创新、潮流",
        "icon": "⚡"
    },
    "高端奢华": {
        "scene": "奢华空间,金属质感,高级材质",
        "lighting": "戏剧性光影,聚光灯效果,金色暖光",
        "colors": "金色+黑色+深色系,奢华配色",
        "atmosphere": "高端、奢华、尊贵、品质",
        "icon": "👑"
    }
}
```

#### 风格选择界面

```python
def show_style_selector():
    """显示风格选择器"""
    st.subheader("选择设计风格")
    
    # 预设风格卡片
    cols = st.columns(3)
    for idx, (style_name, style_config) in enumerate(STYLE_PRESETS.items()):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"### {style_config['icon']} {style_name}")
                st.caption(style_config['atmosphere'])
                
                if st.button("选择", key=f"style_{style_name}"):
                    return style_name
    
    # 自定义风格
    st.markdown("---")
    st.subheader("或者自定义风格")
    custom_style = st.text_area(
        "描述您想要的风格",
        placeholder="例如：我想要一个温馨的家居风格，暖色调，有生活气息..."
    )
    
    if custom_style and st.button("使用自定义风格"):
        return {"custom": custom_style}
    
    return None
```

---

### 4. 多轮优化机制

#### 反馈处理

```python
def handle_feedback(self, user_feedback: str) -> dict:
    """
    处理用户反馈，决定下一步行动
    
    反馈类型：
    1. 满意 → 结束流程
    2. 调整风格 → 重新选择风格
    3. 调整细节 → 微调参数重新生成
    4. 生成更多 → 生成更多变体
    """
    # 使用Claude理解用户意图
    intent = self._classify_feedback_intent(user_feedback)
    
    if intent == "satisfied":
        return {
            "agent_message": "太好了！您可以下载喜欢的设计。需要我帮您生成其他产品的易拉宝吗？",
            "state": ConversationState.COMPLETED.value
        }
    
    elif intent == "change_style":
        self.state = ConversationState.COLLECT_STYLE
        return {
            "agent_message": "好的，让我们重新选择风格。您想要什么样的风格？",
            "state": self.state.value
        }
    
    elif intent == "adjust_details":
        # 提取调整建议
        adjustments = self._extract_adjustments(user_feedback)
        
        # 更新提示词
        self.context['adjustments'] = adjustments
        
        return {
            "agent_message": f"明白了，我将调整：{adjustments}。正在重新生成...",
            "state": ConversationState.GENERATING.value
        }
    
    elif intent == "generate_more":
        return {
            "agent_message": "好的，我将为您生成更多变体...",
            "state": ConversationState.GENERATING.value
        }
```

---

## 实施计划

### 阶段一：核心Agent系统（1-2天）

**目标**：实现基本的对话流程和产品信息提取

**任务**：
1. 创建 `agent_orchestrator.py` - Agent编排器
   - 实现状态机
   - 实现基本对话流程
   - 集成现有工具

2. 创建 `vision_analyzer.py` - Claude Vision集成
   - 实现图片分析
   - 实现信息提取
   - 测试准确性

3. 改造 `agent_app.py` - Streamlit界面
   - 三栏布局
   - 聊天式对话
   - 结果展示

**验证标准**：
- ✅ 能上传图片并自动分析
- ✅ 能通过对话确认产品信息
- ✅ 能选择风格并生成易拉宝
- ✅ 能展示生成结果

---

### 阶段二：增强交互体验（1-2天）

**目标**：优化对话流程，增加多轮优化能力

**任务**：
1. 实现反馈处理机制
   - 意图识别
   - 参数调整
   - 重新生成

2. 优化风格选择
   - 风格卡片展示
   - 自定义风格支持
   - 风格预览

3. 添加历史记录
   - 保存对话历史
   - 保存生成结果
   - 支持回溯

**验证标准**：
- ✅ 能根据反馈调整设计
- ✅ 支持多轮优化
- ✅ 历史记录完整

---

### 阶段三：批量处理功能（必需）

**目标**：支持多产品并行生成

**任务**：
1. **批量选择界面**
   - 从知识库多选产品
   - 为每个产品设置风格
   - 预览批量任务列表

2. **并行生成管理**
   - 多任务并行调用API
   - 独立进度跟踪
   - 失败重试机制

3. **结果统一管理**
   - 批量结果展示
   - 按产品分组
   - 批量下载功能

**验证标准**：
- ✅ 支持同时处理5+个产品
- ✅ 每个产品独立进度显示
- ✅ 支持批量下载
- ✅ 失败产品可单独重试

---

## 关键文件清单

### 新增文件

1. **agent_orchestrator.py** - Agent编排器
   - 对话状态管理
   - 工具协调
   - 流程控制

2. **vision_analyzer.py** - Claude Vision集成
   - 图像分析
   - 信息提取
   - OCR识别
   - **支持多种文件格式**（PDF、Word、PPT）

3. **agent_app.py** - 新的Streamlit界面
   - 对话式交互（文字+语音）
   - 四栏布局（侧边栏+对话+进度/结果+知识库）
   - 实时进度显示
   - 知识库管理

4. **conversation_state.py** - 状态定义
   - 状态枚举
   - 状态转换规则

5. **knowledge_base.py** - 产品知识库管理
   - 产品信息存储（支持图片、PDF、Word、PPT等）
   - 搜索和筛选
   - 批量导入导出
   - 表格式管理界面

6. **file_processor.py** - 文件处理器
   - PDF文本提取
   - Word文档解析
   - PPT内容提取
   - 图片OCR识别

7. **progress_tracker.py** - 进度跟踪器
   - 步骤指示器
   - 进度百分比计算
   - 实时日志记录
   - ETA预估

### 复用文件

1. **runninghub_client.py** - API客户端（无需修改）
2. **banner_prompt_template.py** - 提示词模板（可能需要微调）
3. **test_standard_api.py** - 图片处理函数（复用Logo合成等）
4. **test_recorder.py** - 记录系统（复用）

---

## 技术栈

- **前端**: Streamlit (保持现有技术栈)
- **Agent核心**: Claude Opus 4.7 (claude-opus-4-20250514) - 最强推理能力
  - **API配置**: 支持自定义base_url和api_key（用户使用中转服务）
  - **配置方式**: 通过Streamlit secrets或环境变量配置
- **Vision分析**: Claude Opus 4.7 Vision (多模态能力)
- **API调用**: Running Hub (现有)
  - **并行生成**: ✅ 支持异步并行调用多个生成任务
  - **实现方式**: 使用asyncio同时提交多个任务，独立轮询各自进度
- **图片处理**: PIL (现有)
- **状态管理**: Streamlit session_state
- **语音识别**: SpeechRecognition (Google Speech API)

---

## 并行生成技术方案

### 问题：Running Hub API是否支持并行生成？

**答案：✅ 支持**

### 实现方案

```python
import asyncio
import httpx

async def generate_multiple_banners(product_info, style, count=3):
    """
    并行生成多张易拉宝
    
    Args:
        product_info: 产品信息
        style: 设计风格
        count: 生成数量
    
    Returns:
        List[task_id]: 任务ID列表
    """
    tasks = []
    
    # 为每张图片生成略有不同的提示词（变体）
    for i in range(count):
        prompt = generate_banner_prompt_variant(product_info, style, variant_index=i)
        
        # 创建异步任务
        task = asyncio.create_task(
            submit_generation_task(prompt, product_info['image_url'])
        )
        tasks.append(task)
    
    # 并行提交所有任务
    task_ids = await asyncio.gather(*tasks)
    
    return task_ids

async def submit_generation_task(prompt, image_url):
    """异步提交单个生成任务"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/rhart-image-g-2/image-to-image",
            json={
                "prompt": prompt,
                "imageUrls": [image_url],
                "aspectRatio": "9:21",
                "resolution": "2k"
            },
            headers=headers,
            timeout=30.0
        )
        result = response.json()
        return result.get('taskId')

async def wait_for_all_tasks(task_ids):
    """
    并行等待所有任务完成
    
    每个任务独立轮询，互不影响
    """
    tasks = [
        asyncio.create_task(wait_for_single_task(task_id))
        for task_id in task_ids
    ]
    
    # 并行等待所有任务
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results
```

### 优势

1. **节省时间**: 3张图片并行生成，总时间 ≈ 单张时间（而非3倍）
2. **独立进度**: 每张图片独立显示进度
3. **容错性**: 某张失败不影响其他
4. **用户体验**: 可以看到多张图片逐个完成

### 提示词变体策略

为了生成多张不同的图片，对提示词做微调：

```python
def generate_banner_prompt_variant(product_info, style, variant_index):
    """
    生成提示词变体
    
    变体策略：
    - 变体0: 标准提示词
    - 变体1: 调整光影角度
    - 变体2: 调整场景细节
    """
    base_prompt = generate_banner_prompt(product_info, style)
    
    if variant_index == 0:
        return base_prompt
    elif variant_index == 1:
        # 调整光影
        return base_prompt.replace(
            "45度角斜射",
            "顶部柔和漫射"
        )
    elif variant_index == 2:
        # 调整场景时间
        return base_prompt.replace(
            "下午3点的自然光",
            "清晨8点的柔和光线"
        )
    
    return base_prompt
```

---

## 风险和应对

### 风险1：Claude Vision提取不准确

**应对**：
- 提供手动修正功能
- 优化Vision prompt
- 支持多次重试

### 风险2：对话流程复杂

**应对**：
- 简化状态机
- 提供快捷选项
- 支持跳过步骤

### 风险3：生成速度慢

**应对**：
- 异步处理
- 显示进度
- 支持后台生成

---

## 下一步行动

### 立即开始

1. **确认技术方案**
   - Claude API Key准备
   - 确认预算和配额
   - 确认部署方式

2. **创建核心模块**
   - agent_orchestrator.py
   - vision_analyzer.py
   - conversation_state.py

3. **改造界面**
   - agent_app.py
   - 对话式交互
   - 结果展示

### 验证方式

**端到端测试**：
1. 上传产品图 → 自动分析
2. 确认信息 → 选择风格
3. 生成易拉宝 → 查看结果
4. 提供反馈 → 重新生成

**成功标准**：
- 信息提取准确率 > 85%
- 对话流程自然流畅
- 生成时间 < 2分钟（单张）或 < 2.5分钟（3张并行）
- 用户满意度 > 80%
- Agent主动提问及时准确
- 意图确认清晰明确

---

## 关键更新说明（2024-05-16）

### 1. Claude API中转支持
- 用户使用Claude API中转服务
- 需要在界面提供base_url和api_key配置
- 配置验证功能确保连接正常

### 2. 并行生成功能
- ✅ 支持同时生成多张图片
- 使用asyncio并行提交任务
- 每张图片独立进度跟踪
- 预计节省50%以上时间

### 3. 灵活的风格选择
- 如果用户确定风格 → 生成多张同风格变体
- 如果用户未指定 → 可为每个产品单独设置
- 批量处理时支持混合策略

### 4. 增强的下载功能
- 单张下载：每张图片独立下载按钮
- 批量下载：一键下载所有图片
- 分组下载：批量处理时按产品分组

### 5. Agent主动提问机制
- 信息不完整时主动询问
- 关键决策前主动确认
- 结果反馈时主动收集意见
- 每次提问不超过3个问题

### 6. 意图确认流程
- 开始生成前完整展示所有参数
- 明确询问用户是否确认
- 用户确认后才开始生成
- 避免浪费API调用和时间
