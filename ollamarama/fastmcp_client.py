from __future__ import annotations

import asyncio
import json
import shlex
from typing import Any, Dict, List, Mapping, Sequence

from fastmcp import Client
import mcp.types


class FastMCPClient:
    """Minimal wrapper around fastmcp.Client for tool discovery and calls."""

    def __init__(self, servers: Mapping[str, Any]) -> None:
        config: Dict[str, Dict[str, Any]] = {}
        for name, spec in servers.items():
            if isinstance(spec, str):
                spec = spec.strip()
                if not spec:
                    continue
                if spec.startswith("http://") or spec.startswith("https://"):
                    config[name] = {"url": spec}
                else:
                    parts = shlex.split(spec)
                    if not parts:
                        continue
                    config[name] = {"command": parts[0], "args": parts[1:]}
            elif isinstance(spec, Sequence) and not isinstance(spec, (bytes, bytearray, str)):
                parts = list(spec)
                if not parts:
                    continue
                config[name] = {"command": parts[0], "args": parts[1:]}
            elif isinstance(spec, Mapping):
                config[name] = dict(spec)

        if not config:
            raise ValueError("No valid MCP servers provided")

        self._client = Client({"mcpServers": config})
        # map public tool name -> internal name used by fastmcp
        self._tool_map: Dict[str, str] = {}

    async def _list_tools_async(self) -> List[Dict[str, Any]]:
        schema: List[Dict[str, Any]] = []
        async with self._client:
            tools = await self._client.list_tools()
        for tool in tools:
            internal_name = tool.name
            public_name = internal_name.split("_", 1)[1] if "_" in internal_name else internal_name
            self._tool_map[public_name] = internal_name
            schema.append(
                {
                    "type": "function",
                    "function": {
                        "name": public_name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema
                        or {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    },
                }
            )
        return schema

    def list_tools(self) -> List[Dict[str, Any]]:
        return asyncio.run(self._list_tools_async())

    async def _call_tool_async(self, name: str, arguments: Dict[str, Any]) -> Any:
        async with self._client:
            result = await self._client.call_tool(name, arguments)
        if result.data is not None:
            return result.data
        if result.structured_content is not None:
            return result.structured_content
        texts: List[str] = []
        for block in result.content:
            if isinstance(block, mcp.types.TextContent):
                texts.append(block.text)
        return {"result": "\n".join(texts)}

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        internal_name = self._tool_map.get(name)
        if internal_name is None:
            return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
        try:
            data = asyncio.run(self._call_tool_async(internal_name, arguments))
        except Exception as e:
            return json.dumps(
                {"error": f"Tool execution error for {name}: {e}"}, ensure_ascii=False
            )
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return json.dumps({"result": str(data)}, ensure_ascii=False)


__all__ = ["FastMCPClient"]
