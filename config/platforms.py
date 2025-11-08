# config/platforms.py

PLATFORM_CONFIGS = {
    "instacart": {
        "name": "Instacart",
        "merchant_id": 40,  # Knot API merchant ID
        "search_url": "https://www.instacart.com/store/search?q={}",
        "cart_url": "https://www.instacart.com/store/cart",
        "login_url": "https://www.instacart.com/login",
        "user_data_dir": "./user_data_instacart",
    },
    "ubereats": {
        "name": "Uber Eats",
        "merchant_id": 36,
        "search_url": "https://www.ubereats.com/search?q={}",
        "cart_url": "https://www.ubereats.com/cart",
        "login_url": "https://www.ubereats.com/login",
        "user_data_dir": "./user_data_ubereats",
    },
    "doordash": {
        "name": "DoorDash",
        "merchant_id": 19,
        "search_url": "https://www.doordash.com/store/search/?query={}",
        "cart_url": "https://www.doordash.com/cart/",
        "login_url": "https://www.doordash.com/consumer/login",
        "user_data_dir": "./user_data_doordash",
    },
}

# Global settings
BROWSER_ARGS = ["--disable-blink-features=AutomationControlled"]
HEADLESS = False  # Always visible for demo/debugging
MAX_RETRIES = 3
PARALLEL_EXECUTION = True

