from openai import AsyncOpenAI
from agents import set_tracing_export_api_key, Agent, OpenAIChatCompletionsModel, ModelSettings
from openai.types.shared import Reasoning
from pydantic import BaseModel, Field
from enum import Enum
from agents import Runner, trace
from fastapi import HTTPException
from tools import SearchDeps, hybrid_search
import os
import logging
from agents.tools import search_knowledge_base


logger = logging.getLogger(__name__)


class RagCrew:
    def __init__(self):
        self.agents = {}
        self.model = None
        self.search_deps = SearchDeps()
        set_tracing_export_api_key(self.search_deps.settings.tracing_api_key)

    def add_model(self):
        local = self.search_deps.settings.llm_local
        base_url = self.search_deps.settings.llm_base_url
        api_key = self.search_deps.settings.llm_api_key
        model_name = self.search_deps.settings.llm_model
        if local:
            client =  AsyncOpenAI(base_url=base_url, api_key=api_key)
            self.model = OpenAIChatCompletionsModel(model=model_name, openai_client=client)
        else:
            self.model = model_name

    async def init_crew(self):
        self.add_model()
        await self.create_agents_as_a_tool()
        await self.create_agents()

    async def create_agents_as_a_tool(self):
        pass

    async def create_agents(self):
        self.agents["query"] = await self.query_agent()
        self.agents["evaluator"] = await self.evaluator_agent()
        
    async def query_agent(self):
        agent = Agent(
            name="Query", 
            instructions='''
           
            ''',
            model=self.model,
            tools=[search_knowledge_base],

        )
        return agent
    
    async def evaluator_agent(self):
        agent = Agent(
            name="Evaluator", 
            instructions='''
           
            ''',
            model=self.model

        )
        return agent


    async def run_agent(self, agent_name, prompt):
        agent = self.agents[agent_name]
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        with trace(agent.name):
            result = await Runner.run(agent, prompt)
            return result.final_output


 