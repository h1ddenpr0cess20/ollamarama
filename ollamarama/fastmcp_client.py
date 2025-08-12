from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Mapping, Sequence

from fastmcp import Client
import mcp.types


class FastMCPClient:
    def __init__(self, servers: Mapping[str, str | Dict[str, Any]]) -> None:
        self._clients: List[Client] = []
        for name, spec in servers.items():
            if isinstance(spec, dict):
                config = {"mcpServers": {name: spec}}
                client = Client(config)
            else:
                client = Client(spec)
            self._clients.append(client)
        self._tool_clients: Dict[str, Client] = {}

    async def _list_tools_async(self) -> List[Dict[str, Any]]:
        schema: List[Dict[str, Any]] = []
        for client in self._clients:
            async with client:
                tools = await client.list_tools()
            for tool in tools:
                self._tool_clients[tool.name] = client
                schema.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
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

    async def _call_tool_async(self, client: Client, name: str, arguments: Dict[str, Any]) -> Any:
        async with client:
            result = await client.call_tool(name, arguments)
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
        client = self._tool_clients.get(name)
        if client is None:
            return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
        try:
            data = asyncio.run(self._call_tool_async(client, name, arguments))
        except Exception as e:
            return json.dumps({"error": f"Tool execution error for {name}: {e}"}, ensure_ascii=False)
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return json.dumps({"result": str(data)}, ensure_ascii=False)


__all__ = ["FastMCPClient"]
