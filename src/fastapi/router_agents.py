# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI agents configuration and execution router
# =============================================================================
# Description:
#   Provides FastAPI endpoints for managing system and custom AI agents,
#   handling prompt generation via AI Architect, and executing agent test workflows.
#
# File: router_agents.py
# Project: ai-breadboard
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import time
import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from header import __root__
from src.logger import logger
from src.utils.jjson import j_loads_ns

import copy

_CONFIG_PATH = __root__ / 'config.json'
_AGENTS_METADATA_PATH = Path(__file__).parent / 'agents_metadata.json'

# ============================================================================
# Load agents metadata from external config
# ============================================================================

def _load_agents_metadata() -> dict:
    """Load available tools and providers from external metadata file.
    
    Returns:
        dict: Dictionary with 'tools' and 'providers' keys.
    """
    if not _AGENTS_METADATA_PATH.exists():
        logger.warning(f'[router_agents] Metadata file not found: {_AGENTS_METADATA_PATH}')
        return {'tools': [], 'providers': {}}
    
    try:
        with open(_AGENTS_METADATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'[router_agents] Error loading agents metadata: {e}')
        return {'tools': [], 'providers': {}}

_AGENTS_METADATA = _load_agents_metadata()
_AVAILABLE_TOOLS = _AGENTS_METADATA.get('tools', [])
_PROVIDERS_CONFIG = _AGENTS_METADATA.get('providers', {})

# ============================================================================
# Pydantic Models
# ============================================================================

class AgentModel(BaseModel):
    """Agent configuration model.
    
    Defines all parameters for AI agent execution and behavior.
    """
    id: str
    name: str
    description: str = ''
    is_system: bool = False
    enabled: bool = True
    provider: str = 'gemini'
    model: str = 'gemini-2.5-flash'
    temperature: float = 0.3
    max_steps: int = 15
    timeout_seconds: int = 60
    tools: List[str] = Field(default_factory=list)
    system_prompt: str = ''

class GeneratePromptRequest(BaseModel):
    """Request to generate agent prompt via AI Architect."""
    task_description: str
    provider: str = 'gemini'
    model: str = 'gemini-2.5-flash'
    agent_name: str = ''

class TestAgentRequest(BaseModel):
    """Request to test agent execution."""
    agent_id: str = ''
    inline_config: Optional[AgentModel] = Field(default_factory=dict) # type: ignore
    test_message: str

# ============================================================================
# Config.json helper functions
# ============================================================================

def _load_raw_config() -> dict:
    """Load full config.json file.
    
    Returns:
        dict: Parsed configuration or empty dict if file not found.
    """
    if not _CONFIG_PATH.exists():
        return {}
    try:
        with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'[router_agents] Error loading config.json: {e}')
        return {}

def _save_raw_config(data: dict) -> None:
    """Save config.json with formatting.
    
    Args:
        data: Configuration dictionary to save.
        
    Raises:
        HTTPException: If save operation fails.
    """
    try:
        with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f'[router_agents] Error saving config.json: {e}')
        raise HTTPException(status_code=500, detail='Failed to save configuration')

def _get_agents_list() -> List[dict]:
    """Get list of agents from config.json.
    
    Returns:
        List[dict]: List of agent configurations.
    """
    cfg = _load_raw_config()
    agents_cfg = cfg.get('agents', {})
    if isinstance(agents_cfg, dict):
        return agents_cfg.get('items', [])
    return []

def _save_agents_list(items: List[dict]) -> None:
    """Save updated agents list to config.json.
    
    Args:
        items: List of agent configurations to save.
    """
    cfg = _load_raw_config()
    if 'agents' not in cfg or not isinstance(cfg['agents'], dict):
        cfg['agents'] = {}
    cfg['agents']['items'] = items
    _save_raw_config(cfg)

# ============================================================================
# FastAPI Router
# ============================================================================

def init_agents_router(prefix: str = '/api/agents') -> APIRouter:
    """Initialize and return agent management router.
    
    Args:
        prefix: URL prefix for router endpoints.
        
    Returns:
        APIRouter: Configured FastAPI router.
    """
    router = APIRouter(prefix=prefix, tags=['agents'])

    @router.get('')
    async def list_agents() -> List[dict]:
        """Get list of all agents (system and user-defined).
        
        Returns:
            List[dict]: List of agent configurations.
        """
        return _get_agents_list()

    @router.get('/tools')
    async def list_tools() -> List[dict]:
        """Get catalog of all available system tools.
        
        Returns:
            List[dict]: List of tool definitions.
        """
        return _AVAILABLE_TOOLS

    @router.get('/providers')
    async def list_providers() -> dict:
        """Get list of providers and dynamically fetched models from project pool."""
        from src.ai.model_manager import get_available_models

        raw_cfg = _load_raw_config()
        ai_section = raw_cfg.get('ai', {})

        # Deep copy base provider metadata
        providers = copy.deepcopy(_PROVIDERS_CONFIG)

        # Dynamically populate models for each provider from model_manager
        for prov_id, prov_info in providers.items():
            try:
                raw_models = get_available_models(prov_id)
                prov_info['models'] = [{'id': m, 'name': m} for m in raw_models]
            except Exception as e:
                logger.warning(f'[router_agents] Error querying models for provider {prov_id}: {e}')
                prov_info['models'] = []

        # Override defaults from config.json if present
        if 'gemini_cli_model_id' in ai_section:
            if 'gemini_cli' in providers:
                providers['gemini_cli']['default_model'] = ai_section['gemini_cli_model_id']

        if 'agy_model_id' in ai_section:
            if 'agy' in providers:
                providers['agy']['default_model'] = ai_section['agy_model_id']

        if 'foundry_model_id' in ai_section:
            if 'foundry' in providers:
                providers['foundry']['default_model'] = ai_section['foundry_model_id']

        if 'ollama_model' in raw_cfg.get('langchain', {}):
            if 'ollama' in providers:
                providers['ollama']['default_model'] = raw_cfg['langchain']['ollama_model']

        return providers

    @router.post('')
    async def create_agent(agent: AgentModel) -> dict:
        """Create new custom agent.
        
        Args:
            agent: Agent configuration.
            
        Returns:
            dict: Created agent data with status.
            
        Raises:
            HTTPException: If agent ID already exists.
        """
        items = _get_agents_list()
        
        # Check ID uniqueness
        existing_ids = {a.get('id') for a in items}
        if agent.id in existing_ids:
            raise HTTPException(status_code=400, detail=f'Agent with ID "{agent.id}" already exists')

        # Protect is_system flag for user agents
        agent_dict = agent.dict()
        agent_dict['is_system'] = False

        items.append(agent_dict)
        _save_agents_list(items)
        logger.info(f'[router_agents] Created new agent: {agent.id} ({agent.name})')
        return {'status': 'ok', 'agent': agent_dict}

    @router.put('/{agent_id}')
    async def update_agent(agent_id: str, agent: AgentModel) -> dict:
        """Update existing agent.
        
        Args:
            agent_id: Agent identifier.
            agent: Updated agent configuration.
            
        Returns:
            dict: Updated agent data with status.
            
        Raises:
            HTTPException: If agent not found.
        """
        items = _get_agents_list()
        found_idx = -1
        for idx, item in enumerate(items):
            if item.get('id') == agent_id:
                found_idx = idx
                break

        if found_idx == -1:
            raise HTTPException(status_code=404, detail=f'Agent with ID "{agent_id}" not found')

        old_item = items[found_idx]
        agent_dict = agent.dict()
        # Preserve system status from original agent
        agent_dict['is_system'] = old_item.get('is_system', False)
        agent_dict['id'] = agent_id  # ID does not change

        items[found_idx] = agent_dict
        _save_agents_list(items)
        logger.info(f'[router_agents] Updated agent: {agent_id}')
        return {'status': 'ok', 'agent': agent_dict}

    @router.delete('/{agent_id}')
    async def delete_agent(agent_id: str) -> dict:
        """Delete custom agent (system agents are protected).
        
        Args:
            agent_id: Agent identifier.
            
        Returns:
            dict: Status and deleted agent ID.
            
        Raises:
            HTTPException: If agent not found or is system agent.
        """
        items = _get_agents_list()
        target = None
        for item in items:
            if item.get('id') == agent_id:
                target = item
                break

        if not target:
            raise HTTPException(status_code=404, detail=f'Agent with ID "{agent_id}" not found')

        if target.get('is_system', False):
            raise HTTPException(status_code=403, detail='System agents cannot be deleted. You can disable them.')

        items = [i for i in items if i.get('id') != agent_id]
        _save_agents_list(items)
        logger.info(f'[router_agents] Deleted agent: {agent_id}')
        return {'status': 'ok', 'deleted_id': agent_id}

    @router.post('/generate-prompt')
    async def generate_prompt(req: GeneratePromptRequest) -> dict:
        """Generate system prompt and agent settings via AI Architect model.
        
        Uses a language model to automatically generate agent configuration
        based on task description.
        
        Args:
            req: Request with task description and model selection.
            
        Returns:
            dict: Generated agent specification with recommended tools and settings.
            
        Raises:
            HTTPException: If task description is empty or model fails.
        """
        if not req.task_description.strip():
            raise HTTPException(status_code=400, detail='Task description cannot be empty')

        tool_ids = [t['id'] for t in _AVAILABLE_TOOLS]
        tool_desc = "\n".join([f"- {t['id']}: {t['name']} ({t['description']})" for t in _AVAILABLE_TOOLS])

        prompt_architect_query = f"""You are an experienced AI Agent Architect.
User wants to create a specialized agent for the ai-breadboard platform.

User's agent task:
"{req.task_description}"

Available system tools:
{tool_desc}

Generate complete agent specification in valid JSON format without markdown blocks:
{{
  "name": "Agent name (short, clear)",
  "description": "Brief description of agent role (1-2 sentences)",
  "system_prompt": "Detailed system instruction: role, reasoning rules (ReAct), tool selection, output format",
  "recommended_tools": ["tool_ids_from_list_above"],
  "temperature": 0.2,
  "max_steps": 15
}}
"""

        try:
            from src.fastapi.router_chat import get_chat_model
            model_key = req.model
            if req.provider == 'gemini_cli' and not model_key.startswith('gemini_cli:'):
                model_key = f'gemini_cli:{model_key}'
            elif req.provider == 'foundry' and not model_key.startswith('foundry:'):
                model_key = f'foundry:{model_key}'
            elif req.provider == 'ollama' and not model_key.startswith('ollama:'):
                model_key = f'ollama:{model_key}'

            llm = get_chat_model(model_key, system_instruction="You are an expert AI Agent Architect. Always return pure JSON.")
            
            # Call model
            if hasattr(llm, 'ask'):
                response_text = await llm.ask(prompt_architect_query)
            elif hasattr(llm, 'chat'):
                response_text = await llm.chat(prompt_architect_query)
            elif hasattr(llm, 'generate_response'):
                response_text = await llm.generate_response(prompt_architect_query)
            else:
                response_text = str(llm)

            # Clean JSON from possible ```json wrappers
            cleaned = response_text.strip()
            if cleaned.startswith('```'):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)

            parsed_data = json.loads(cleaned)
            # Validate recommended tools
            if 'recommended_tools' in parsed_data:
                parsed_data['recommended_tools'] = [
                    t for t in parsed_data['recommended_tools'] if t in tool_ids
                ]

            return {
                'status': 'ok',
                'data': parsed_data
            }
        except Exception as e:
            logger.error(f'[router_agents] Error in AI prompt generator: {e}')
            # Fallback to default structure on model failure
            return {
                'status': 'fallback',
                'data': {
                    'name': req.agent_name or 'Custom agent',
                    'description': req.task_description[:100],
                    'system_prompt': f"You are a specialized ai-breadboard agent.\nYour task: {req.task_description}\nUse provided tools when needed and provide clear answers.",
                    'recommended_tools': ['web_search'],
                    'temperature': 0.3,
                    'max_steps': 10
                },
                'error': str(e)
            }

    @router.post('/test')
    async def test_agent(req: TestAgentRequest) -> dict:
        """Interactive sandbox: test agent run with step tracing.
        
        Executes agent with provided configuration or inline settings,
        returning step-by-step execution trace.
        
        Args:
            req: Request with agent ID or inline config and test message.
            
        Returns:
            dict: Execution result with response, duration, and steps trace.
            
        Raises:
            HTTPException: If agent configuration not found or execution fails.
        """
        start_time = time.time()
        
        # Determine agent configuration
        target_config = {}
        if req.inline_config and isinstance(req.inline_config, AgentModel) and req.inline_config.name:
            target_config = req.inline_config.dict()
        elif req.agent_id:
            items = _get_agents_list()
            for item in items:
                if item.get('id') == req.agent_id:
                    target_config = item
                    break

        if not target_config:
            raise HTTPException(status_code=400, detail='Agent configuration not set for testing')

        provider = target_config.get('provider', 'gemini')
        model_name = target_config.get('model', 'gemini-2.5-flash')
        sys_prompt = target_config.get('system_prompt', '')
        tools = target_config.get('tools', [])

        steps = []
        steps.append({
            'step': 1,
            'type': 'thought',
            'content': f"Initializing agent '{target_config.get('name')}' [Provider: {provider}, Model: {model_name}]"
        })

        if tools:
            steps.append({
                'step': 2,
                'type': 'tool_init',
                'content': f"Connected tools ({len(tools)}): {', '.join(tools)}"
            })

        try:
            from src.fastapi.router_chat import get_chat_model
            model_key = model_name
            if provider == 'gemini_cli' and not model_key.startswith('gemini_cli:'):
                model_key = f'gemini_cli:{model_key}'
            elif provider == 'foundry' and not model_key.startswith('foundry:'):
                model_key = f'foundry:{model_key}'
            elif provider == 'ollama' and not model_key.startswith('ollama:'):
                model_key = f'ollama:{model_key}'

            llm = get_chat_model(model_key, system_instruction=sys_prompt)
            
            steps.append({
                'step': 3,
                'type': 'action',
                'content': f"Processing incoming message: '{req.test_message}'"
            })

            # Execute model call
            if hasattr(llm, 'ask'):
                res = await llm.ask(req.test_message)
            elif hasattr(llm, 'chat'):
                res = await llm.chat(req.test_message)
            else:
                res = "Model response received."

            duration_ms = int((time.time() - start_time) * 1000)

            steps.append({
                'step': 4,
                'type': 'finish',
                'content': f"Completed successfully in {duration_ms} ms."
            })

            return {
                'status': 'ok',
                'response': res,
                'duration_ms': duration_ms,
                'steps': steps
            }
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f'[router_agents] Error in agent test run: {e}')
            steps.append({
                'step': len(steps) + 1,
                'type': 'error',
                'content': f"Execution error: {str(e)}"
            })
            return {
                'status': 'error',
                'response': f"Error during agent execution: {str(e)}",
                'duration_ms': duration_ms,
                'steps': steps
            }

    return router
