# AI Simulation & Synthetic Data Generator

## Overview

The `src/ai/simulation` package provides an extensible simulation engine for generating realistic mock entities (such as contracts, agreements, invoices, profiles, and arbitrary custom records) upon user requests.

Every generated mock interaction is automatically persisted into the user's isolated personal **Client RAG** vector storage (`src/ai/gemini/user_query_rag.py`). As a result, subsequent and follow-up questions from the user reliably retrieve the exact simulated facts directly from their RAG index.

---

## Architecture & Flow

```
User: "Найди договор с ivan_petrov"
       │
       ▼
 ┌───────────────────────────────────────────────┐
 │ SimulationEngine (src/ai/simulation)          │
 │                                               │
 │  1. Selects Generator (ContractGenerator)     │
 │  2. Generates mock data (№, dates, sums)      │
 │  3. Formats response text & structured meta   │
 └──────────────────────┬────────────────────────┘
                        │
                        ├──────────────────────────┐
                        ▼                          ▼
               Returns Mock Response     index_user_query(...)
               to User                   into Client RAG
                                                   │
                                                   ▼
Follow-up: "Какой номер договора с ivan_petrov?"   │
                   │                               │
                   ▼                               │
         search_user_context() ◄───────────────────┘
         Retrieves generated contract context!
```

---

## Key Components

- **`SimulationEngine`**: Central coordinator and lifecycle manager. Routes requests to registered generators and indexes results in RAG.
- **`BaseSimulationGenerator`**: Interface for building domain-specific simulation generators.
- **`ContractSimulationGenerator`**: Specialized generator for commercial contracts and agreements, extracting usernames/counterparties and generating deterministic realistic terms.
- **`GenericSimulationGenerator`**: Fallback and dynamic generator for new entity types defined during dialogues.
- **`models.py`**: Pydantic/dataclass models (`SimulationRequest`, `SimulationResult`, `EntityType`).

---

## Usage Example

```python
import asyncio
from src.ai.simulation import SimulationEngine, SimulationRequest

async def main():
    engine = SimulationEngine()
    
    # Simulate contract generation for a user
    request = SimulationRequest(
        query="Найди договор с ivan_petrov",
        user_id="user_123",
        api_key="your_gemini_api_key",
    )
    
    result = await engine.simulate(request, auto_index=True)
    print(result.generated_text)
    print(f"Indexed in RAG: {result.is_indexed}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Extending Simulation for New Entities

To add a new entity type on the fly:

```python
from src.ai.simulation import BaseSimulationGenerator, SimulationRequest, SimulationResult

class InvoiceGenerator(BaseSimulationGenerator):
    @property
    def entity_type(self) -> str:
        return "invoice"

    def can_handle(self, request: SimulationRequest) -> bool:
        return "счет" in request.query.lower() or "invoice" in request.query.lower()

    async def generate(self, request: SimulationRequest) -> SimulationResult:
        # Custom mock logic...
        return SimulationResult(
            entity_type="invoice",
            title="Счет на оплату",
            generated_text="### Счет № ...",
            structured_data={"invoice_num": "INV-101"}
        )

# Register into engine
engine.register_generator(InvoiceGenerator())
```
