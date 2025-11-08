# Grocery Delivery SuperApp MVP

Multi-platform grocery ordering super app with parallel browser automation agents, cart management with diff tracking, and Knot API integration for transaction demonstration.

## Features

- **Multi-Platform Support**: Instacart, Uber Eats, DoorDash
- **Parallel Execution**: All platforms processed simultaneously using asyncio
- **AI-Powered Automation**: Uses Gemini + BrowserUse for resilient browser automation
- **Cart Diff Tracking**: Record and apply user edits before checkout
- **Session Management**: Persistent browser contexts maintain login state
- **Knot API Integration**: Transaction data demonstration with SKU-level details

## Architecture

### Components

1. **Agents** (`agents/`)
   - `SignInAgent`: Manual user authentication with session persistence
   - `SearchOrderAgent`: AI-powered search and cart addition (Gemini + BrowserUse)
   - `EditCartAgent`: Apply user cart modifications
   - `CartDetailAgent`: Extract cart information

2. **Orchestrator** (`orchestrator.py`)
   - Parallel execution coordinator using `asyncio.gather()`
   - Exception isolation per platform
   - Cart state persistence

3. **Data Models** (`models/`)
   - `CartItem`, `PlatformCart`, `CartDiff`, `CartState`
   - JSON serialization for persistence

4. **Knot API** (`knot_api/`)
   - Transaction sync with mock data fallback
   - SKU-level product data

5. **Main Entry** (`main.py`)
   - CLI application
   - 6-step workflow orchestration

## Installation

### Prerequisites

- Python 3.11+
- 8-16GB RAM (for parallel browser instances)
- GEMINI_API_KEY in `.env` file

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Verify installation
python -c "import playwright; import browser_use; print('Ready!')"
```

### Environment Configuration

Create `.env` file in project root:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

## Usage

### Step 1: Sign In to Platforms

Run SignIn agent for each platform (one-time setup):

```bash
python -m agents.signin_agent instacart
python -m agents.signin_agent ubereats
python -m agents.signin_agent doordash
```

A browser will open - manually log in. Session persists in `user_data_<platform>/` directories.

### Step 2: Run Complete Workflow

```bash
# With default ingredients (milk, eggs, paneer, tomatoes)
python main.py

# With custom ingredients
python main.py milk eggs bread cheese tomatoes
```

### Workflow Steps

1. **Search & Order**: Agents search for ingredients on all platforms in parallel
2. **Extract Cart Details**: Retrieve actual cart state from each platform
3. **User Edits**: (Simulated) Record cart modifications as diffs
4. **Apply Diffs**: Apply user edits to actual platform carts
5. **Final Cart State**: Re-extract cart details after edits
6. **Mock Payment**: Demonstrate Knot API transaction structure

### Output

- Console: Step-by-step progress and cart summaries
- File: `data/cart_state.json` with complete cart state

## Testing

Run phase-specific tests:

```bash
python tests/test_phase1.py  # Core utilities
python tests/test_phase2.py  # Data models
python tests/test_phase3.py  # Agents (structure only)
python tests/test_phase4.py  # Knot API
python tests/test_phase5.py  # Orchestrator
python tests/test_phase6.py  # Main entry point
```

## Configuration

### Platform Configuration (`config/platforms.py`)

Each platform has:
- Name and merchant ID (for Knot API)
- URLs (search, cart, login)
- User data directory for session storage

### Adding New Platforms

1. Add platform config to `config/platforms.py`
2. Add merchant ID to `knot_api/config.py` (if available)
3. Update platform list in `main.py`

## Data Models

### CartItem
- Tracks individual product with ingredient request, actual product name, price, quantity, status

### PlatformCart
- Complete cart for one platform with items list, fees, totals
- Methods: `add_item()`, `remove_item()`, `calculate_totals()`

### CartDiff
- Records user edits (add/remove/update_quantity)
- Tracked as unapplied until Edit Cart agent executes

### CartState
- Global state manager for all platform carts and diffs
- JSON persistence to `data/cart_state.json`

## Architecture Decisions

### Why BrowserUse?
- **Resilient**: AI adapts to UI changes without brittle selectors
- **Cross-Platform**: Same logic works across different sites
- **Popup Handling**: Automatically dismisses blocking elements

### Why Parallel Execution?
- **Speed**: Process 3-4 platforms simultaneously
- **Isolation**: One platform failure doesn't affect others
- **User Experience**: Faster overall workflow

### Why Session Persistence?
- **Convenience**: Login once, reuse sessions
- **Security**: No password storage
- **Reliability**: Fewer authentication failures

## Knot API Integration

Knot API demonstrates transaction data structure:

- Retrieves sample transactions with SKU-level items
- Shows what real order data looks like
- Falls back to mock data if API unavailable
- Used for payment demonstration only (no actual payments)

## Troubleshooting

### Session Expired
Re-run SignIn agent for the platform:
```bash
python -m agents.signin_agent <platform>
```

### Browser Automation Fails
- Check internet connection
- Verify Playwright chromium installed
- Check platform didn't change UI significantly
- Review logs for specific errors

### API Key Issues
- Verify GEMINI_API_KEY in `.env`
- Check API key has sufficient quota
- Test with `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GEMINI_API_KEY'))"`

### Resource Issues
- Reduce number of platforms processed
- Close other applications
- Ensure 8GB+ RAM available

## Development

### Project Structure

```
HackPton_Delivery_App/
├── agents/              # Browser automation agents
├── config/              # Platform configurations
├── data/                # Runtime cart state storage
├── knot_api/            # Knot API integration
├── models/              # Data models
├── tests/               # Phase-specific tests
├── utils/               # Shared utilities
├── orchestrator.py      # Parallel execution coordinator
├── main.py              # CLI entry point
└── requirements.txt     # Dependencies
```

### Code Quality

- Type hints throughout
- Comprehensive docstrings
- Logging at INFO level
- Exception handling per platform
- Retry logic with exponential backoff

## Limitations (MVP)

- Mock payment only (no real transactions)
- No price comparison/optimization
- First available product selected
- Manual sign-in required
- Desktop/local execution only

## Future Enhancements

- Web UI for cart management
- Price comparison across platforms
- Smart product matching
- Recipe-to-ingredients API (Gemini)
- Cloud deployment
- Real payment integration
- Order tracking

## License

MIT License - HackPrinceton 2024

## Credits

- **Browser Automation**: BrowserUse + Playwright
- **AI Models**: Google Gemini (gemini-1.5-flash)
- **Transaction API**: Knot API
- **Platforms**: Instacart, Uber Eats, DoorDash

