# MCP Tool Integration

This project now includes **Model Context Protocol (MCP)** integration, allowing the voice agent to use external tools for calendar management, CRM operations, and more.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  LiveKit Room   │────▶│  Voice Agent    │────▶│   MCP Server    │
│  (Phone Call)   │     │   (agent.py)    │     │  (mcp_server.py)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                        │
                                ▼                        ▼
                         Groq LLM               Calendar & CRM Tools
                         (with tool calling)     (via MCP protocol)
```

## Available Tools

### Calendar Tools
| Tool | Description |
|------|-------------|
| `check_availability` | Check appointment availability for a given date |
| `book_appointment` | Book a new appointment slot |
| `cancel_appointment` | Cancel an existing appointment |

### CRM Tools
| Tool | Description |
|------|-------------|
| `create_lead` | Create a new lead in the CRM |
| `score_lead` | Score a lead based on qualification criteria |
| `update_lead_status` | Update lead status and add notes |
| `get_lead_summary` | Get lead information summary |

## Setup

### 1. Install Dependencies

```bash
uv sync
```

This installs the MCP library along with other dependencies.

### 2. Test the MCP Server

Before running the full agent, test the MCP server independently:

```bash
uv run python test_mcp_server.py
```

You should see output like:
```
📦 Available Tools (7):
  • check_availability: Check appointment availability...
  • book_appointment: Book a new appointment slot...
  ...

🧪 Testing Tools:
✅ All tests passed!
```

### 3. Run the Agent Worker

```bash
uv run python agent.py
```

The agent will:
1. Start and prewarm the VAD model
2. Connect to the MCP server via stdio
3. Load all available tools
4. Wait for room assignments

### 4. Make a Test Call

In a separate terminal:

```bash
uv run python outbound.py +1234567890 --agent-type appointment
```

## How It Works

### MCP Server (`mcp_server.py`)
- Runs as a separate process using stdio transport
- Exposes tools via the MCP protocol
- Handles tool execution and returns results

### Agent Integration (`agent.py`)
```python
# Connect to MCP server
mcp_server = MCPServerStdio(
    command="uv",
    args=["run", "python", "mcp_server.py"],
    cwd=os.path.dirname(os.path.abspath(__file__))
)

# Load tools
await mcp_server.initialize()
tools = await mcp_server.list_tools()

# Pass to voice agent
session.start(
    agent=voice.Agent(
        instructions=PROMPT,
        tools=tools,  # MCP tools available here
    )
)
```

## Adding Custom Tools

To add a new tool:

1. **Define the tool in `mcp_server.py`:**

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "your_new_tool":
        result = your_function(arguments)
        return [TextContent(type="text", text=str(result))]
```

2. **Add to the tool list in `list_tools()`:**

```python
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="your_new_tool",
            description="What your tool does",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "..."}
                },
                "required": ["param1"]
            }
        ),
        # ... other tools
    ]
```

3. **Update the prompt to instruct when to use it:**

Add instructions in `prompts.py` so the LLM knows when to call your tool.

## Example Conversation Flow

**Agent**: "Hi, this is Sarah calling from Medical Clinic. I'm calling to remind you about your appointment tomorrow at 10 AM. Am I speaking with John?"

**User**: "Yes, that's me. But I can't make it tomorrow."

**Agent**: "I understand. Let me check what other times are available this week."
*(Agent calls `check_availability` tool)*

**Agent**: "I have openings on Wednesday at 2 PM, Thursday at 10 AM, or Friday at 3 PM. Would any of those work?"

**User**: "Thursday at 10 AM works."

**Agent**: "Perfect, let me book that for you."
*(Agent calls `book_appointment` tool)*

**Agent**: "Great! Your appointment is confirmed for Thursday at 10 AM. Is there anything else I can help with?"

## Troubleshooting

### MCP Server Not Starting
- Ensure `uv` is installed and in PATH
- Check that `mcp_server.py` is in the same directory as `agent.py`

### Tools Not Available
- Check logs for "Loaded X tools from MCP server"
- Run `test_mcp_server.py` to verify server works independently

### Tool Calls Failing
- Check argument names match the tool schema
- Ensure required parameters are provided
- Check MCP server logs for errors

## Files Modified/Added

- **`mcp_server.py`** - Custom MCP server with Calendar and CRM tools
- **`agent.py`** - Updated with MCP integration
- **`prompts.py`** - Updated prompts with tool usage instructions
- **`test_mcp_server.py`** - Test script for MCP server
- **`pyproject.toml`** - Added MCP dependency
