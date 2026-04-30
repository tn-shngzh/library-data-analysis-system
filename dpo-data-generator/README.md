# DPO Data Generator

DPO (Direct Preference Optimization) 训练数据生成工具，用于日常对话场景收集和标注偏好数据。

## 功能特性

- ✅ 从模型 API 获取问题和回答
- ✅ 交互式标注界面
- ✅ 支持批量处理
- ✅ 保存为标准 DPO 训练格式 (JSON/JSONL)
- ✅ 支持 OpenAI 兼容 API 和本地模型
- ✅ 数据统计和导出功能

## 安装

```bash
# 克隆或进入项目目录
cd dpo-data-generator

# 安装依赖
pip install -e .

# 开发模式安装 (包含开发工具)
pip install -e ".[dev]"
```

## 快速开始

### 1. 初始化配置 (可选)

```bash
dpo-gen init
```

按照提示配置：
- API 基础 URL (如使用本地模型可设置为 `http://localhost:1234/v1`)
- API 密钥 (留空或输入 `mock` 使用模拟模式测试)
- 模型名称
- 数据目录
- 输出格式

### 2. 获取问题并标注 (主要工作流程)

```bash
dpo-gen fetch -p "今天天气怎么样？"
```

**工作流程：**
1. 模型生成问题和回答
2. 显示问题和模型回答
3. **您输入偏好的回答**
4. 自动保存为 JSON 格式

**输出示例：**
```json
{
  "prompt": "今天天气怎么样？",
  "chosen": "您的回答",
  "rejected": "模型生成的回答"
}
```

# 只导出特定状态的
dpo-gen export -o output.jsonl -s annotated
```

## 高级用法

### 批量获取

创建问题列表文件 `prompts.txt`:
```
问题 1
问题 2
问题 3
...
```

然后运行:
```bash
dpo-gen fetch-batch -i prompts.txt -b 20 -m 5
```

参数说明:
- `-b`: 批量大小
- `-m`: 最大并发数

### 测试 API 连接

```bash
dpo-gen test
```

### 清空数据

```bash
dpo-gen clean
```

## 数据格式

### 输入 (原始数据)
保存在 `data/raw/samples.jsonl`:
```jsonl
{"prompt": "问题", "response": "模型回答", "model_name": "gpt-3.5-turbo", "timestamp": "2026-04-29T10:00:00"}
```

### 输出 (DPO 训练格式)

**Simple 格式** (默认):
```jsonl
{"prompt": "问题", "chosen": "偏好回答", "rejected": "模型回答"}
```

**Chat 格式**:
```jsonl
{
  "messages": [
    {"role": "user", "content": "问题"},
    {"role": "assistant", "content": "偏好回答"}
  ],
  "rejected": "模型回答",
  "metadata": {"timestamp": "2026-04-29T10:00:00"}
}
```

## 配置说明

配置文件 `config.yaml`:

```yaml
# API 配置
api_base_url: "https://api.openai.com/v1"
api_key: "your-api-key"
model_name: "gpt-3.5-turbo"

# 生成参数
max_tokens: 1024
temperature: 0.7

# 数据目录
data_dir: "data"

# 输出格式：simple 或 chat
output_format: "simple"
```

### 使用本地模型

配置本地模型示例 (如 Ollama, LM Studio 等):

```yaml
api_base_url: "http://localhost:1234/v1"
api_key: "not-needed"
model_name: "local-model"
```

## 项目结构

```
dpo-data-generator/
├── src/
│   ├── __init__.py
│   ├── main.py          # CLI 入口
│   ├── models.py        # 数据模型
│   ├── api_client.py    # API 客户端
│   ├── storage.py       # 数据存储
│   └── annotator.py     # 标注界面
├── data/
│   ├── raw/             # 原始数据
│   ├── annotated/       # 已标注数据
│   └── exports/         # 导出数据
├── config.yaml          # 配置文件
├── pyproject.toml       # 项目配置
└── README.md
```

## 命令行帮助

```bash
dpo-gen --help
dpo-gen <command> --help
```

## 开发

```bash
# 代码格式化
black src/

# 代码检查
ruff check src/

# 运行测试
pytest
```

## 许可证

MIT License
