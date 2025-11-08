# Usage Guide - Grocery Delivery SuperApp

## Agent Type

The app uses **Amazon Nova Auto agents**:

### Amazon Nova Auto (Natural Language)
- Uses Amazon Nova Auto with natural language instructions
- Requires `GEMINI_API_KEY` for weight estimation
- Requires `NOVA_ACT_API_KEY` for Nova Auto
- Simplest implementation - just describe what to do
- Batches items (5 per batch) for better reliability
- Based on proven `instacart_nova_auto.py` and `uber_nova_auto.py`
- Runs in background threads to avoid asyncio conflicts

---

## Command Line Options

### Basic Usage

```bash
# Add items to cart across all platforms
python main.py milk eggs bread

# Uses default ingredients if none provided
python main.py  # Uses: milk, eggs, paneer, tomatoes
```

---

## Full Workflow Example

### Run the App

```bash
# Nova Auto agents (natural language)
python main.py milk eggs paneer
```

Note: Nova Auto will handle authentication and session management automatically.

---

## What Happens

1. **Search & Order**: Agents search for ingredients on all platforms in parallel
2. **Cart Detail**: Extract actual cart state from each platform
3. **User Edits**: (Simulated) Record any cart modifications
4. **Apply Diffs**: Apply edits to actual carts
5. **Final Details**: Re-extract cart after changes
6. **Mock Payment**: Demo Knot API transaction data

---

## Troubleshooting

### Nova Act Errors
Check environment variables are set:
```bash
# In .env file
GEMINI_API_KEY=your_gemini_key
NOVA_ACT_API_KEY=your_nova_key
```

---

## Files

- **Nova Auto Agents**: `agents/search_order_agent_nova.py`
- **Orchestrator**: `orchestrator_nova.py`
- **Main**: `main.py`
- **Tests**: `tests/nova_sync_smoke_instacart.py`, `tests/nova_async_wrapper_smoke.py`

## Testing

### Sync Smoke Test
Tests basic NovaAct functionality on Instacart:
```bash
python tests/nova_sync_smoke_instacart.py
```

### Async Wrapper Smoke Test
Tests the threading wrapper with any platform:
```bash
python tests/nova_async_wrapper_smoke.py -p instacart milk
python tests/nova_async_wrapper_smoke.py -p ubereats milk eggs
python tests/nova_async_wrapper_smoke.py -p doordash bread
```

