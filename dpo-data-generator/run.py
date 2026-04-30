"""DPO 数据生成器 - 自动生成问题版本"""
import sys
import asyncio
import random

sys.path.insert(0, 'src')

from src.models import Config
from src.api_client import MockAPIClient
from src.storage import DataStorage
from src.annotator import Annotator

# 问题类型列表（用于让模型生成不同类型的问题）
QUESTION_TYPES = [
    "日常对话",
    "学习方法",
    "健康生活",
    "工作效率",
    "人际关系",
    "心理健康",
    "职业发展",
    "时间管理",
    "创意思考",
    "知识科普",
]

async def generate_question_prompt(client: MockAPIClient) -> str:
    """让模型生成一个问题"""
    question_type = random.choice(QUESTION_TYPES)
    prompt = f"请生成一个关于{question_type}的常见问题，简短明了，适合日常对话。只返回问题本身，不要其他内容。"
    
    response = await client.generate_response(prompt)
    # 清理回答，只保留问题
    question = response.response.strip()
    
    # 如果回答太长，取第一句
    if len(question) > 100:
        question = question.split('.')[0].split('。')[0]
    
    return question

async def generate_model_answer(client: MockAPIClient, question: str) -> str:
    """让模型生成对这个问题的回答"""
    prompt = f"请回答这个问题，给出一个普通但合理的回答：{question}"
    
    response = await client.generate_response(prompt)
    return response.response.strip()

async def main():
    """主函数"""
    print("=" * 60)
    print("DPO 数据生成器 - 自动生成问题版本")
    print("=" * 60)
    print()
    print("工作流程:")
    print("1. [AI] 模型自动生成一个问题")
    print("2. [AI] 模型生成一个普通回答")
    print("3. [您] 填写更好的回答")
    print("4. [保存] 自动保存为 JSON 格式")
    print()
    print("JSON 格式:")
    print('  {"prompt": "问题", "chosen": "您的回答", "rejected": "模型回答"}')
    print()
    
    # 配置
    cfg = Config(api_key="mock")
    storage = DataStorage("data")
    client = MockAPIClient(cfg)
    
    try:
        while True:
            print("-" * 60)
            print("\n请选择操作:")
            print("1. [生成] 生成问题并标注")
            print("2. [统计] 查看统计")
            print("3. [导出] 导出数据")
            print("4. [退出] 退出程序")
            print()
            
            choice = input("输入选项 (1-4): ").strip()
            
            if choice == "1":
                print("\n" + "=" * 60)
                print("正在生成问题...")
                
                try:
                    # 1. 生成问题
                    question = await generate_question_prompt(client)
                    print(f"\n[问题] 生成的问题:")
                    print(f"   {question}")
                    
                    # 2. 生成模型回答
                    print("\n正在生成模型回答...")
                    model_answer = await generate_model_answer(client, question)
                    print(f"\n[模型回答]:")
                    print(f"   {model_answer}")
                    
                    # 3. 用户填写回答
                    print("\n" + "=" * 60)
                    print("[您的回答]")
                    print("请输入您认为更好的回答（直接输入，回车结束）:")
                    print("-" * 60)
                    
                    user_answer = input("> ").strip()
                    
                    if not user_answer:
                        print("\n[提示] 回答不能为空，已跳过")
                        continue
                    
                    if user_answer.lower() in [':q', ':skip', 'skip']:
                        print("\n[跳过] 已跳过")
                        continue
                    
                    if user_answer.lower() in [':quit', ':exit', 'quit']:
                        print("\n[退出] 退出标注")
                        break
                    
                    # 4. 保存为 JSON
                    from src.models import DPOSample
                    sample = DPOSample(
                        prompt=question,
                        chosen=user_answer,
                        rejected=model_answer,
                    )
                    sample.mark_annotated()
                    
                    storage.save_annotated_sample(sample, cfg.output_format)
                    
                    print("\n" + "=" * 60)
                    print("[成功] 保存成功！")
                    print(f"[文件] {storage.annotated_file}")
                    print()
                    print("生成的 JSON:")
                    import json
                    json_data = sample.to_training_format("simple")
                    print(json.dumps(json_data, ensure_ascii=False, indent=2))
                    print("=" * 60)
                
                except Exception as e:
                    print(f"\n[错误] {e}")
                    import traceback
                    traceback.print_exc()
            
            elif choice == "2":
                stats = storage.get_statistics()
                print("\n" + "=" * 60)
                print("[数据统计]")
                print("=" * 60)
                print(f"  已标注样本数：{stats['total_annotated']}")
                if stats['status_breakdown']:
                    print("  状态分布:")
                    for status, count in stats['status_breakdown'].items():
                        status_text = "[已标注]" if status == "annotated" else "[跳过]"
                        print(f"    {status_text} {status}: {count}")
                print(f"  数据文件：{stats['annotated_file']}")
                print("=" * 60)
            
            elif choice == "3":
                print("\n请输入输出文件名 (默认：dpo_data.jsonl):")
                output = input("> ").strip() or "dpo_data.jsonl"
                
                count = storage.export_data(output, cfg.output_format)
                print(f"\n[成功] 导出了 {count} 个样本到：{output}")
            
            elif choice == "4":
                print("\n再见！")
                break
            
            else:
                print("\n[错误] 无效选项，请重新输入！")
    
    except KeyboardInterrupt:
        print("\n\n[中断] 退出程序")
    
    finally:
        await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()
