"""数据模型定义"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AnnotationStatus(str, Enum):
    """标注状态枚举"""
    PENDING = "pending"
    ANNOTATED = "annotated"
    SKIPPED = "skipped"


class Message(BaseModel):
    """对话消息模型"""
    role: str = Field(..., description="消息角色 (user/assistant)")
    content: str = Field(..., description="消息内容")


class ModelResponse(BaseModel):
    """模型响应模型"""
    prompt: str = Field(..., description="用户问题")
    response: str = Field(..., description="模型生成的回答")
    model_name: Optional[str] = Field(None, description="模型名称")
    timestamp: datetime = Field(default_factory=datetime.now, description="生成时间")
    metadata: Optional[dict] = Field(default_factory=dict, description="额外元数据")


class DPOSample(BaseModel):
    """DPO 训练样本模型"""
    prompt: str = Field(..., description="用户问题/提示")
    chosen: str = Field(..., description="用户偏好的回答 (chosen)")
    rejected: str = Field(..., description="模型生成的普通回答 (rejected)")
    status: AnnotationStatus = Field(default=AnnotationStatus.PENDING, description="标注状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    metadata: Optional[dict] = Field(default_factory=dict, description="额外元数据")
    
    def mark_annotated(self):
        """标记为已标注"""
        self.status = AnnotationStatus.ANNOTATED
        self.updated_at = datetime.now()
    
    def mark_skipped(self):
        """标记为已跳过"""
        self.status = AnnotationStatus.SKIPPED
        self.updated_at = datetime.now()
    
    def to_training_format(self, format_type: str = "simple") -> dict:
        """
        转换为 DPO 训练格式
        
        Args:
            format_type: 格式类型 ("simple" 或 "chat")
        
        Returns:
            训练数据字典
        """
        if format_type == "chat":
            return {
                "messages": [
                    {"role": "user", "content": self.prompt},
                    {"role": "assistant", "content": self.chosen}
                ],
                "rejected": self.rejected,
                "metadata": {
                    **self.metadata,
                    "timestamp": self.created_at.isoformat(),
                }
            }
        else:
            return {
                "prompt": self.prompt,
                "chosen": self.chosen,
                "rejected": self.rejected,
            }


class Config(BaseModel):
    """配置模型"""
    api_base_url: str = Field(default="https://api.openai.com/v1", description="API 基础 URL")
    api_key: str = Field(default="", description="API 密钥")
    model_name: str = Field(default="gpt-3.5-turbo", description="模型名称")
    max_tokens: int = Field(default=1024, description="最大生成 token 数")
    temperature: float = Field(default=0.7, description="温度参数")
    data_dir: str = Field(default="data", description="数据目录")
    output_format: str = Field(default="simple", description="输出格式 (simple/chat)")
    
    class Config:
        env_prefix = "DPO_"
