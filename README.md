# LiveKit Outbound Voice Agent

A production-ready AI voice agent for making outbound phone calls using LiveKit Agents, Deepgram STT, Groq LLM, and Cartesia TTS.

## Features

- **Outbound Calling**: Make automated phone calls via Twilio SIP trunk
- **Voice AI Pipeline**: Silero VAD, Deepgram Nova-3 STT, Groq LLM, Cartesia Sonic-3 TTS
- **Agent Personas**: Appointment reminder and lead qualification agents
- **Natural Conversations**: Handles interruptions, maintains context, responds naturally
- **MCP Tool Integration**: Calendar and CRM tools via Model Context Protocol
- **Production Ready**: Async/await, error handling, logging, no hardcoded secrets

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐      ┌─────────────┐
│   Twilio    │──────│  LiveKit     │──────│   Agent     │──────│   MCP       │
│  SIP Trunk  │ SIP  │  SIP Service │ Room │  Worker     │ MCP  │   Server    │
└─────────────┘      └──────────────┘      └─────┬───────┘      └──────┬──────┘
                                                   │                      │
                              ┌────────────────────┼────────────────────┐ │
                              │                    │                    │ │
                              ▼                    ▼                    ▼ ▼
                        ┌──────────┐         ┌──────────┐         ┌──────────┐
                        │  Silero  │         │Deepgram  │         │ Calendar │
                        │   VAD    │         │ Nova-3   │         │    &     │
                        └──────────┘         └─────┬────┘         │   CRM    │
                                                   │               └──────────┘
                                                   ▼
                                            ┌──────────┐
                                            │  Groq    │
                                            │   LLM    │
                                            │ (w/ Tool │
                                            │ Calling)│
                                            └──────────┘
```

## Prerequisites

- **Python 3.13+**: Required by the project
- **uv**: Fast Python package manager (`pip install uv`)
- **LiveKit Cloud Account**: [Sign up free](https://cloud.livekit.io)
- **Twilio Account**: [Sign up](https://twilio.com)
- **API Accounts**: Deepgram, Groq, Cartesia (free tiers available)

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd livekit-outbound-agent

# Install dependencies
uv sync
```

### 2. Configure Environment Variables

Copy the `.env` template and add your API keys:

```bash
# Copy .env template
cp .env .env.local

# Edit with your API keys
# Use your favorite editor or:
notepad .env.local  # Windows
nano .env.local     # Linux/Mac
```

Required environment variables:
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- `DEEPGRAM_API_KEY`
- `GROQ_API_KEY`
- `CARTESIA_API_KEY`
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `LIVEKIT_SIP_TRUNK_ID`

### 3. Test MCP Server

Verify the MCP server works before starting the agent:

```bash
uv run python test_mcp_server.py
```

You should see:
```
📦 Available Tools (7):
  • check_availability: Check appointment availability...
  • book_appointment: Book an appointment slot...
  • cancel_appointment: Cancel an existing appointment...
  • create_lead: Create a new lead in the CRM...
  • score_lead: Score a lead based on qualification...
  • update_lead_status: Update a lead's status...
  • get_lead_summary: Get a summary of lead information...

✅ MCP Server Test Complete!
```

### 4. Start Agent Worker

Run the agent worker (keeps running to handle calls):

```bash
uv run python agent.py
```

You should see:
```
INFO - Starting LiveKit agent worker with MCP tool support...
INFO - Prewarming agent process...
INFO - Silero VAD model loaded successfully
INFO - MCP server initialized successfully
INFO - Loaded 7 tools from MCP server
INFO - Agent worker started
```

### 5. Make Outbound Call

In a new terminal, trigger an outbound call:

```bash
# Appointment reminder call
uv run python outbound.py +1234567890 --agent-type appointment

# Lead qualification call
uv run python outbound.py +1234567890 --agent-type lead
```

Expected output:
```
==================================================
OUTBOUND CALL INITIATED SUCCESSFULLY
==================================================
Room Name: outbound_call_appointment_20240425_143022
Room SID: RM_xxxxxxxxx
Call SID: PA_xxxxxxxxx
Phone: +1234567890
Agent Type: appointment
==================================================

Make sure your agent worker is running to handle this call!
```

The agent will call the number and start the conversation automatically!

## MCP Tools

The voice agent has access to 7 tools via MCP:

### Calendar Tools
| Tool | Description |
|------|-------------|
| `check_availability` | Check available appointment slots for a date |
| `book_appointment` | Book a new appointment slot |
| `cancel_appointment` | Cancel an existing appointment |

### CRM Tools
| Tool | Description |
|------|-------------|
| `create_lead` | Create a new lead in the CRM |
| `score_lead` | Score a lead based on qualification criteria |
| `update_lead_status` | Update lead status and add notes |
| `get_lead_summary` | Get lead information summary |

### Example Conversation Flow

**Agent**: "Hi, this is Sarah calling from Medical Clinic. I'm calling to remind you about your appointment tomorrow at 10 AM. Am I speaking with John?"

**User**: "Yes, that's me. But I can't make it tomorrow."

**Agent**: "I understand. Let me check what other times are available."
*(Agent calls `check_availability` tool)*

**Agent**: "I have openings on Wednesday at 2 PM, Thursday at 10 AM, or Friday at 3 PM. Would any of those work?"

**User**: "Thursday at 10 AM works."

**Agent**: "Perfect, let me book that for you."
*(Agent calls `book_appointment` tool)*

**Agent**: "Great! Your appointment is confirmed for Thursday at 10 AM."

For more details, see [MCP_INTEGRATION.md](MCP_INTEGRATION.md).

## Configuration Guides

### Twilio SIP Trunk Setup

1. **Create SIP Trunk**:
   - Go to [Twilio Console](https://console.twilio.com)
   - Navigate to SIP Trunking
   - Click "Create SIP Trunk"

2. **Configure Trunk**:
   - Give it a friendly name (e.g., "LiveKit Outbound")
   - Note your Account SID and Auth Token from the Twilio Console

3. **Get Your Phone Number**:
   - Buy or port a number in Twilio
   - Note the number in E.164 format (+1XXXXXXXXXX or +92XXXXXXXXXX)

4. **Add to .env**:
   ```bash
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
   TWILIO_FROM_NUMBER=+1XXXXXXXXXX
   LIVEKIT_SIP_TRUNK_ID=your_livekit_trunk_id
   ```

### LiveKit SIP Setup

1. **Register SIP Trunk in LiveKit**:
   - Go to [LiveKit Console](https://cloud.livekit.io)
   - Navigate to SIP → Trunks
   - Click "Add SIP Trunk"

2. **Enter Twilio Details**:
   - **Trunk Name**: Twilio Outbound
   - **SIP Address**: `sip.twilio.com`
   - **Username/Password**: (from Twilio SIP credentials)

3. **Verify Registration**:
   - Status should show "Registered"
   - Note the LiveKit SIP Trunk ID and add to `.env` as `LIVEKIT_SIP_TRUNK_ID`

### API Keys Setup

**Deepgram** (STT):
- Go to [console.deepgram.com](https://console.deepgram.com)
- Create API key
- Region: Global
- Add `DEEPGRAM_API_KEY` to `.env`

**Groq** (LLM):
- Go to [console.groq.com](https://console.groq.com)
- Create API key
- Add `GROQ_API_KEY` to `.env`

**Cartesia** (TTS):
- Go to [cartesia.ai](https://cartesia.ai)
- Sign up and get API key
- Add `CARTESIA_API_KEY` to `.env`

## Development

### Project Structure

```
livekit-outbound-agent/
├── agent.py              # Main LiveKit agent with MCP integration
├── outbound.py           # SIP outbound call trigger script
├── prompts.py            # Agent system prompts and personas
├── mcp_server.py         # MCP server with Calendar & CRM tools
├── test_mcp_server.py    # Test script for MCP server
├── tools.py              # Legacy tool functions (deprecated, use MCP)
├── tests/                # Test suite
│   └── test_tools.py     # Unit tests for tools module
├── .env                  # API keys template
├── .env.local            # Your actual keys (gitignored)
├── pyproject.toml        # Dependencies and project config
├── MCP_INTEGRATION.md    # MCP documentation
├── pytest.ini            # Pytest configuration
└── README.md             # This file
```

### Customizing Agent Behavior

**Edit prompts in `prompts.py`**:
- `APPOINTMENT_REMINDER_PROMPT`: Modify the appointment reminder persona
- `LEAD_QUALIFICATION_PROMPT`: Modify the lead qualification persona

**Add custom tools in `mcp_server.py`**:
- Define new tool classes and methods
- Add tool schema to `list_tools()`
- Handle tool calls in `call_tool()`
- Update agent prompts to instruct when to use the tool

See [MCP_INTEGRATION.md](MCP_INTEGRATION.md) for detailed guide.

### Running Tests

```bash
# Test MCP server
uv run python test_mcp_server.py

# Run all unit tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test class
uv run pytest tests/test_tools.py::TestCalendarTools -v

# Run with coverage (requires pytest-cov)
uv run pytest --cov=tools --cov-report=html
```

### Logging

Logs are output to console with INFO level by default. Set `LOG_LEVEL` in `.env`:

```bash
LOG_LEVEL=DEBUG   # More verbose
LOG_LEVEL=WARNING # Less verbose
```

## Deployment

### Production Checklist

- [ ] Use strong API keys and rotate regularly
- [ ] Enable HTTPS/WSS for all connections
- [ ] Set up monitoring and alerting
- [ ] Configure call recording if needed
- [ ] Add rate limiting for outbound calls
- [ ] Implement proper error handling and retry logic
- [ ] Set up database for storing call logs
- [ ] Configure authentication for agent endpoints
- [ ] Add observability (metrics, traces)

### Running as a Service

**Using systemd (Linux)**:
```bash
# Create service file
sudo nano /etc/systemd/system/livekit-agent.service
```

```ini
[Unit]
Description=LiveKit Outbound Agent
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/livekit-outbound-agent
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable livekit-agent
sudo systemctl start livekit-agent
sudo systemctl status livekit-agent
```

**Using Docker** (if needed):
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv
RUN uv sync
CMD ["uv", "run", "python", "agent.py"]
```

## Troubleshooting

**Agent not connecting**:
- Verify LiveKit credentials in `.env`
- Check agent worker logs for errors
- Ensure LIVEKIT_URL uses `wss://` protocol

**SIP call failing**:
- Verify Twilio SIP trunk is registered in LiveKit Console
- Check LIVEKIT_SIP_TRUNK_ID matches your trunk ID in LiveKit Console
- Ensure phone number format: `+1234567890` (with + prefix)
- Verify TWILIO_FROM_NUMBER is your Twilio phone number

**MCP server not starting**:
- Ensure `uv` is installed and in PATH
- Check that `mcp_server.py` is in the same directory as `agent.py`
- Run `test_mcp_server.py` to verify server works independently

**Tools not available**:
- Check logs for "Loaded X tools from MCP server"
- Run `test_mcp_server.py` to verify server works
- Verify MCP server starts when agent worker starts

**No audio in calls**:
- Check all API keys are valid
- Verify agent worker is running
- Check browser console for WebRTC errors

**VAD not detecting speech**:
- Ensure Silero model downloaded successfully
- Check microphone permissions
- Adjust VAD sensitivity in `agent.py`

## Cost Estimates

**Free Tier Limits** (as of 2024):
- Deepgram: 200 hours/month free
- Groq: Various free tier options
- Cartesia: Free tier available
- LiveKit: 75GB/month free
- Twilio: Free trial credits available, then pay-as-you-go (varies by destination)

**Typical cost**: ~$0.02-0.05 per minute of calls

## License

MIT License - feel free to use in your projects!

## Support

- **LiveKit Docs**: [docs.livekit.io](https://docs.livekit.io)
- **LiveKit Discord**: [discord.gg/livekit](https://discord.gg/livekit)
- **Issues**: Open an issue in the repository

## Acknowledgments

Built with:
- [LiveKit Agents](https://livekit.io) - Real-time voice/video infrastructure
- [Deepgram](https://deepgram.com) - Speech-to-text
- [Groq](https://groq.com) - Fast LLM inference
- [Cartesia](https://cartesia.ai) - Text-to-speech
- [MCP](https://modelcontextprotocol.io) - Model Context Protocol for tools
