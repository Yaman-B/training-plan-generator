"""Tracing helper.

`observe` is Langfuse's decorator when tracing is switched on, and a no-op passthrough
when it isn't. That way the rest of the codebase can decorate its functions freely
without caring whether Langfuse is configured.
"""

from tpg.config import LANGFUSE_ENABLED

if LANGFUSE_ENABLED:
    from langfuse import observe
else:

    def observe(*args, **kwargs):
        """No-op stand-in: hands the function back untouched."""
        # Bare @observe (no parentheses)
        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]

        # Called form: @observe(...)
        def decorator(func):
            return func

        return decorator
