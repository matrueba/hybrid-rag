#!/usr/bin/env python3
"""Conversational CLI with real-time streaming and tool call visibility."""

import asyncio
import argparse
import logging
from typing import List, Tuple, Any, Optional, Dict

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.text import Text

from dotenv import load_dotenv
from agents import gen_trace_id

from rag_agent.agent import RagAgent
from settings import Settings

load_dotenv(override=True)

logger = logging.getLogger(__name__)
console = Console()


async def run_agent_stream(rag_agent: RagAgent, user_input: str):
    """Run a query through the session-backed agent and stream the response to the console."""
    try:
        trace_id = gen_trace_id()
        logger.info(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
        
        streaming_result = rag_agent.run_agent_stream(user_input)
        
        console.print("[bold blue]Assistant:[/bold blue] ", end="")
        full_response = ""
        
        async for event in streaming_result.stream_events():
            # 1. Handle raw text deltas from the model
            if event.type == "raw_response_event":
                data = event.data
                if data.type == "response.output_text.delta":
                    delta = data.delta
                    console.print(delta, end="")
                    full_response += delta
                elif data.type == "response.function_call_arguments.delta":
                    pass

            # 2. Handle high-level lifecycle events
            elif event.type == "run_item_stream_event":
                if event.name == "tool_called":
                    tool_call = event.item
                    console.print(f"\n  [cyan]🔧 Calling tool:[/cyan] [bold]{tool_call.raw_item.name}[/bold]")
                elif event.name == "tool_output":
                    console.print(f"  [green]✅ Tool execution finished[/green]")
                    console.print("[bold blue]Assistant:[/bold blue] ", end="")
        
        console.print() # New line
        return full_response

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return ""


async def run_agent_query(rag_agent: RagAgent, user_input: str) -> str:
    """Run a simple non-streamed query."""
    try:
        return await rag_agent.run_agent(user_input)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return ""


def display_welcome(settings: Settings):
    """Display welcome message with configuration info."""
    llm_model = getattr(settings, "llm_model", "N/A")
    welcome = Panel(
        "[bold blue]RAG System[/bold blue]\n\n"
        "[green]Intelligent knowledge base search[/green]\n"
        f"[cyan]LLM: {llm_model}[/cyan]\n\n"
        "[cyan]Type 'exit' to quit, 'info' for system info, 'clear' to clear screen[/cyan]",
        style="blue",
        padding=(1, 2)
    )
    console.print(welcome)
    console.print()


def display_info(settings: Settings):
    """Displays system configuration."""
    console.print(Panel(
        f"[cyan]LLM Local:[/cyan] {settings.llm_local}\n"
        f"[cyan]LLM Model:[/cyan] {settings.llm_model}\n"
        f"[cyan]Embedding Model:[/cyan] {settings.embedding_model}\n"
        f"[cyan]Supabase URL:[/cyan] {settings.supabase_url}",
        title="System Configuration",
        border_style="magenta"
    ))


async def interactive_chat(rag_agent: RagAgent, settings: Settings):
    """Main interactive conversation loop with Supabase session persistence."""
    while True:
        try:
            user_input = Prompt.ask("[bold green]You").strip()

            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("\n[yellow]👋 Goodbye![/yellow]")
                break
            elif user_input.lower() == 'info':
                display_info(settings)
                continue
            elif user_input.lower() == 'clear':
                console.clear()
                display_welcome(settings)
                continue
            else:
                await run_agent_stream(rag_agent, user_input)

        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            continue
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            continue

        console.print("\n[dim]Goodbye![/dim]")


async def run_cli_mode(settings: Settings, session_id: str = "default"):
    display_welcome(settings)
    rag_agent = RagAgent(settings, session_id=session_id)
    await rag_agent.create_agent()
    console.print(f"[bold green]✓[/bold green] Session [cyan]{session_id}[/cyan] initialized\n")
    await interactive_chat(rag_agent, settings)