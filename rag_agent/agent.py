from openai import AsyncOpenAI
from agents import set_tracing_export_api_key, Agent, OpenAIChatCompletionsModel, ModelSettings
from agents import Runner, RunHooks, trace, RunContextWrapper, ItemHelpers
from agents.tool import Tool
from fastapi import HTTPException
from supabase import create_client
import logging
from rag_agent.agent_tools import search_knowledge_base
from rag_agent.system_prompt import SYSTEM_PROMPT
from rag_agent.supabase_session import SupabaseSession
from agents.memory.session_settings import SessionSettings


logger = logging.getLogger(__name__)


class ToolUsageHooks(RunHooks):
    """Logs when tools are invoked and when they finish."""

    async def on_llm_start(self, context, agent, session) -> None:
        logger.info("🚀 [%s] Starting LLM call", agent.name)

    async def on_llm_end(self, context, agent, session) -> None:
        logger.info("✅ [%s] LLM call finished", agent.name)

    async def on_tool_start(self, context, agent, tool: Tool) -> None:
        logger.info("🔧 [%s] Calling tool: %s", agent.name, tool.name)

    async def on_tool_end(self, context, agent, tool: Tool, result: str) -> None:
        preview = (result[:120] + "…") if len(result) > 120 else result
        logger.info("✅ [%s] Tool %s finished — %s", agent.name, tool.name, preview)


class RagAgent:
    def __init__(self, settings, session_id: str = "default"):
        self.agent = None
        self.model = None
        self.session = None
        self.settings = settings
        self.session_id = session_id
        self.hooks = ToolUsageHooks()
        set_tracing_export_api_key(self.settings.tracing_api_key)

    def _add_model(self):
        local = self.settings.llm_local
        base_url = self.settings.llm_base_url
        api_key = self.settings.llm_api_key
        model_name = self.settings.llm_model
        if local:
            client = AsyncOpenAI(base_url=base_url, api_key=api_key)
            self.model = OpenAIChatCompletionsModel(model=model_name, openai_client=client)
        else:
            self.model = model_name

    async def create_agent(self):
        self._add_model()

        # Initialize Supabase session for conversation persistence
        supabase = create_client(self.settings.supabase_url, self.settings.supabase_key)
        self.session = SupabaseSession(
            session_id=self.session_id,
            supabase=supabase,
            session_settings=SessionSettings(limit=10),
        )

        self.agent = Agent(
            name="Query",
            instructions=SYSTEM_PROMPT,
            model=self.model,
            tools=[search_knowledge_base],
            model_settings=ModelSettings(tool_choice="search_knowledge_base")
        )

    async def run_agent(self, prompt):
        if self.agent is None:
            raise Exception("Agent not created. Call create_agent() first.")

        with trace(self.agent.name):
            result = await Runner.run(self.agent, prompt, hooks=self.hooks, session=self.session)

        return result.final_output

    def run_agent_stream(self, prompt):
        if self.agent is None:
            raise Exception("Agent not created. Call create_agent() first.")

        with trace(self.agent.name):
            return Runner.run_streamed(self.agent, prompt, session=self.session)