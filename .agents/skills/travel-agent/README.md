---
name: travel-agent
description: Autonomous travel and flight search agent leveraging multi-engine search and MCP tools for airline ticket discovery, comparison, and pricing.
---

# Travel Agent Skill

## Overview
	ravel-agent is an autonomous AI agent engineered for the AI-Breadboard platform to discover, compare, and price airline tickets, flight routes, and itineraries.

## Core Capabilities
- **Multi-Engine Search**: Dispatches queries across Google Search Grounding, Google Antigravity (AGY), Gemini CLI, and MCP web scrapers.
- **MCP Integration**: Connects with Playwright MCP for live aggregator parsing (Google Flights, Skyscanner, Aviasales, Expedia) and Fetch MCP.
- **Flight Price Calculation**: Evaluates complex fares including base price, baggage fees, local taxes, multi-passenger multipliers, and currency conversion.
- **Intelligent Comparison Matrix**: Segregates flights into:
  - 🟢 **Best Budget**: Lowest total cost.
  - ⚡ **Fastest / Direct**: Shortest duration and minimal layovers.
  - ⭐ **Best Value**: Optimal balance between comfort, duration, and price.

## Available Tools
1. light_search(origin, destination, date, return_date, passengers, travel_class): Dispatches flight queries across providers.
2. light_price_calculator(base_price, currency, baggage_fee, passengers, tax_rate, discount_percent): Computes final ticket prices.
3. web_search(query): Grounded web search.
4. ag_search(query, top_k): Queries user preferences, frequent flyer details, and passport guidelines.
5. python_eval(code): Computes timezone differences and layover mathematics.

## Usage Example
`python
import asyncio
from src.ai.agents import TravelAgent

async def main():
    agent = TravelAgent()
    result = await agent.search("Find flights from Tel Aviv (TLV) to Paris (CDG) on October 15, 2026, 1 passenger, economy")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
`
"@ | Out-File -FilePath ".agents\skills\travel-agent\SKILL.md" -Encoding utf8

@"
# Travel Agent Package

Autonomous flight search and travel itinerary agent for AI-Breadboard.
