# Usage Guide - Grocery Delivery SuperApp

## Agent Types

The app supports **two types of agents**:

### 1. **Playwright Agents** (Default, Recommended) `-2`
- Pure DOM selectors based on proven `instacart_agent.py` pattern
- **No LLM required** - works immediately
- Faster and more reliable
- Uses heuristics and explicit selectors

### 2. **BrowserUse Agents** (AI-Powered) `-1`
- Uses Gemini AI + BrowserUse for intelligent automation
- Requires `GEMINI_API_KEY` in `.env`
- More flexible, adapts to UI changes
- **Currently has compatibility issues** - use Playwright for now

---

## Command Line Options

### Basic Usage (Playwright - Default)

```bash
# Uses Playwright agents by default
python main.py milk eggs bread

# Explicit Playwright flag
python main.py -2 milk eggs bread
python main.py --playwright milk eggs bread
```

### BrowserUse (AI-Powered)

```bash
# Use BrowserUse agents with Gemini AI
python main.py -1 milk eggs bread
python main.py --browseruse milk eggs bread
```

### No Ingredients (Uses Defaults)

```bash
# Uses: milk, eggs, paneer, tomatoes
python main.py
python main.py -2
```

---

## Full Workflow Example

### Step 1: Sign In to Platforms (One-time)

```bash
python -m agents.signin_agent instacart
python -m agents.signin_agent ubereats
python -m agents.signin_agent doordash
```

Follow the prompts to log in manually. Sessions persist in `user_data_*` directories.

### Step 2: Run the App

```bash
# Playwright agents (recommended)
python main.py -2 milk eggs paneer

# BrowserUse agents (if Gemini API working)
python main.py -1 milk eggs paneer
```

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

### "Not logged in" Errors
Run signin agents again:
```bash
python -m agents.signin_agent <platform>
```

### BrowserUse Not Working
Use Playwright instead:
```bash
python main.py -2 milk eggs
```

### Browsers Not Opening
Check if Playwright is installed:
```bash
playwright install chromium
```

---

## Files

- **Playwright Agents**: `agents/*_playwright.py`
- **BrowserUse Agents**: `agents/search_order_agent.py`, `agents/edit_cart_agent.py`
- **Orchestrators**: `orchestrator_playwright.py`, `orchestrator.py`
- **Main**: `main.py` (handles CLI args)

