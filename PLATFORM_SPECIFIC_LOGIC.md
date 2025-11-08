# Platform-Specific Logic for Nova Act Agents

## Overview

Each platform (Instacart, UberEats, DoorDash) has a unique workflow for browsing and adding items to cart. This document explains the platform-specific logic implemented in our unified agent system.

## Key Changes Applied

### 1. **Fixed Windows Path Issue** ✅
**Problem**: NovaAct couldn't find files when using relative paths (`./user_data_instacart`)

**Solution**: Convert to absolute paths using `os.path.abspath()`

```python
# Before (BROKEN on Windows):
user_data_dir=self.config["user_data_dir"]  # "./user_data_instacart"

# After (WORKS on Windows):
user_data_path = os.path.abspath(self.config["user_data_dir"])
user_data_dir=user_data_path  # "D:\STUFF\Projects\...\user_data_instacart"
```

**Applied to**:
- `agents/search_order_agent_nova.py` (line 118)
- `agents/cart_detail_agent_nova.py` (line 47)
- `agents/edit_cart_agent_nova.py` (line 46)
- `agents/signin_agent_nova.py` (line 51)

### 2. **Platform-Specific Workflows** ✅
**Problem**: Generic instructions don't work - each platform has different UI/UX

**Solution**: Separate instruction builders based on proven reference implementations

## Platform Workflows

### Instacart (`instacart_nova_auto.py` pattern)

```
┌─────────────────────────────────────────┐
│ 1. Close sign-up popups                 │
│ 2. Handle CAPTCHA if present            │
│ 3. Close any popups                     │
│ 4. Search for "Stop & shop" store       │ ← Direct store access
│ 5. Click on store                       │
│ 6. Close popups                         │
│ 7. Search and add items                 │
└─────────────────────────────────────────┘
```

**Key Feature**: Direct store selection (no address needed upfront)

### UberEats (`uber_nova_auto.py` pattern)

```
┌─────────────────────────────────────────┐
│ 1. Close sign-up popups                 │
│ 2. Set delivery address FIRST           │ ← Address required!
│ 3. Handle CAPTCHA if present            │
│ 4. Close any popups                     │
│ 5. Search for grocery store             │
│ 6. Click on store                       │
│ 7. Close popups                         │
│ 8. Search and add items                 │
└─────────────────────────────────────────┘
```

**Key Feature**: Address MUST be set before store selection

### DoorDash (Similar to UberEats)

```
┌─────────────────────────────────────────┐
│ 1. Close sign-up popups                 │
│ 2. Set delivery address FIRST           │ ← Address required!
│ 3. Handle CAPTCHA if present            │
│ 4. Close any popups                     │
│ 5. Search for grocery store             │
│ 6. Click on store                       │
│ 7. Close popups                         │
│ 8. Search and add items                 │
└─────────────────────────────────────────┘
```

**Key Feature**: Same workflow as UberEats (address-first pattern)

## Implementation Details

### File: `agents/search_order_agent_nova.py`

```python
def _build_instruction_for_items(self, items: List[str], is_first_batch=True) -> str:
    """Build natural language instruction for Nova Auto - platform-specific logic"""
    
    if is_first_batch:
        # Platform-specific initialization
        if "instacart" in self.platform_name:
            instruction = "Close popups → Find 'Stop & shop' → Add items"
        
        elif "ubereats" in self.platform_name:
            instruction = "Close popups → Set address → Find store → Add items"
        
        elif "doordash" in self.platform_name:
            instruction = "Close popups → Set address → Find store → Add items"
    
    # Add items (same for all platforms)
    for item in items:
        instruction += f"Search for '{item}'. Add 1 to cart. "
```

### Why This Matters

1. **Instacart**: Allows browsing without address (location-based defaults)
2. **UberEats/DoorDash**: Require address to show available stores/restaurants
3. **Order Matters**: Setting address AFTER searching breaks UberEats/DoorDash
4. **Store Names**: Instacart uses specific store names, delivery platforms use generic "grocery store"

## Testing Address

All platforms configured to use:
```
89 Northampton St, Boston, MA 02118
```

This is a test address that all platforms recognize.

## Subsequent Batches

After the first batch, all platforms use simplified instructions:
```
"If any popup appears, close it. "
"Go to the store page if not already there. "
```

This works because:
- Address is already set (UberEats/DoorDash)
- Store is already selected (all platforms)
- Session persists the navigation state

## Benefits of Unified Agent

Despite platform differences, we maintain ONE agent class that:
- ✅ Handles all 3 platforms
- ✅ Uses platform-specific logic where needed
- ✅ Shares common code (item normalization, session management)
- ✅ Based on proven working implementations

## Future Enhancements

1. **Configurable Store Names**: Allow users to specify preferred stores
2. **Configurable Address**: Allow users to set their delivery address
3. **Additional Platforms**: Easy to add new platforms with their specific workflows
4. **Smart Fallbacks**: If store not found, try alternative stores

## Success Criteria

✅ **Step 1 Complete**: Fixed Windows path issues with absolute paths
✅ **Step 2 Complete**: Implemented platform-specific workflows
🔜 **Next**: Test with actual platforms to verify workflows work

---

**Last Updated**: 2025-11-08
**Status**: Ready for testing

