"""
llama.cpp 本地模型调用封装
支持流式输出和审查模式
"""
import requests
import json
from typing import AsyncIterator
import logging

logger = logging.getLogger(__name__)

LLAMA_API_URL = "http://localhost:8080"
TIMEOUT = 300


class LLMServerError(Exception):
    pass


class LLMConnectionError(Exception):
    pass


def check_llm_status() -> dict:
    """检查 LLM 服务状态"""
    try:
        resp = requests.get(f"{LLAMA_API_URL}/health", timeout=5)
        if resp.status_code == 200:
            return {"status": "online", "detail": "LLM服务运行中"}
        return {"status": "offline", "detail": f"LLM服务异常: {resp.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "detail": "LLM服务未启动，请确保 llama.cpp 服务在 localhost:8080 运行"}
    except Exception as e:
        return {"status": "offline", "detail": str(e)}


def call_llm_sync(prompt: str, system_prompt: str = "", n_predict: int = 2048) -> str:
    """
    同步调用 LLM，返回完整文本
    """
    try:
        payload = {
            "prompt": prompt,
            "n_predict": n_predict,
            "system": system_prompt,
            "stream": False,
        }
        resp = requests.post(f"{LLAMA_API_URL}/completion", json=payload, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("content", "").strip()
            return content
        else:
            error_detail = resp.text
            logger.error(f"LLM调用失败: {resp.status_code} - {error_detail}")
            raise LLMServerError(f"LLM返回错误: {resp.status_code}")
            
    except requests.exceptions.ConnectionError:
        raise LLMConnectionError("无法连接到 LLM 服务，请确保 llama.cpp 服务在 localhost:8080 运行")
    except requests.exceptions.Timeout:
        raise LLMServerError("LLM 调用超时")


def call_llm_stream(prompt: str, system_prompt: str = "", n_predict: int = 2048) -> AsyncIterator[str]:
    """
    流式调用 LLM，返回 AsyncIterator
    前端 SSE 流式读取
    """
    import asyncio
    
    async def _stream():
        try:
            payload = {
                "prompt": prompt,
                "n_predict": n_predict,
                "system": system_prompt,
                "stream": True,
            }
            async with asyncio.timeout(TIMEOUT):
                async with requests.post(
                    f"{LLAMA_API_URL}/completion", 
                    json=payload,
                    stream=True,
                    timeout=TIMEOUT
                ) as resp:
                    if resp.status_code != 200:
                        yield f"error:LLM返回{resp.status_code}"
                        return
                    
                    buffer = ""
                    async for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            buffer += chunk
                            # 尝试解析 SSE 格式
                            if "data:" in buffer:
                                lines = buffer.split("\n")
                                buffer = ""
                                for line in lines:
                                    line = line.strip()
                                    if line.startswith("data:"):
                                        try:
                                            data_str = line[5:].strip()
                                            if data_str == "[DONE]":
                                                yield "data:[DONE]"
                                                return
                                            data = json.loads(data_str)
                                            content = data.get("content", "")
                                            if content:
                                                yield f"data:{json.dumps({'content': content})}"
                                        except json.JSONDecodeError:
                                            buffer += line + "\n"
                                    elif line and not line.startswith("event:"):
                                        # 直接是 content 内容
                                        yield f"data:{json.dumps({'content': line})}"

        except asyncio.TimeoutError:
            yield 'data:{"error": "LLM调用超时"}'
        except requests.exceptions.ConnectionError:
            yield 'data:{"error": "无法连接到 LLM 服务"}'
        except Exception as e:
            yield f'data:{json.dumps({"error": str(e)})}'
    
    return _stream()


def review_with_llm(content: str, original_data: dict, system_prompt: str = "") -> str:
    """
    使用 LLM 审查报告内容，发现问题自动修正
    """
    review_prompt = f"""你是资深报告质量审核员。
请审核以下报告是否：
1. 数据准确性：报告中的数字与数据一致，无幻觉
2. 逻辑连贯性：分析推理是否成立
3. 格式规范性：结构清晰、表达通顺

原始数据：
{json.dumps(original_data, ensure_ascii=False, indent=2)}

待审核报告：
{content}

如果报告有问题，直接输出修正后的完整报告。
如果报告没有问题，输出"REVIEW_PASS"即可。
"""
    
    system = system_prompt or "你是一个严格的报告审核员，只输出修正后的内容或 REVIEW_PASS"
    result = call_llm_sync(review_prompt, system)
    
    if result.strip() == "REVIEW_PASS":
        return content  # 无需修正
    return result  # 返回修正后的报告


def generate_with_llm(data: dict, report_type: str, system_prompt: str = "") -> str:
    """
    使用 LLM 生成报告内容
    """
    prompt = f"""# Role
你是资深图书馆数据分析师。

# Data
{json.dumps(data, ensure_ascii=False, indent=2)}

# Task
基于以上数据，生成一份中文数据分析报告：
1. 数据概览：描述核心指标
2. 深度分析：解释数据原因
3. 建议措施：提出改进建议

# Style
简洁清晰、通俗易懂、结论先行。

# Output
Markdown 格式，结构清晰，200字左右。
"""
    
    system = system_prompt or "你是一个专业的数据分析师，用简洁清晰的中文输出报告。"
    return call_llm_sync(prompt, system)
