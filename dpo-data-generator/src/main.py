"""DPO 数据生成器 - 主入口"""
import asyncio
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.prompt import Prompt, Confirm

from .models import Config, DPOSample
from .api_client import APIClient, MockAPIClient
from .storage import DataStorage
from .annotator import Annotator

console = Console(force_terminal=True, force_interactive=False)


def load_config(config_path: Optional[str] = None) -> Config:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        Config: 配置对象
    """
    if config_path and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return Config(**data)
    
    default_path = Path("config.yaml")
    if default_path.exists():
        with open(default_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return Config(**data)
    
    return Config()


@click.group()
@click.version_option(version="0.1.0", prog_name="DPO Data Generator")
def cli():
    """DPO 训练数据生成工具
    
    用于日常对话场景收集和标注偏好数据，生成适配 DPO 训练的 JSON 格式数据。
    """
    pass


@cli.command()
@click.option("--config", "-c", default=None, help="配置文件路径")
@click.option("--prompt", "-p", required=True, help="问题/提示")
def fetch(config: Optional[str], prompt: str):
    """从模型获取问题回答并立即标注"""
    cfg = load_config(config)
    storage = DataStorage(cfg.data_dir)
    
    async def run():
        if cfg.api_key == "mock" or not cfg.api_key:
            client = MockAPIClient(cfg)
        else:
            client = APIClient(cfg)
        
        try:
            with console.status("[bold green]正在生成回答..."):
                response = await client.generate_response(prompt)
            
            console.print(f"\n[bold blue]问题:[/bold blue] {response.prompt}")
            console.print(f"[bold yellow]模型回答:[/bold yellow]\n{response.response}\n")
            
            # 立即进入标注流程
            annotator = Annotator(storage)
            annotated = annotator.interactive_annotate_single(response.prompt, response.response)
            
            if annotated:
                storage.save_annotated_sample(annotated, cfg.output_format)
                console.print(f"[green][OK] 已保存到：{storage.annotated_file}[/green]")
            else:
                console.print("[yellow][SKIP] 已跳过[/yellow]")
        
        finally:
            await client.close()
    
    asyncio.run(run())


@cli.command()
@click.option("--config", "-c", default=None, help="配置文件路径")
@click.option("--input", "-i", "input_file", required=True, help="输入文件路径 (包含问题列表)")
@click.option("--batch-size", "-b", default=10, help="批量大小")
@click.option("--max-concurrent", "-m", default=5, help="最大并发数")
def fetch_batch(
    config: Optional[str],
    input_file: str,
    batch_size: int,
    max_concurrent: int,
):
    """批量从模型获取回答"""
    cfg = load_config(config)
    storage = DataStorage(cfg.data_dir)
    
    if not Path(input_file).exists():
        console.print(f"[red]输入文件不存在：{input_file}[/red]")
        return
    
    with open(input_file, "r", encoding="utf-8") as f:
        prompts = [line.strip() for line in f if line.strip()]
    
    console.print(f"[green][OK] 读取了 {len(prompts)} 个问题[/green]")
    
    async def run():
        if cfg.api_key == "mock" or not cfg.api_key:
            client = MockAPIClient(cfg)
        else:
            client = APIClient(cfg)
        
        try:
            with console.status("[bold green]正在批量生成..."):
                responses = await client.generate_batch(prompts[:batch_size], max_concurrent=max_concurrent)
            
            console.print(f"[green][OK] 生成了 {len(responses)} 个回答[/green]")
            
            count = storage.save_raw_batch(responses)
            console.print(f"[green][OK] 保存了 {count} 个原始样本[/green]")
        
        finally:
            await client.close()
    
    asyncio.run(run())


@cli.command()
@click.option("--config", "-c", default=None, help="配置文件路径")
def annotate(config: Optional[str]):
    """标注已获取的原始数据"""
    cfg = load_config(config)
    storage = DataStorage(cfg.data_dir)
    
    annotator = Annotator(storage)
    annotator.run()


@cli.command()
@click.option("--config", "-c", default=None, help="配置文件路径")
def stats(config: Optional[str]):
    """查看数据统计"""
    cfg = load_config(config)
    storage = DataStorage(cfg.data_dir)
    
    stats_data = storage.get_statistics()
    
    console.print("\n[bold][STATS] 数据统计[/bold]\n")
    console.print(f"原始样本数：[cyan]{stats_data['raw_samples']}[/cyan]")
    console.print(f"已标注样本数：[green]{stats_data['total_annotated']}[/green]")
    
    if stats_data['status_breakdown']:
        console.print("\n状态分布:")
        for status, count in stats_data['status_breakdown'].items():
            status_icon = "[OK]" if status == "annotated" else "[SKIP]"
            console.print(f"  {status_icon} {status}: [bold]{count}[/bold]")
    
    console.print(f"\n标注文件：{stats_data['annotated_file']}")
    console.print()


@cli.command()
@click.option("--config", "-c", default=None, help="配置文件路径")
@click.option("--output", "-o", required=True, help="输出文件路径")
@click.option("--format", "-f", "format_type", default="simple", type=click.Choice(["simple", "chat"]))
@click.option("--status", "-s", default=None, type=click.Choice(["pending", "annotated", "skipped"]))
def export(config: Optional[str], output: str, format_type: str, status: Optional[str]):
    """导出数据为训练格式"""
    cfg = load_config(config)
    storage = DataStorage(cfg.data_dir)
    
    from .models import AnnotationStatus
    
    filter_status = None
    if status:
        filter_status = AnnotationStatus(status)
    
    count = storage.export_data(output, format_type, filter_status)
    
    console.print(f"[green][OK] 导出了 {count} 个样本到：{output}[/green]")


@cli.command()
@click.option("--config", "-c", default=None, help="配置文件路径")
def test(config: Optional[str]):
    """测试 API 连接"""
    cfg = load_config(config)
    
    async def run():
        if cfg.api_key == "mock" or not cfg.api_key:
            client = MockAPIClient(cfg)
        else:
            client = APIClient(cfg)
        
        try:
            success = await client.test_connection()
            if not success:
                raise SystemExit(1)
        finally:
            await client.close()
    
    asyncio.run(run())


@cli.command()
@click.option("--config", "-c", default=None, help="配置文件路径")
def init(config: Optional[str]):
    """初始化配置"""
    cfg = load_config(config)
    
    console.print("\n[bold]DPO Data Generator 配置向导[/bold]\n")
    
    api_base = Prompt.ask(
        "API 基础 URL",
        default=cfg.api_base_url,
    )
    
    api_key = Prompt.ask(
        "API 密钥",
        default=cfg.api_key if cfg.api_key else "mock",
        password=True,
    )
    
    model_name = Prompt.ask(
        "模型名称",
        default=cfg.model_name,
    )
    
    data_dir = Prompt.ask(
        "数据目录",
        default=cfg.data_dir,
    )
    
    output_format = Prompt.ask(
        "输出格式",
        type=click.Choice(["simple", "chat"]),
        default=cfg.output_format,
    )
    
    new_config = Config(
        api_base_url=api_base,
        api_key=api_key,
        model_name=model_name,
        data_dir=data_dir,
        output_format=output_format,
    )
    
    config_path = "config.yaml"
    if Path(config_path).exists():
        if not Confirm.ask(f"{config_path} 已存在，是否覆盖？"):
            config_path = Prompt.ask("请输入新的配置文件名", default="config_new.yaml")
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(new_config.model_dump(), f, default_flow_style=False, allow_unicode=True)
    
    console.print(f"\n[green][OK] 配置已保存到：{config_path}[/green]")
    console.print("\n您可以使用以下命令开始：")
    console.print("  [bold]dpo-gen fetch -p '您的问题'[/bold]")
    console.print("  [bold]dpo-gen annotate[/bold]")
    console.print()


@cli.command()
def clean():
    """清空数据"""
    if Confirm.ask("确定要清空所有数据吗？此操作不可恢复！"):
        storage = DataStorage()
        storage.clear_raw_data()
        storage.clear_annotated_data()
        console.print("[green][OK] 数据已清空[/green]")
    else:
        console.print("[yellow]操作已取消[/yellow]")


if __name__ == "__main__":
    cli()
