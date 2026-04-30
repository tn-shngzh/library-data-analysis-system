"""数据存储模块"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from rich.console import Console

from .models import DPOSample, ModelResponse, AnnotationStatus

console = Console(force_terminal=True, force_interactive=False)


class DataStorage:
    """数据存储器"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化存储器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.annotated_dir = self.data_dir / "annotated"
        self.exports_dir = self.data_dir / "exports"
        
        self._ensure_directories()
        
        self.raw_file = self.raw_dir / "samples.jsonl"
        self.annotated_file = self.annotated_dir / "dpo_data.jsonl"
    
    def _ensure_directories(self):
        """确保目录存在"""
        for dir_path in [self.raw_dir, self.annotated_dir, self.exports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def save_raw_sample(self, response: ModelResponse) -> str:
        """
        保存原始样本
        
        Args:
            response: 模型响应
        
        Returns:
            保存的文件路径
        """
        data = {
            "prompt": response.prompt,
            "response": response.response,
            "model_name": response.model_name,
            "timestamp": response.timestamp.isoformat(),
            "metadata": response.metadata,
        }
        
        with open(self.raw_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        
        return str(self.raw_file)
    
    def save_raw_batch(self, responses: List[ModelResponse]) -> int:
        """
        批量保存原始样本
        
        Args:
            responses: 模型响应列表
        
        Returns:
            保存的数量
        """
        count = 0
        for response in responses:
            self.save_raw_sample(response)
            count += 1
        
        return count
    
    def load_raw_samples(self) -> List[Dict[str, Any]]:
        """
        加载原始样本
        
        Returns:
            原始样本列表
        """
        if not self.raw_file.exists():
            return []
        
        samples = []
        with open(self.raw_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    samples.append(json.loads(line))
        
        return samples
    
    def save_annotated_sample(
        self,
        sample: DPOSample,
        format_type: str = "simple",
    ) -> str:
        """
        保存标注后的样本
        
        Args:
            sample: DPO 样本
            format_type: 输出格式
        
        Returns:
            保存的文件路径
        """
        data = sample.to_training_format(format_type)
        data["status"] = sample.status.value
        data["created_at"] = sample.created_at.isoformat()
        data["updated_at"] = sample.updated_at.isoformat() if sample.updated_at else None
        data["metadata"] = sample.metadata
        
        with open(self.annotated_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        
        return str(self.annotated_file)
    
    def load_annotated_samples(self) -> List[DPOSample]:
        """
        加载已标注样本
        
        Returns:
            DPO 样本列表
        """
        if not self.annotated_file.exists():
            return []
        
        samples = []
        with open(self.annotated_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    try:
                        sample = DPOSample(
                            prompt=data["prompt"],
                            chosen=data["chosen"],
                            rejected=data["rejected"],
                            status=AnnotationStatus(data.get("status", "annotated")),
                            created_at=datetime.fromisoformat(data["created_at"]),
                            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
                            metadata=data.get("metadata", {}),
                        )
                        samples.append(sample)
                    except Exception as e:
                        console.print(f"[yellow]加载样本失败：{e}[/yellow]")
        
        return samples
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计
        
        Returns:
            统计信息字典
        """
        raw_count = 0
        if self.raw_file.exists():
            with open(self.raw_file, "r", encoding="utf-8") as f:
                raw_count = sum(1 for line in f if line.strip())
        
        annotated_samples = self.load_annotated_samples()
        
        status_counts = {}
        for sample in annotated_samples:
            status = sample.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "raw_samples": raw_count,
            "total_annotated": len(annotated_samples),
            "status_breakdown": status_counts,
            "annotated_file": str(self.annotated_file),
        }
    
    def export_data(
        self,
        output_path: str,
        format_type: str = "simple",
        filter_status: Optional[AnnotationStatus] = None,
    ) -> int:
        """
        导出数据
        
        Args:
            output_path: 输出文件路径
            format_type: 输出格式
            filter_status: 筛选状态 (可选)
        
        Returns:
            导出的样本数量
        """
        samples = self.load_annotated_samples()
        
        if filter_status:
            samples = [s for s in samples if s.status == filter_status]
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        with open(output_file, "w", encoding="utf-8") as f:
            for sample in samples:
                if sample.status == AnnotationStatus.ANNOTATED:
                    data = sample.to_training_format(format_type)
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
                    count += 1
        
        return count
    
    def clear_raw_data(self):
        """清空原始数据"""
        if self.raw_file.exists():
            self.raw_file.unlink()
            console.print("[green][OK] 原始数据已清空[/green]")
    
    def clear_annotated_data(self):
        """清空标注数据"""
        if self.annotated_file.exists():
            self.annotated_file.unlink()
            console.print("[green][OK] 标注数据已清空[/green]")
