"""测试新的标注流程"""
import sys
import asyncio
sys.path.insert(0, 'src')

from src.models import Config, DPOSample
from src.api_client import MockAPIClient
from src.storage import DataStorage
from src.annotator import Annotator

async def test_fetch_and_annotate():
    """测试获取并标注流程"""
    cfg = Config(api_key="mock")
    storage = DataStorage("data")
    client = MockAPIClient(cfg)
    
    try:
        # 1. 生成问题和回答
        prompt = "如何保持学习动力？"
        print(f"\n[测试] 问题：{prompt}")
        
        response = await client.generate_response(prompt)
        print(f"[测试] 模型回答：{response.response}\n")
        
        # 2. 进入标注流程
        annotator = Annotator(storage)
        annotated = annotator.interactive_annotate_single(response.prompt, response.response)
        
        if annotated:
            storage.save_annotated_sample(annotated, "simple")
            print(f"\n[OK] 已保存到：{storage.annotated_file}")
            
            # 显示保存的内容
            import json
            with open(storage.annotated_file, 'r', encoding='utf-8') as f:
                data = json.loads(f.readline())
                print(f"\n[JSON 格式示例]:")
                print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print("\n[SKIP] 已跳过")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_fetch_and_annotate())
