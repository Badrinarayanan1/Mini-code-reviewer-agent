from typing import Any, Callable, Dict

ToolFunc = Callable[[Any], Any]


class ToolRegistry:
    """Registry of named tools (Python callables)."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolFunc] = {}

    def register(self, name: str, func: ToolFunc) -> None:
        if not callable(func):
            raise TypeError("Tool must be callable")
        self._tools[name] = func

    def get(self, name: str) -> ToolFunc:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered")
        return self._tools[name]

    def list_tools(self) -> Dict[str, str]:
        return {name: func.__name__ for name, func in self._tools.items()}


tool_registry = ToolRegistry()
