"""CLI 标注界面"""
from typing import Optional, List
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.text import Text

from .models import DPOSample, ModelResponse, AnnotationStatus
from .storage import DataStorage

console = Console(force_terminal=True, force_interactive=False)


class Annotator:
    """数据标注器"""
    
    def __init__(self, storage: DataStorage):
        """
        初始化标注器
        
        Args:
            storage: 数据存储器
        """
        self.storage = storage
        self.current_index = 0
        self.samples: List[DPOSample] = []
    
    def load_pending_samples(self):
        """加载待标注样本"""
        raw_data = self.storage.load_raw_samples()
        
        self.samples = []
        for data in raw_data:
            sample = DPOSample(
                prompt=data["prompt"],
                chosen="",  # 待用户填写
                rejected=data["response"],
                status=AnnotationStatus.PENDING,
                created_at=datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data["timestamp"],
                metadata=data.get("metadata", {}),
            )
            self.samples.append(sample)
        
        console.print(f"[green][OK] 加载了 {len(self.samples)} 个待标注样本[/green]")
    
    def display_sample(self, index: Optional[int] = None):
        """
        显示当前样本
        
        Args:
            index: 样本索引 (可选，默认为当前索引)
        """
        if index is None:
            index = self.current_index
        
        if index >= len(self.samples):
            console.print("[yellow]没有更多待标注样本了！[/yellow]")
            return False
        
        sample = self.samples[index]
        
        console.print("\n")
        console.print(Panel(
            f"[bold cyan]样本 {index + 1}/{len(self.samples)}[/bold cyan]",
            title="[DPO 标注]",
            border_style="cyan",
        ))
        
        console.print("\n[bold blue]问题 (Prompt):[/bold blue]")
        console.print(Panel(sample.prompt, border_style="blue"))
        
        console.print("\n[bold yellow]模型回答 (Rejected):[/bold yellow]")
        console.print(Panel(sample.rejected, border_style="yellow"))
        
        return True
    
    def get_user_preference(self) -> Optional[str]:
        """
        获取用户偏好的回答
        
        Returns:
            用户输入的回答，None 表示跳过
        """
        console.print("\n[bold green]请输入您偏好的回答 (Chosen):[/bold green]")
        console.print("[dim]提示：输入 :q 跳过当前样本，输入 :quit 退出标注[/dim]\n")
        
        try:
            user_input = Prompt.ask("您的回答")
            
            if user_input.strip().lower() in [":q", ":quit", ":exit"]:
                return None
            
            if not user_input.strip():
                console.print("[red]回答不能为空！[/red]")
                return self.get_user_preference()
            
            return user_input
        
        except (KeyboardInterrupt, EOFError):
            return None
    
    def annotate_current_sample(self, chosen_response: str):
        """
        标注当前样本
        
        Args:
            chosen_response: 用户偏好的回答
        """
        sample = self.samples[self.current_index]
        sample.chosen = chosen_response.strip()
        sample.mark_annotated()
        
        self.storage.save_annotated_sample(sample)
        
        console.print(f"\n[green][OK] 样本 {self.current_index + 1} 已保存[/green]")
    
    def skip_current_sample(self):
        """跳过当前样本"""
        sample = self.samples[self.current_index]
        sample.mark_skipped()
        
        console.print(f"\n[yellow][SKIP] 样本 {self.current_index + 1} 已跳过[/yellow]")
    
    def run(self):
        """运行标注流程"""
        if not self.samples:
            self.load_pending_samples()
        
        if not self.samples:
            console.print("[yellow]没有待标注的样本。请先使用 'fetch' 命令获取数据。[/yellow]")
            return
        
        console.print("\n[bold]开始标注，使用以下命令:[/bold]")
        console.print("  [green]<Enter>[/green] - 输入您的回答")
        console.print("  [yellow]:q[/yellow] - 跳过当前样本")
        console.print("  [yellow]:quit[/yellow] - 退出标注")
        console.print("  [yellow]:stat[/yellow] - 查看统计\n")
        
        while self.current_index < len(self.samples):
            if not self.display_sample():
                break
            
            user_input = self.get_user_preference()
            
            if user_input is None:
                action = Prompt.ask(
                    "\n选择操作",
                    choices=["skip", "quit", "stat"],
                    default="skip",
                )
                
                if action == "quit":
                    break
                elif action == "skip":
                    self.skip_current_sample()
                elif action == "stat":
                    self.show_statistics()
                    continue
            else:
                self.annotate_current_sample(user_input)
            
            self.current_index += 1
        
        console.print("\n[bold green][OK] 标注完成！[/bold green]")
        self.show_statistics()
    
    def show_statistics(self):
        """显示统计信息"""
        stats = self.storage.get_statistics()
        
        console.print("\n[bold]数据统计:[/bold]")
        console.print(f"  原始样本：[cyan]{stats['raw_samples']}[/cyan]")
        console.print(f"  已标注：[green]{stats['total_annotated']}[/green]")
        
        if stats['status_breakdown']:
            console.print("  状态分布:")
            for status, count in stats['status_breakdown'].items():
                console.print(f"    {status}: [bold]{count}[/bold]")
        
        console.print()
    
    def interactive_annotate_single(self, prompt: str, model_response: str) -> Optional[DPOSample]:
        """
        交互式标注单个样本
        
        Args:
            prompt: 问题
            model_response: 模型回答
        
        Returns:
            标注后的样本，None 表示跳过
        """
        console.print("\n")
        console.print(Panel(
            "[bold cyan]新样本[/bold cyan]",
            title="[DPO 标注]",
            border_style="cyan",
        ))
        
        console.print("\n[bold blue]问题:[/bold blue]")
        console.print(Panel(prompt, border_style="blue"))
        
        console.print("\n[bold yellow]模型回答:[/bold yellow]")
        console.print(Panel(model_response, border_style="yellow"))
        
        console.print("\n[bold green]请输入您偏好的回答:[/bold green]")
        console.print("[dim]输入 :q 跳过，输入 :quit 退出[/dim]\n")
        
        try:
            user_input = Prompt.ask("您的回答")
            
            if user_input.strip().lower() in [":q", ":quit", ":exit"]:
                return None
            
            if not user_input.strip():
                console.print("[red]回答不能为空！[/red]")
                return self.interactive_annotate_single(prompt, model_response)
            
            sample = DPOSample(
                prompt=prompt,
                chosen=user_input.strip(),
                rejected=model_response,
            )
            sample.mark_annotated()
            
            return sample
        
        except (KeyboardInterrupt, EOFError):
            return None
