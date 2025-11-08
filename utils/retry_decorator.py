# utils/retry_decorator.py

import asyncio
from functools import wraps
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)

def async_retry(
    max_attempts: int = 3,
    backoff_base: float = 2.0,
    backoff_multiplier: float = 2.0,
    on_retry_callback: Optional[Callable] = None
):
    """
    Decorator for async functions with exponential backoff retry
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        backoff_base: Initial wait time in seconds (default: 2.0)
        backoff_multiplier: Multiplier for exponential backoff (default: 2.0)
        on_retry_callback: Optional async function to call before retry
                          Signature: async def callback(attempt, exception, *args, **kwargs)
    
    Returns:
        Decorated function that retries on any exception
    
    Example:
        @async_retry(max_attempts=5, backoff_base=1.0)
        async def unreliable_operation():
            # might fail
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts. "
                            f"Last error: {e}"
                        )
                        raise
                    
                    # Calculate backoff time
                    wait_time = backoff_base * (backoff_multiplier ** (attempt - 1))
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry_callback:
                        try:
                            await on_retry_callback(attempt, e, *args, **kwargs)
                        except Exception as callback_error:
                            logger.warning(f"Retry callback failed: {callback_error}")
                    
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    return decorator

