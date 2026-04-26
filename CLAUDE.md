# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Production-ready AI voice agent for outbound phone calls using LiveKit Agents, Deepgram Nova-3 STT, Groq LLM, and Cartesia Sonic-3 TTS via Twilio SIP trunking.

### Two-Process Architecture

1. **Agent Worker** (`agent.py`): Long-running worker that pre-loads Silero VAD and waits for room assignments
2. **Call Trigger** (`outbound.py`): Creates LiveKit room and adds SIP participant via Twilio trunk

**Flow**: `outbound.py` creates room → adds SIP participant → Twilio calls phone number → agent worker joins room → voice pipeline activates

## Development Setup

**Prerequisites**: Python 3.13+, uv package manager, API accounts (LiveKit, Twilio, Deepgram, Groq, Cartesia)

```bash
uv sync                           # Install dependencies
cp .env .env.local               # Add your API keys to .env.local
uv run python agent.py           # Start agent worker (runs continuously)
uv run python outbound.py +1234567890 --agent-type appointment  # Make call
```

## Project Structure

- **`agent.py`**: LiveKit agent worker with entrypoints for different agent types
- **`outbound.py`**: SIP call trigger script using LiveKit API
- **`prompts.py`**: System prompts (`APPOINTMENT_REMINDER_PROMPT`, `LEAD_QUALIFICATION_PROMPT`)
- **`tools.py`**: Optional LLM tools (Calendar, CRM) - not integrated by default

## Key Architecture Patterns

### Voice Pipeline Initialization
Uses LiveKit's `voice.AgentSession` with custom `GroqLLMAdapter`:
1. **STT** (Deepgram Nova-3): Transcribes speech
2. **LLM** (Groq): Generates responses via `AsyncOpenAI` client
3. **TTS** (Cartesia Sonic-3): Synthesizes speech
4. **VAD** (Silero): Pre-loaded for turn management

Critical: All components must be initialized before `session.start()`.

### GroqLLMAdapter Pattern
Each entrypoint defines a local `GroqLLMAdapter` class that:
- Takes an `AsyncOpenAI` client and model name
- Implements `async chat(chat_ctx, tools)` method
- Converts LiveKit chat messages to Groq API format
- Returns `llm.ChatMessage` with response

This adapter is passed to `voice.AgentSession(llm=groq_llm, ...)`.

### Environment Variables

**Required for agent.py**:
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- `DEEPGRAM_API_KEY`, `GROQ_API_KEY`, `CARTESIA_API_KEY`

**Required for outbound.py** (additional):
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `LIVEKIT_SIP_TRUNK_ID`

**Note**: `.env` is committed as template; `.env.local` is gitignored and contains actual keys.

### Adding New Agent Types

1. Create prompt in `prompts.py`
2. Copy existing entrypoint pattern in `agent.py` (create new async function with `JobContext` parameter)
3. Update `WorkerOptions(entrypoint_fnc=your_new_entrypoint)` in `main()`
4. Currently only one entrypoint can be registered at a time via `cli.run_app()`

## Debugging SIP Issues

1. Verify Twilio SIP trunk is registered in LiveKit Console
2. Check `LIVEKIT_SIP_TRUNK_ID` matches your trunk ID in LiveKit Console
3. Phone number format: `+1234567890` (with + prefix)
4. `TWILIO_FROM_NUMBER` must be your Twilio phone number

## Dependencies

Add with `uv add <package>`. Key deps in `pyproject.toml`:
- `livekit-agents[deepgram,cartesia,silero]` >= 0.12.0
- `livekit-api` >= 0.6.0
- `openai` >= 2.32.0 (used for Groq API compatibility)
