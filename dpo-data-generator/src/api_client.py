"""模型 API 客户端"""
import asyncio
from typing import List, Optional
from datetime import datetime

import httpx
from rich.console import Console

from .models import ModelResponse, Config

console = Console(force_terminal=True, force_interactive=False)


class APIClient:
    """OpenAI 兼容 API 客户端"""
    
    def __init__(self, config: Config):
        """
        初始化 API 客户端
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.base_url = config.api_base_url.rstrip("/")
        self.api_key = config.api_key
        self.model_name = config.model_name
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
    
    async def generate_response(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ModelResponse:
        """
        从模型生成回答
        
        Args:
            prompt: 用户问题
            max_tokens: 最大 token 数 (可选，覆盖配置)
            temperature: 温度参数 (可选，覆盖配置)
        
        Returns:
            ModelResponse: 模型响应对象
        
        Raises:
            httpx.HTTPError: API 调用失败
        """
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
        }
        
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            return ModelResponse(
                prompt=prompt,
                response=content,
                model_name=self.model_name,
                timestamp=datetime.now(),
                metadata={
                    "usage": data.get("usage"),
                    "finish_reason": data["choices"][0].get("finish_reason"),
                }
            )
        
        except httpx.HTTPError as e:
            console.print(f"[red]API 调用失败：{e}[/red]")
            raise
    
    async def generate_batch(
        self,
        prompts: List[str],
        max_concurrent: int = 5,
    ) -> List[ModelResponse]:
        """
        批量生成回答
        
        Args:
            prompts: 问题列表
            max_concurrent: 最大并发数
        
        Returns:
            ModelResponse 列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(prompt: str) -> Optional[ModelResponse]:
            async with semaphore:
                try:
                    return await self.generate_response(prompt)
                except Exception as e:
                    console.print(f"[yellow]生成失败 '{prompt[:50]}...': {e}[/yellow]")
                    return None
        
        tasks = [generate_with_semaphore(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        
        return [r for r in results if r is not None]
    
    async def test_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            response = await self.generate_response("Hello", max_tokens=10)
            console.print("[green][OK] API 连接成功[/green]")
            return True
        except Exception as e:
            console.print(f"[red][FAIL] API 连接失败：{e}[/red]")
            return False


class MockAPIClient:
    """模拟 API 客户端 (用于测试)"""
    
    def __init__(self, config: Config):
        self.config = config
    
    async def close(self):
        pass
    
    async def generate_response(self, prompt: str, **kwargs) -> ModelResponse:
        """生成模拟响应"""
        await asyncio.sleep(0.5)  # 模拟延迟
        
        return ModelResponse(
            prompt=prompt,
            response=f"这是一个模拟回答。您问的是：{prompt}",
            model_name="mock-model",
            timestamp=datetime.now(),
        )
    
    async def generate_batch(self, prompts: List[str], **kwargs) -> List[ModelResponse]:
        """批量生成模拟响应"""
        return await asyncio.gather(*[self.generate_response(p) for p in prompts])
    
    async def test_connection(self) -> bool:
        console.print("[green][OK] 模拟客户端就绪[/green]")
        return True
