# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Flight Search and Travel Planning Agent
# =============================================================================
# Description:
#   Dedicated autonomous Travel Agent for searching, comparing, and pricing
#   airline tickets across multiple search engines and MCP servers.
#
# File: travel_agent.py
# Project: ai-breadboard
# Package: src.ai.agents
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import json
import asyncio
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from src.logger import logger
from src.utils.jjson import j_loads_ns

from .prompts import (
    TRAVEL_AGENT_SYSTEM_PROMPT,
    FLIGHT_SEARCH_GUIDELINES,
    FLIGHT_RESULT_FORMAT,
    TOOL_SELECTION_GUIDELINES,
)
from .tools import (
    flight_search,
    flight_price_calculator,
    web_search,
    rag_search,
    python_eval,
    file_read,
)
from .mcp_client import MCPClientManager


class TravelAgent:
    """Autonomous agent for flight discovery, pricing, and itinerary evaluation.

    Leverages multi-engine search capabilities and MCP tools:
    - Dedicated flight search aggregators and schedule fetchers (flight_search)
    - Multi-engine web search (Google Grounding, AGY, Playwright MCP) (web_search)
    - Arithmetic flight fare, tax, and baggage calculations (flight_price_calculator)
    - Traveler preferences and loyalty programs search (rag_search)
    - Python execution for timezone/layover math (python_eval)
    """

    def __init__(self, config_path: Path = Path('config.json'), ai_model: Any = None) -> None:
        """Initialize the TravelAgent.

        Args:
            config_path: Path to configuration file containing agent settings.
            ai_model: Optional external model instance.
        """
        self.config_path = config_path
        self.config = j_loads_ns(config_path)
        self.ai_model = ai_model

        langchain_cfg = getattr(self.config, 'langchain', object())
        self.llm_type = getattr(langchain_cfg, 'default_llm', 'gemini')
        self.max_steps = getattr(langchain_cfg, 'max_agent_steps', 15)
        self.timeout = getattr(langchain_cfg, 'search_timeout_seconds', 60)

        self._llm = None
        self._langchain_cfg = langchain_cfg

        # Native tools suite for travel and flight reasoning
        self.native_tools = [
            flight_search,
            flight_price_calculator,
            web_search,
            rag_search,
            python_eval,
            file_read,
        ]

        logger.info(
            f"[TravelAgent] Initialized: llm={self.llm_type}, "
            f"max_steps={self.max_steps}, timeout={self.timeout}"
        )

    def _get_llm(self) -> Any:
        """Lazy initialization of the underlying LLM instance."""
        if self._llm is not None:
            return self._llm

        if self.llm_type == 'gemini':
            from langchain_google_genai import ChatGoogleGenerativeAI
            model_name = getattr(self._langchain_cfg, 'gemini_model', 'gemini-2.5-flash')
            api_key = os.environ.get('GEMINI_API_KEY', '')
            if not api_key:
                from src.secrets.api_key_state import load_api_keys
                loaded, _, _ = load_api_keys()
                aiza_keys = [k for k in loaded if k.startswith('AIzaSy')]
                if aiza_keys:
                    api_key = aiza_keys[0]
                elif loaded:
                    api_key = loaded[0]
            if not api_key:
                logger.error('[TravelAgent] GEMINI_API_KEY is not set in environment')
                raise EnvironmentError('GEMINI_API_KEY is not set')

            self._llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.2,
            )
        else:
            from langchain_ollama import ChatOllama
            model_name = getattr(self._langchain_cfg, 'ollama_model', 'qwen2.5:7b')
            base_url = getattr(self._langchain_cfg, 'ollama_base_url', 'http://localhost:11434')
            self._llm = ChatOllama(
                model=model_name,
                base_url=base_url,
                temperature=0.2,
            )

        logger.info(f"[TravelAgent] LLM initialized: {self.llm_type}")
        return self._llm

    def _build_system_prompt(self) -> str:
        """Construct the comprehensive flight search and comparison system prompt."""
        return "\n\n".join([
            TRAVEL_AGENT_SYSTEM_PROMPT,
            FLIGHT_SEARCH_GUIDELINES,
            TOOL_SELECTION_GUIDELINES,
            FLIGHT_RESULT_FORMAT,
        ])

    async def search(self, query: str) -> Dict[str, Any]:
        """Execute autonomous flight search and return structured flight options.

        Args:
            query: Flight search request (e.g., 'Find flights from TLV to Paris for Oct 15').

        Returns:
            Dict containing action type, formatted analysis, and flight offers.
        """
        try:
            import re
            try:
                from langgraph.prebuilt import create_react_agent
            except ImportError:
                create_react_agent = None

            llm = self._get_llm()
            system_prompt = self._build_system_prompt()

            # Assemble tools: native tools + dynamically attached MCP tools
            all_tools = list(self.native_tools)

            try:
                async with MCPClientManager(str(self.config_path)) as mcp:
                    mcp_tools = await mcp.get_tools()
                    if mcp_tools:
                        all_tools.extend(mcp_tools)
                        logger.info(f"[TravelAgent] Attached {len(mcp_tools)} MCP tools")
            except Exception as mcp_err:
                logger.warning(f"[TravelAgent] MCP servers unavailable, continuing with native tools: {mcp_err}")

            logger.info(f'[TravelAgent] Executing ReAct agent with {len(all_tools)} tools for: "{query}"')

            if create_react_agent is not None:
                try:
                    agent_executor = create_react_agent(
                        llm,
                        all_tools,
                        prompt=system_prompt,
                    )
                except TypeError:
                    agent_executor = create_react_agent(
                        llm,
                        all_tools,
                        state_modifier=system_prompt,
                    )

                result = await asyncio.wait_for(
                    agent_executor.ainvoke({'messages': [('user', query)]}),
                    timeout=self.timeout,
                )

                messages = result.get('messages', [])
                if not messages:
                    return {'action': 'error', 'data': {'message': 'Travel agent returned no response'}}

                last_message = messages[-1]
                raw_content = getattr(last_message, 'content', '')
            else:
                # Direct fallback when langgraph is not installed
                if hasattr(llm, "ainvoke"):
                    res = await llm.ainvoke([("system", system_prompt), ("user", query)])
                    raw_content = getattr(res, "content", str(res))
                elif hasattr(llm, "ask"):
                    raw_content = await llm.ask(f"{system_prompt}\n\nUser: {query}")
                else:
                    raw_content = str(llm)
            if isinstance(raw_content, list):
                content = "".join([
                    c.get('text', '') if isinstance(c, dict) else str(c)
                    for c in raw_content
                ])
            else:
                content = str(raw_content)

            cleaned_content = content.strip()
            if cleaned_content.startswith('`'):
                cleaned_content = re.sub(r'^`(?:json)?\s*', '', cleaned_content)
                cleaned_content = re.sub(r'\s*`$', '', cleaned_content).strip()

            try:
                parsed = json.loads(cleaned_content)
                if isinstance(parsed, dict):
                    action = parsed.get('action', 'flight_results')
                    return {'action': action, **parsed}
                return {'action': 'flight_results', 'text': content}
            except (json.JSONDecodeError, ValueError):
                return {'action': 'flight_results', 'text': content}

        except asyncio.TimeoutError:
            logger.error(f'[TravelAgent] Timeout ({self.timeout}s) during flight search: "{query}"')
            return {'action': 'error', 'data': {'message': f'Search timeout exceeded ({self.timeout}s)'}}
        except Exception as e:
            logger.error(f'[TravelAgent] Error during flight search: {e}')
            return {'action': 'error', 'data': {'message': str(e)}}

    async def search_stream(self, query: str) -> AsyncIterator[Dict[str, Any]]:
        """Stream real-time progress statuses during flight search execution.

        Args:
            query: User's flight request.

        Yields:
            Progress dictionaries with 'status' or final 'result'.
        """
        yield {'status': '🛫 Analyzing flight route, dates, and passenger details...'}
        yield {'status': '🌐 Connecting to MCP search engines and flight aggregators...'}

        try:
            yield {'status': '🔍 Querying airlines, flight schedules, and pricing matrix...'}
            result = await self.search(query)

            action = result.get('action', 'error')
            if action == 'flight_results':
                yield {'status': '✨ Found flight options! Compiling comparison report...'}
            else:
                yield {'status': '⚠️ Flight search completed'}

            yield {'result': result}

        except Exception as e:
            logger.error(f'[TravelAgent] Error in stream search: {e}')
            yield {'status': f'❌ Error: {e}'}
            yield {'result': {'action': 'error', 'data': {'message': str(e)}}}
