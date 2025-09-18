"""Application package bootstrap logic."""
from __future__ import annotations

import sys
from typing import ForwardRef

# NOTE: Older Pydantic releases (<=1.10.12) do not pass the required
# ``recursive_guard`` keyword argument when running on Python 3.11+.
# This triggers ``TypeError: ForwardRef._evaluate() missing 1 required
# keyword-only argument: 'recursive_guard'`` while FastAPI starts up.
#
# The project already pins a recent Pydantic version in ``requirements.txt``.
# However, some environments might still load an older global installation
# before the pinned one is installed.  To keep the development experience
# smoother, we patch ``typing.ForwardRef._evaluate`` so that calls missing the
# keyword get upgraded at runtime.  The patch is safe for newer versions too,
# as the ``recursive_guard`` provided by those versions is simply forwarded.
if sys.version_info >= (3, 11):
    _original_forward_evaluate = ForwardRef._evaluate  # type: ignore[attr-defined]

    def _patched_forward_evaluate(self: ForwardRef, globalns, localns, *args, **kwargs):  # type: ignore[override]
        if "recursive_guard" not in kwargs:
            args_list = list(args)
            recursive_guard = None
            if args_list:
                candidate = args_list[-1]
                if isinstance(candidate, set):
                    recursive_guard = args_list.pop()
            if recursive_guard is None:
                recursive_guard = set()
            kwargs["recursive_guard"] = recursive_guard
            args = tuple(args_list)
        return _original_forward_evaluate(self, globalns, localns, *args, **kwargs)

    ForwardRef._evaluate = _patched_forward_evaluate  # type: ignore[assignment]

__all__ = []
