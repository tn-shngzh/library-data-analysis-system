# 🚀 DPO 数据生成器 - 启动指南

## ⚡ 最简单的启动方式

### 方式 1：使用 Python 脚本（推荐）

```bash
cd d:\library-data-analysis-system\dpo-data-generator
python run.py
```

然后按照菜单提示操作！

### 方式 2：直接使用命令行

```bash
# 获取问题并标注
dpo-gen fetch -p "如何学习 Python？"
```

## 📋 完整使用流程

### 步骤 1：启动程序

```bash
python run.py
```

### 步骤 2：选择操作

程序会显示菜单：
```
请选择操作:
1. 获取问题并标注
2. 查看统计
3. 退出
```

### 步骤 3：输入问题

选择 `1` 后，输入您的问题，例如：
```
请输入您的问题：如何保持学习动力？
```

### 步骤 4：查看模型回答

程序会显示：
```
问题：如何保持学习动力？

模型回答:
这是一个模拟回答。您问的是：如何保持学习动力？
```

### 步骤 5：填写您的回答

```
请输入您偏好的回答:
[在此输入您的回答内容]
```

### 步骤 6：自动保存

程序会自动保存为 JSON 格式：
```
[OK] 已保存到：data\annotated\dpo_data.jsonl
```

## 📁 生成的数据格式

```json
{
  "prompt": "如何保持学习动力？",
  "chosen": "您填写的回答",
  "rejected": "模型生成的回答"
}
```

## 🎯 常用操作

### 查看统计

在菜单中选择 `2` 或运行：
```bash
dpo-gen stats
```

### 导出数据

```bash
dpo-gen export -o my_data.jsonl
```

### 查看生成的数据

直接打开文件：
```
data\annotated\dpo_data.jsonl
```

## 💡 使用技巧

1. **连续收集**: 可以多次选择选项 1 来收集多个样本
2. **跳过**: 输入 `:q` 可以跳过当前样本
3. **退出**: 输入 `:quit` 或选择选项 3 退出程序
4. **查看统计**: 随时选择选项 2 查看已收集的数据量

## ❓ 常见问题

**Q: 需要配置才能使用吗？**  
A: 不需要！默认使用模拟模式，可以直接测试。

**Q: 如何配置真实 API？**  
A: 运行 `dpo-gen init` 按照提示配置。

**Q: 数据保存在哪里？**  
A: `data/annotated/dpo_data.jsonl`

**Q: 如何查看数据？**  
A: 用文本编辑器打开 `data/annotated/dpo_data.jsonl`

## 🎉 立即开始

```bash
cd d:\library-data-analysis-system\dpo-data-generator
python run.py
```

然后选择 `1` 开始第一个样本！
