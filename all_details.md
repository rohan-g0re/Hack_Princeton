# Grocery Delivery SuperApp: Technical Specification

This document provides a detailed technical overview of the Grocery Delivery SuperApp, a project designed to unify the online grocery shopping experience across multiple platforms.

## 1. Project Vision & Goals

### 1.1. Overview

The primary goal of this project is to build a "superapp" that acts as a single, centralized interface for ordering groceries from various online delivery services like Instacart, UberEats, and DoorDash. The current user experience is fragmented, requiring users to visit multiple websites or apps to compare prices and availability. This superapp eliminates that friction by automating the process of cart management across platforms.

The system is designed to be robust and resilient, leveraging AI-powered browser automation to navigate dynamic web UIs, handle popups, and manage complex cart states.

### 1.2. Core User Workflow

The application follows a seamless, user-centric workflow:

1.  **Recipe to Ingredients**: The user starts with a simple text query, such as a recipe name (e.g., "Caesar Salad"). An LLM (like Gemini) processes this query to generate a comprehensive list of required ingredients.
2.  **Shopping List Finalization**: The generated list is presented to the user, who can then customize it by removing items they already have or adding other groceries.
3.  **Parallel Cart Population**: Once the list is finalized, the system dispatches autonomous `Search & Order` agents. These agents work in parallel to visit each configured grocery platform (e.g., Instacart, UberEats), search for the items on the list, and add them to the respective carts.
4.  **Unified Cart View**: The superapp presents a consolidated view of all platform carts. The user can see which items were added to each platform's cart and the associated costs.
5.  **Cross-Platform Cart Editing**: The user can expand the details for each platform's cart and make modifications. For example, if milk was added to carts on both Instacart and UberEats, the user can choose to remove it from the UberEats cart directly within the superapp. These changes are recorded as "diffs" against the current cart state.
6.  **Checkout & Diff Application**: When the user proceeds to checkout, the system triggers `Edit Cart` agents. These agents apply the recorded diffs to the live carts on the actual platforms, ensuring the final cart composition matches the user's edits.
7.  **Mock Payment & Transaction Capture**: After the final cart details are fetched and displayed, the user can click a "Pay" button. This action simulates a mock payment and invokes the Knot API to demonstrate the retrieval of detailed, SKU-level transaction data, which is then stored for record-keeping.

## 2. System Architecture

### 2.1. High-Level Design

The application is architected as a Python-based system driven by a central **Orchestrator**. This orchestrator manages the parallel execution of multiple specialized, autonomous **Agents**. Each agent is responsible for a specific part of the workflow, interacting with web platforms through a combination of direct browser automation and AI-driven control.

The entire system is designed around a persistent state model, where the contents of all platform carts and user-initiated changes are continuously saved to a JSON file (`data/cart_state.json`). This ensures resilience and allows the workflow to be paused and resumed.

![](https://i.imgur.com/your_architecture_diagram_url.png) <!-- Placeholder for a diagram -->

### 2.2. Core Components

The architecture is modular, with a clear separation of concerns:

| Component | File(s) | Responsibility |
| :--- | :--- | :--- |
| **Orchestrator** | `orchestrator.py` | The central coordinator. Uses `asyncio.gather()` to launch and manage agents for all platforms in parallel. It directs the overall workflow from searching for items to applying final edits. |
| **Agents** | `agents/*.py` | Specialized modules that perform actions on the web platforms. There are four distinct types of agents. |
| **Data Models** | `models/cart_models.py` | A set of Python `dataclasses` that define the structure for all data, including `CartItem`, `PlatformCart`, `CartDiff`, and the global `CartState`. This ensures type safety and provides a clear data contract between components. |
| **Configuration** | `config/platforms.py` | A centralized file containing all platform-specific information (URLs, selectors, merchant IDs for the Knot API) and global settings (headless mode, retry attempts). |
| **Utilities** | `utils/*.py` | Common, reusable code shared across agents. This includes a robust `@async_retry` decorator for handling transient network or UI failures and an aggressive `dismiss_popups` function. |
| **Knot API Client** | `knot_api/*.py` | A dedicated client for interacting with the Knot API. It includes logic for making API calls and a fallback mechanism to generate realistic mock data for demonstration purposes. |
| **Entry Point** | `main.py` | The main executable script that initializes the orchestrator and runs the end-to-end workflow based on command-line inputs. |

### 2.3. Technology Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Core Language** | Python 3.9+ | For all application logic. |
| **Concurrency** | `asyncio` | To enable high-performance, parallel execution of agents across multiple platforms. |
| **Web Automation**| Playwright | Provides a robust foundation for browser control, context management, and session persistence. |
| **AI Automation** | `browser-use` | An AI-powered layer on top of Playwright. It uses an LLM (GPT-4o) to interpret natural language tasks (e.g., "add milk to cart") and execute them, making the automation resilient to UI changes. |
| **LLMs** | GPT-4o, Gemini | GPT-4o powers the `browser-use` agent's reasoning capabilities. Gemini is used in the initial phase to generate ingredient lists from recipes. |
| **Data Persistence**| JSON | A simple `cart_state.json` file is used for lightweight, human-readable state management, avoiding the overhead of a database for this MVP. |
| **Dependency Mgmt**| `pip` & `requirements.txt`| Standard Python package management. |

## 3. Product Overview

### 3.1. Elevator Pitch

A single app that turns “I want Caesar salad tonight” into a ready-to-checkout set of carts across Instacart, UberEats, and other platforms—automatically searching, adding items, syncing edits, and presenting one unified, editable view with a mock checkout to capture final transaction details.

### 3.2. The Problem We Solve

- Fragmented experiences: Users juggle multiple apps/sites to find the same groceries.
- Manual, repetitive work: Searching, comparing, and adding the same items across platforms is time-consuming.
- Cart drift: Edits in one platform aren’t reflected elsewhere, causing confusion.
- Poor visibility: There’s no consolidated, platform-agnostic view of what’s in each cart.
- Checkout friction: Users frequently discover missing items or misaligned carts at the last step.

### 3.3. Who It’s For

- Home cooks who plan meals and want the simplest path from recipe to groceries.
- Busy professionals who want time savings over platform micro-optimization.
- Power users who want to compare availability and item-level differences across platforms.
- Early adopters/tech-savvy users comfortable with an AI-assisted automation layer.

### 3.4. Core Capabilities

- Recipe-to-ingredients: Convert a meal idea into a curated ingredients list using an LLM.
- Parallel cart population: Dispatch agents to fill carts across multiple platforms simultaneously.
- Unified cart dashboard: See each platform’s cart as a card with expandable line items and prices.
- Cross-platform cart editing: Add/remove items per platform; changes are tracked as diffs.
- Diff application at checkout: Apply all recorded changes back to the live platform carts.
- Mock payment & transaction capture: Simulate payment and retrieve transaction-like detail via Knot API.
- Session persistence: Maintain login sessions so agents can operate with minimal user interventions.

### 3.5. End-to-End Experience (User Journey)

1. Enter a food intent (e.g., “Caesar salad for 2”).
2. Review the suggested ingredient list; remove items you already have, add extras you want.
3. Start automation. Agents open each platform, search items, and add them to carts in parallel.
4. View platform cards in the superapp, expand to inspect items, quantities, and prices.
5. Make edits per platform (e.g., remove milk from UberEats while keeping it on Instacart). These edits are stored as diffs.
6. Click “To Checkout.” Edit Cart agents apply diffs to real carts to align with your final decisions.
7. See final cart details and totals. Click “Pay” to run a mock payment and capture transaction data.

### 3.6. What the Product Is Not (Initial Non‑Goals)

- Not a price-comparison or optimizer (yet). We prioritize completeness and convenience over optimal pricing.
- Not a real payment processor. The “Pay” action is a mock that records transaction-like data.
- Not a marketplace. We don’t fulfill orders; we orchestrate carts on existing platforms.
- Not an API scraper. We use AI-guided browser automation for resilience to UI changes.

### 3.7. Example Scenarios

- Single-meal prep: “Stir fry tonight” → ingredients list → carts populated on Instacart and DoorDash → remove tofu on DoorDash only → finalize and mock pay.
- Weekly staples: “Milk, eggs, bread, spinach” → quick add across platforms → compare availability by expanding cards → remove duplicates on one platform → proceed.
- Dietary preferences: Add “gluten-free tortilla” and “lactose-free milk” to the list → agents search best matches per platform → user reviews and trims per-card.

### 3.8. Success Metrics (Early)

- Task time saved (query-to-ready-to-checkout) vs. manual flows.
- Cart accuracy rate: Percentage of items correctly added and preserved post-diff.
- Diff application success rate across platforms.
- Session persistence rate across runs (reduced re-logins).
- User completion rate from list finalization to mock payment.
