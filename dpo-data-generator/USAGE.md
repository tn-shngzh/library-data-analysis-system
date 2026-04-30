# DPO 数据生成器 - 使用示例

## 🎯 主要用途

从模型获取问题和普通回答，然后由您填写偏好的回答，自动生成 DPO 训练数据。

## 📝 基本使用流程

### 步骤 1：获取问题并标注

```bash
dpo-gen fetch -p "如何学习编程？"
```

**执行后：**
1. 模型会生成问题和回答
2. 显示问题：`如何学习编程？`
3. 显示模型回答：`学习编程需要...`
4. **您输入偏好的回答**
5. 自动保存为 JSON 格式

### 步骤 2：查看生成的数据

数据保存在 `data/annotated/dpo_data.jsonl`

```bash
# 查看数据
type data\annotated\dpo_data.jsonl
```

**JSON 格式：**
```json
{
  "prompt": "如何学习编程？",
  "chosen": "您的回答",
  "rejected": "模型生成的回答"
}
```

## 🚀 实际使用场景

### 场景 1：日常对话数据收集

```bash
# 获取一个对话样本
dpo-gen fetch -p "今天心情不好怎么办？"

# 继续获取更多
dpo-gen fetch -p "如何保持积极心态？"
dpo-gen fetch -p "有什么推荐的减压方法？"
```

### 场景 2：专业知识问答

```bash
# 收集专业领域数据
dpo-gen fetch -p "Python 中的装饰器是什么？"
dpo-gen fetch -p "解释一下机器学习中的过拟合"
dpo-gen fetch -p "什么是区块链？"
```

### 场景 3：创意写作

```bash
# 收集创意写作数据
dpo-gen fetch -p "写一首关于春天的诗"
dpo-gen fetch -p "编一个关于机器人的短篇故事"
```

## 📊 查看统计

```bash
dpo-gen stats
```

**输出示例：**
```
[STATS] 数据统计

原始样本数：10
已标注样本数：8

状态分布:
  [OK] annotated: 8
  [SKIP] skipped: 2

标注文件：data\annotated\dpo_data.jsonl
```

## 💾 导出数据

### 导出所有已标注数据

```bash
dpo-gen export -o my_dpo_data.jsonl
```

### 导出为特定格式

```bash
# Chat 格式 (用于某些训练框架)
dpo-gen export -o chat_data.jsonl -f chat

# 只导出标注的数据
dpo-gen export -o annotated_only.jsonl -s annotated
```

### 导出数据格式

**Simple 格式（默认）：**
```jsonl
{"prompt": "问题", "chosen": "偏好回答", "rejected": "模型回答"}
```

**Chat 格式：**
```jsonl
{
  "messages": [
    {"role": "user", "content": "问题"},
    {"role": "assistant", "content": "偏好回答"}
  ],
  "rejected": "模型回答"
}
```

## 🔧 配置（可选）

### 使用真实 API

如果您有 OpenAI API 或本地模型：

```bash
dpo-gen init
```

**配置示例：**

```yaml
# config.yaml
api_base_url: "https://api.openai.com/v1"
api_key: "sk-..."  # 您的 API 密钥
model_name: "gpt-3.5-turbo"
max_tokens: 1024
temperature: 0.7
data_dir: "data"
output_format: "simple"
```

### 使用本地模型

```yaml
# config.yaml
api_base_url: "http://localhost:1234/v1"  # Ollama, LM Studio 等
api_key: "not-needed"
model_name: "local-model"
```

## 📋 完整工作流程示例

```bash
# 1. 获取并标注 5 个样本
dpo-gen fetch -p "问题 1"
dpo-gen fetch -p "问题 2"
dpo-gen fetch -p "问题 3"
dpo-gen fetch -p "问题 4"
dpo-gen fetch -p "问题 5"

# 2. 查看统计
dpo-gen stats

# 3. 导出数据
dpo-gen export -o dpo_training_data.jsonl

# 4. 查看导出的数据
type dpo_training_data.jsonl
```

## ⌨️ 标注界面快捷键

在标注界面中：

- **直接输入**：填写您偏好的回答
- **`:q`** 或 **`:skip`**：跳过当前样本
- **`:quit`** 或 **`:exit`**：退出标注
- **`:stat`**：查看统计信息

## 📁 数据目录结构

```
dpo-data-generator/
├── data/
│   ├── raw/              # 原始数据（已弃用）
│   ├── annotated/        # 已标注数据
│   │   └── dpo_data.jsonl
│   └── exports/          # 导出的数据
│       └── output.jsonl
├── config.yaml           # 配置文件
└── ...
```

## 🎓 DPO 训练数据说明

### 数据格式要求

DPO (Direct Preference Optimization) 需要三元组数据：
- **prompt**: 用户问题
- **chosen**: 偏好的回答（您填写的）
- **rejected**: 不偏好的回答（模型生成的）

### 数据质量建议

1. **多样性**：收集不同类型的问题
2. **真实性**：填写真实、自然的回答
3. **一致性**：保持回答风格和质量一致
4. **完整性**：确保回答完整、准确

### 推荐数据量

- **最小可用**：100-500 个样本
- **推荐**：1000-5000 个样本
- **高质量**：10000+ 个样本

## ❓ 常见问题

### Q: 可以批量获取问题吗？
A: 当前版本专注于单个获取和标注，确保数据质量。批量获取功能在规划中。

### Q: 如何修改已标注的数据？
A: 直接编辑 `data/annotated/dpo_data.jsonl` 文件。

### Q: 支持哪些模型？
A: 支持所有 OpenAI 兼容的 API，包括：
- OpenAI GPT 系列
- 本地模型（Ollama, LM Studio, vLLM 等）
- 其他兼容 API

### Q: 数据格式可以自定义吗？
A: 支持 simple 和 chat 两种格式，可通过 `--format` 参数选择。

## 🎉 开始使用

```bash
# 立即开始第一个样本
dpo-gen fetch -p "您的第一个问题"
```
