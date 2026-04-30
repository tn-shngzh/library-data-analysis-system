"""测试标注流程"""
import sys
sys.path.insert(0, 'src')

from src.models import DPOSample, AnnotationStatus
from src.storage import DataStorage
from src.annotator import Annotator

# 测试存储
storage = DataStorage("data")

# 加载原始样本
raw_samples = storage.load_raw_samples()
print(f"加载了 {len(raw_samples)} 个原始样本")

# 显示统计
stats = storage.get_statistics()
print(f"\n统计信息:")
print(f"  原始样本：{stats['raw_samples']}")
print(f"  已标注：{stats['total_annotated']}")

# 测试创建 DPO 样本
if raw_samples:
    sample_data = raw_samples[0]
    sample = DPOSample(
        prompt=sample_data["prompt"],
        chosen="这是用户偏好的回答",
        rejected=sample_data["response"],
    )
    sample.mark_annotated()
    
    # 保存标注样本
    storage.save_annotated_sample(sample)
    print(f"\n保存了测试标注样本")
    
    # 验证
    annotated = storage.load_annotated_samples()
    print(f"加载了 {len(annotated)} 个标注样本")
    
    # 导出
    count = storage.export_data("data/exports/test_output.jsonl")
    print(f"导出了 {count} 个样本")
