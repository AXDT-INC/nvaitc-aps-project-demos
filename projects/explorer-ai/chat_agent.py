# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os

load_dotenv()
agents = {}
checkpointer = None


def get_checkpoint(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    global checkpointer
    if checkpointer is None:
        checkpointer = SqliteSaver.from_conn_string("data/curiosity.db")
    return checkpointer.get(config)


def get_agent(model_id: str):
    global agents
    if not model_id in agents:
        search = TavilySearchResults(max_results=5, include_images=True)
        tools = [search]
        global checkpointer
        cp = SqliteSaver.from_conn_string("data/curiosity.db")
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError("NVIDIA_API_KEY is not set. Create a .env with NVIDIA_API_KEY or export it in the shell.")

        if model_id == "meta/llama-3.1-405b-instruct":
            model = ChatNVIDIA(model=model_id, api_key=api_key, base_url="https://integrate.api.nvidia.com/v1", temperature=0)
        elif model_id == "meta/llama-3.1-70b-instruct":
            model = ChatNVIDIA(model=model_id, api_key=api_key, base_url="https://integrate.api.nvidia.com/v1", temperature=0)
        elif model_id == "meta/llama-3.2-3b-instruct":
            model = ChatNVIDIA(model=model_id, api_key=api_key, base_url="https://integrate.api.nvidia.com/v1", temperature=0)
        elif model_id == "deepseek-ai/deepseek-v3.1":
            model = ChatNVIDIA(model=model_id, api_key=api_key, base_url="https://integrate.api.nvidia.com/v1", temperature=0)
        elif model_id == "qwen/qwen3-next-80b-a3b-instruct":
            model = ChatNVIDIA(model=model_id, api_key=api_key, base_url="https://integrate.api.nvidia.com/v1", temperature=0)
        else:
            raise Exception(f"Model not supported: {model_id}")
        agent = create_react_agent(model, tools, checkpointer=cp)
        agents[model_id] = agent
    return agents[model_id]