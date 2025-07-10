# **📚 本地知识库智能出题系统**

这是一个基于大语言模型（LLM）的智能出题系统，旨在帮助用户从本地技术规范文档中自动生成不同类型的题目（单选题、判断题、主观题），并提供答题及错题分析功能。系统采用模块化设计，易于扩展和维护。

## **✨ 功能特性**

* **文档上传与管理**：支持上传 JSON 格式的技术规范文档，并进行格式校验和预览。  
* **智能题目生成**：  
  * 根据上传的技术文档内容，自动生成单选题、判断题和主观题。  
  * 支持自定义生成题目数量。  
  * 生成过程中进行题目相似度检查，避免重复和高度相似的题目。  
* **题库管理**：  
  * 生成的题目会自动保存到本地题库，并支持与现有题库合并及去重。  
  * 可查看已生成的题库列表。  
* **在线答题**：  
  * 从现有题库中选择题目进行在线答题。  
  * 支持单选题、判断题和主观题的作答。  
* **智能答案批改**：  
  * 单选题和判断题进行精确匹配。  
  * **主观题利用大语言模型进行语义相似度判断**，智能批改答案。  
* **答题结果与分析**：  
  * 提供答题总览，包括总题数、正确数和正确率。  
  * 生成学习建议。  
  * 详细的错题分析，包括问题、你的答案和正确答案（选择题包含选项内容）。

## **🏗️ 项目架构**

项目采用前后端分离的架构，并对后端逻辑进行了模块化解耦，提高了可维护性和可扩展性。

Intelligent_question_generator/  
├── .env                     # 环境变量配置文件，用于存储API密钥等敏感信息  
├── requirements.txt         # Python 依赖库列表  
├── backend/                 # 后端核心逻辑  
│   ├── __init__.py          # Python 包标识  
│   ├── main.py              # 后端主入口，协调各模块  
│   ├── agents/              # 代理层：封装业务逻辑  
│   │   ├── __init__.py  
│   │   ├── question_agent.py# 负责题目生成、相似度检查和题库保存逻辑  
│   │   └── quiz_agent.py    # 负责答题和答案检查逻辑  
│   └── components/          # 组件层：提供基础服务  
│       ├── __init__.py  
│       ├── data_loader.py   # 负责文件上传、保存、加载和获取题库等文件操作  
│       └── llm_connector.py # 负责与大语言模型API的交互，包括文本生成和答案判断  
├── data/                    # 数据存储目录  
│   ├── raw_files/           # 存放用户上传的原始技术规范 JSON 文档  
│   └── question_dataset/    # 存放生成的题库 JSON 文件  
├── frontend/                # 前端界面逻辑 (Streamlit 应用)  
│   ├── __init__.py  
│   └── app.py               # Streamlit 应用主入口  
└── test/                    # 单元测试目录  
    ├── __init__.py  
    └── backend/  
        ├── __init__.py  
        ├── agents/  
        │   ├── __init__.py  
        │   ├── test_question_agent.py # question_agent.py 的测试脚本  
        │   └── test_quiz_agent.py     # quiz_agent.py 的测试脚本  
        └── components/  
            ├── __init__.py  
            ├── test_data_loader.py    # data_loader.py 的测试脚本  
            └── test_llm_connector.py  # llm_connector.py 的测试脚本

## **🚀 快速开始**

### **1. 环境准备**

确保您的系统已安装 Python 3.8+(建议使用3.11)。

### **2. 克隆项目**

运行如下命令以克隆项目到本地：

```bash
git clone <https://github.com/ivyinautumn/Intelligent_question_generator.git>  
cd Intelligent_assistant
```

### **3. 创建并激活虚拟环境 (推荐)**

- 首先创建虚拟环境

```bash
python -m venv venv
``` 

- 在Windows环境下激活虚拟环境

```bash
.venv\Script\sactivate
```

- macOS/Linux环境下激活虚拟环境

```bash 
source venv/bin/activate
```

### **4. 安装依赖**

```bash
# 确保激活虚拟环境之后安装依赖
pip install -r requirements.txt
```
### **5. 配置环境变量**

在项目根目录下创建`.env`(默认存在)文件，并填入您的大语言模型 API 密钥和模型名称。


```bash
# 阿里百炼大模型API配置
BAILIAN_API_KEY=YOUR_ACTUAL_API_KEY_HERE # 替换为你的API密钥  
BAILIAN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1 # 替换为你的API URL (通常无需修改)  
BAILIAN_MODEL_NAME=qwen-plus # 替换为你使用的模型名称 (例如：qwen-turbo, qwen-plus)
```

**请务必将 YOUR_ACTUAL_API_KEY_HERE 替换为您的实际 API 密钥。**

### **6. 运行应用**

<font color=red>注意！！！</font>务必在终端运行以下命令(根据自己的终端类型选择)再启动 Streamlit 应用，主要是为了避免出现"'latin-1' codec can't encode characters in position 45-49: ordinal not in range(256)" 的编码报错  

- Windows Dos

```bash
set PYTHONIOENCODING=utf-8
```

- Windows PowerShell

```bash
$env:PYTHONIOENCODING="utf-8"
```

- macOS/Linux

```bash
export PYTHONIOENCODING=utf-8
```

然后在项目根目录下运行以下命令启动 Streamlit 应用：

```bash
cd Intelligent_question_generator # 进入项目根目录
streamlit run frontend/app.py # 启动 Streamlit 应用
```

应用程序将在您的默认浏览器中打开。

## **🧪 运行测试**

为了验证后端模块的功能，您可以运行位于 `test/` 目录下的测试脚本。

在激活虚拟环境并位于项目根目录的情况下，运行以下命令：

- 运行 DataLoader 的测试  
```bash
python test/backend/components/test_data_loader.py
```

- 运行 LLMConnector 的测试  
```bash
python test/backend/components/test_llm_connector.py
```

- 运行 QuestionAgent 的测试  
```bash
python test/backend/agents/test_question_agent.py
```

- 运行 QuizAgent 的测试  
```bash
python test/backend/agents/test_quiz_agent.py
```

这些测试脚本将通过模拟外部依赖（如文件系统和大模型 API 调用）来演示每个模块的输入和输出。

## **📄 文档格式示例**

### **原始技术规范文档 (data/raw_files/)**

[  
&emsp;&emsp;{  
&emsp;&emsp;&emsp;"idx": "4.3.2.2",  
&emsp;&emsp;&emsp;"title": "条形码结构和尺寸要求",  
&emsp;&emsp;&emsp;"text": "条形码结构、尺寸及相关要求应符合Q/GDW 205—2008 的规定。射频电子条码安放在翻盖铭牌背面中心位置。"  
&emsp;&emsp;},  
&emsp;&emsp;{  
&emsp;&emsp;&emsp;"idx": "4.3.3.1",  
&emsp;&emsp;&emsp;"title": "采样元件",  
&emsp;&emsp;&emsp;"text": "a） 采样元件如采用精密互感器，应保证精密互感器具有足够的准确度，并用硬连接可靠地固定在端子上，或采用焊接方式固定在线路板上，不应使用胶类物质或捆扎方式固定。b） 采样元件如采用锰铜分流器，锰铜片与铜支架应焊接良好、可靠，不应采用铆接工艺；锰铜分流器与其采样连接端子之间应采用电子束或钎焊。"  
&emsp;&emsp;}  
]

---
### **生成的题库文件 (data/question_dataset/)**

[  
&emsp;&emsp;{  
&emsp;&emsp;&emsp;"type": "subjective",  
&emsp;&emsp;&emsp;"question": "请阐述在进行'停电抄表及显示'时，电能表应具备哪些特性或操作流程？",  
&emsp;&emsp;&emsp;"answer": "电能表在停电情况下，可通过按键唤醒显示，显示内容应包含重要结算数据，并且所有数据应能在断电情况下至少保存10年。",  
&emsp;&emsp;&emsp;"idx": 1,  
&emsp;&emsp;&emsp;"source_file": "单相静止式多费率电能表技术规范.json"  
&emsp;&emsp;},  
&emsp;&emsp;{  
&emsp;&emsp;&emsp;"type": "single_choice",  
&emsp;&emsp;&emsp;"question": "根据《单相静止式多费率电能表技术规范》的规定，对于时钟模块的设计要求中需要具有哪些功能？",  
&emsp;&emsp;&emsp;"options": [  
      "A. 应具有日历、计时、闰年自动转换功能",  
      "B. 无需具备日历功能，只需计时",  
      "C. 仅需具备计时和闰年自动转换功能"  
    ],  
&emsp;&emsp;&emsp;"answer": "A",  
&emsp;&emsp;&emsp;"idx": 2,  
&emsp;&emsp;&emsp;"source_file": "单相静止式多费率电能表技术规范.json"  
&emsp;&emsp;},  
&emsp;&emsp;{  
&emsp;&emsp;&emsp;"type": "judge",  
&emsp;&emsp;&emsp;"question": "根据技术规范，瞬时冻结要求保存最近3次的数据，而定时冻结要求每个冻结量至少保存60次。",  
&emsp;&emsp;&emsp;"answer": "正确",  
&emsp;&emsp;&emsp;"idx": 3,  
&emsp;&emsp;&emsp;"source_file": "单相智能电能表技术规范.json"  
&emsp;&emsp;}  
]

## **💡 未来展望**

* **更多题型支持**：考虑增加多选题、填空题等更多题型。  
* **用户认证与数据持久化**：为多用户场景增加用户登录、注册功能，并将用户数据和题库存储到数据库中。  
* **更智能的题目生成**：优化 LLM 提示词，提高题目生成质量和多样性，支持从复杂文档中提取更深层次的知识点。  
* **答案解析与反馈**：为错题提供详细的答案解析，帮助用户更好地理解知识点。  
* **前端交互优化**：提升用户界面和用户体验，例如增加加载动画、更友好的错误提示等。  
* **支持更多文档格式**：除了 JSON，考虑支持 PDF、Word 文档等。