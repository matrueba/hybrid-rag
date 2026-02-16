#!/usr/bin/env python3
"""Conversational CLI with real-time streaming and tool call visibility."""

import asyncio
import argparse
from typing import List, Tuple, Any, Optional, Dict

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from pydantic_ai import Agent
from pydantic_ai.messages import PartDeltaEvent, PartStartEvent, TextPartDelta, FunctionToolCallEvent, FunctionToolResultEvent
from pydantic_ai.ag_ui import StateDeps
from dotenv import load_dotenv

# Import our agent and dependencies
# Assuming src is not a package, corrected imports
from agent import rag_agent, RAGState
from settings import load_settings, Settings

load_dotenv(override=True)

console = Console()

async def stream_agent_interaction(
    user_input: str,
    message_history: List,
    deps: StateDeps[RAGState]
) -> tuple[str, List]:
    """
    Stream agent interaction with real-time tool call display.

    Args:
        user_input: The user's input text
        message_history: List of ModelRequest/ModelResponse objects for conversation context
        deps: StateDeps with RAG state

    Returns:
        Tuple of (streamed_text, updated_message_history)
    """
    try:
        return await _stream_agent(user_input, deps, message_history)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return ("", [])


async def _stream_agent(
    user_input: str,
    deps: StateDeps[RAGState],
    message_history: List
) -> tuple[str, List]:
    """Stream the agent execution and return response."""
    response_text = ""

    async with rag_agent.iter(user_input, deps=deps, message_history=message_history) as run:
        async for node in run:
            if Agent.is_user_prompt_node(node):
                pass  # Clean start
            elif Agent.is_model_request_node(node):
                response_text = await _handle_model_request_node(node, run, response_text)
            elif Agent.is_call_tools_node(node):
                await _handle_tool_calls_node(node, run)
            elif Agent.is_end_node(node):
                pass

    new_messages = run.result.new_messages()
    final_output = run.result.output if hasattr(run.result, 'output') else str(run.result)
    response = response_text.strip() or final_output
    return response, new_messages


async def _handle_model_request_node(node: Any, run: Any, response_text: str) -> str:
    """Handle and stream model request node."""
    console.print("[bold blue]Assistant:[/bold blue] ", end="")
    async with node.stream(run.ctx) as request_stream:
        async for event in request_stream:
            if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                initial_text = event.part.content
                if initial_text:
                    console.print(initial_text, end="")
                    response_text += initial_text
            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                delta_text = event.delta.content_delta
                if delta_text:
                    console.print(delta_text, end="")
                    response_text += delta_text
    console.print()
    return response_text


async def _handle_tool_calls_node(node: Any, run: Any):
    """Handle and stream tool call node."""
    async with node.stream(run.ctx) as tool_stream:
        async for event in tool_stream:
            if isinstance(event, FunctionToolCallEvent):
                _display_tool_call(event)
            elif isinstance(event, FunctionToolResultEvent):
                console.print(f"  [green]Search completed successfully[/green]")


def _display_tool_call(event: FunctionToolCallEvent):
    """Display the tool call information in a structured way."""
    tool_name, args = _extract_tool_info(event)
    console.print(f"  [cyan]Calling tool:[/cyan] [bold]{tool_name}[/bold]")

    if args and isinstance(args, dict):
        if 'query' in args:
            console.print(f"    [dim]Query:[/dim] {args['query']}")
        if 'search_type' in args:
            console.print(f"    [dim]Type:[/dim] {args['search_type']}")
        if 'match_count' in args:
            console.print(f"    [dim]Results:[/dim] {args['match_count']}")
    elif args:
        args_str = str(args)
        if len(args_str) > 100:
            args_str = args_str[:97] + "..."
        console.print(f"    [dim]Args: {args_str}[/dim]")


def _extract_tool_info(event: FunctionToolCallEvent) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Extract tool name and arguments from a tool call event."""
    part = event.part
    tool_name = "Unknown Tool"
    args = None

    if hasattr(part, 'tool_name'):
        tool_name = part.tool_name
    elif hasattr(part, 'function_name'):
        tool_name = part.function_name
    elif hasattr(part, 'name'):
        tool_name = part.name

    if hasattr(part, 'args'):
        args = part.args
    elif hasattr(part, 'arguments'):
        args = part.arguments
    
    return tool_name, args


def display_welcome(settings: Settings):
    """Display welcome message with configuration info."""
    # Assuming settings object has these attributes, which is not in settings.py
    llm_model = getattr(settings, 'llm_model', 'N/A')
    welcome = Panel(
        "[bold blue]Supabase RAG Agent[/bold blue]\n\n"
        "[green]Intelligent knowledge base search with Supabase pgvector[/green]\n"
        f"[dim]LLM: {llm_model}[/dim]\n\n"
        "[dim]Type 'exit' to quit, 'info' for system info, 'clear' to clear screen[/dim]",
        style="blue",
        padding=(1, 2)
    )
    console.print(welcome)
    console.print()


def display_info(settings: Settings):
    """Displays system configuration."""
    # These attributes are not in the Settings class, so using getattr
    llm_provider = getattr(settings, 'llm_provider', 'N/A')
    llm_model = getattr(settings, 'llm_model', 'N/A')
    embedding_model = getattr(settings, 'embedding_model', 'N/A')
    default_match_count = getattr(settings, 'default_match_count', 'N/A')
    default_text_weight = getattr(settings, 'default_text_weight', 'N/A')
    
    console.print(Panel(
        f"[cyan]LLM Provider:[/cyan] {llm_provider}\n"
        f"[cyan]LLM Model:[/cyan] {llm_model}\n"
        f"[cyan]Embedding Model:[/cyan] {embedding_model}\n"
        f"[cyan]Default Match Count:[/cyan] {default_match_count}\n"
        f"[cyan]Default Text Weight:[/cyan] {default_text_weight}",
        title="System Configuration",
        border_style="magenta"
    ))


async def interactive_chat(deps: StateDeps[RAGState], settings: Settings):
    """Main interactive conversation loop."""
    message_history = []
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
            elif not user_input:
                continue

            _, new_messages = await stream_agent_interaction(user_input, message_history, deps)
            message_history.extend(new_messages)
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            continue
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()
            continue


async def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Conversational CLI for Supabase RAG Agent.")
    parser.add_argument("query", nargs="?", type=str, default=None, help="A query to run directly.")
    args = parser.parse_args()

    # Load default settings
    settings = load_settings()
    # Create the state that the agent will use
    state = RAGState()
    # Create StateDeps wrapper with the state
    deps = StateDeps[RAGState](state=state)

    if args.query:
        # Single-shot query mode
        console.print(f"[bold green]You:[/bold green] {args.query}")
        _, _ = await stream_agent_interaction(args.query, [], deps)
    else:
        # Interactive chat mode
        display_welcome(settings)
        console.print("[bold green]✓[/bold green] Search system initialized\n")
        await interactive_chat(deps, settings)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")