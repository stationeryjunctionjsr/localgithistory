"""Simple synchronous retry decorator with exponential back-off.

Intended for network calls to external services (MSG91, OCI) where transient
failures are expected and a few quick retries are safe to attempt.
"""

import functools
import logging
import time
from typing import Any, Callable, Tuple, Type, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator that retries *func* up to *max_attempts* times on *exceptions*.

    Args:
        max_attempts: Total number of tries (first attempt + retries).
        initial_delay: Seconds to wait before the first retry.
        backoff_factor: Multiplier applied to the delay on each subsequent retry.
        exceptions: Exception types that trigger a retry.  Other exceptions
            propagate immediately without retrying.

    Example::

        @with_retry(max_attempts=3, exceptions=(requests.exceptions.ConnectionError,))
        def send_sms(phone: str, otp: str) -> bool:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exc: Exception = RuntimeError("No attempts made")
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        logger.warning(
                            "Attempt %d/%d failed for %s: %s — retrying in %.1fs",
                            attempt,
                            max_attempts,
                            func.__qualname__,
                            exc,
                            delay,
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            "All %d attempts failed for %s: %s",
                            max_attempts,
                            func.__qualname__,
                            exc,
                        )
            raise last_exc

        return wrapper  # type: ignore[return-value]

    return decorator
