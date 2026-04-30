"""
Test script to verify MCP server functionality.
This script connects to the MCP server and tests all available tools.
"""

import asyncio
import json
import sys
import io
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


async def test_mcp_server():
    """Test the MCP server by calling each tool."""

    print("Starting MCP server test...")

    # Connect to the MCP server via stdio
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "mcp_server.py"]
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the session
            await session.initialize()

            print("\n✅ MCP Server connected successfully!\n")

            # List available tools
            tools_result = await session.list_tools()
            tools = tools_result.tools

            print(f"📦 Available Tools ({len(tools)}):")
            print("-" * 60)
            for tool in tools:
                print(f"  • {tool.name}: {tool.description[:80]}...")
            print()

            # Test each tool with sample data
            test_cases = [
                {
                    "tool": "check_availability",
                    "arguments": {"date": "2025-05-15"}
                },
                {
                    "tool": "book_appointment",
                    "arguments": {
                        "patient_name": "John Doe",
                        "date": "2025-05-15",
                        "time": "10:00 AM",
                        "appointment_type": "general"
                    }
                },
                {
                    "tool": "create_lead",
                    "arguments": {
                        "name": "Jane Smith",
                        "company": "Acme Corp",
                        "phone": "+1234567890",
                        "email": "jane@acme.com"
                    }
                },
                {
                    "tool": "score_lead",
                    "arguments": {
                        "lead_id": "lead_1",
                        "company_size": 250,
                        "has_budget": True,
                        "timeline": "1 month",
                        "urgency": "high"
                    }
                },
                {
                    "tool": "update_lead_status",
                    "arguments": {
                        "lead_id": "lead_1",
                        "status": "qualified",
                        "notes": "High priority lead with budget and immediate timeline"
                    }
                },
                {
                    "tool": "get_lead_summary",
                    "arguments": {"lead_id": "lead_1"}
                }
            ]

            print("🧪 Testing Tools:")
            print("=" * 60)

            for test in test_cases:
                print(f"\n🔧 Testing: {test['tool']}")
                print(f"   Arguments: {json.dumps(test['arguments'], indent=2)}")

                try:
                    result = await session.call_tool(test['tool'], test['arguments'])

                    # Extract content from result
                    for content in result.content:
                        if hasattr(content, 'text'):
                            print(f"   ✅ Result: {content.text[:200]}...")
                        else:
                            print(f"   ✅ Result: {str(content)[:200]}...")

                except Exception as e:
                    print(f"   ❌ Error: {e}")

            print("\n" + "=" * 60)
            print("✅ MCP Server Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
