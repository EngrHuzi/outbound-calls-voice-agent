"""
LiveKit Agent Worker with MCP Tool Integration

This module implements a voice agent worker that connects to LiveKit rooms
and uses tools from a custom MCP server for enhanced capabilities.
"""

import os
import asyncio
import logging
from typing import Optional
from dataclasses import dataclass

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    vad,
    voice,
    llm,
)
from livekit.plugins import deepgram, cartesia, silero
from livekit.agents.llm.mcp import MCPServerStdio
from dotenv import load_dotenv
from openai import AsyncOpenAI

from prompts import APPOINTMENT_REMINDER_PROMPT, LEAD_QUALIFICATION_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


@dataclass
class AgentConfig:
    """Configuration for the voice agent."""
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    deepgram_api_key: str
    groq_api_key: str
    cartesia_api_key: str

    @classmethod
    def from_env(cls) -> 'AgentConfig':
        """Create configuration from environment variables."""
        return cls(
            livekit_url=os.getenv('LIVEKIT_URL', ''),
            livekit_api_key=os.getenv('LIVEKIT_API_KEY', ''),
            livekit_api_secret=os.getenv('LIVEKIT_API_SECRET', ''),
            deepgram_api_key=os.getenv('DEEPGRAM_API_KEY', ''),
            groq_api_key=os.getenv('GROQ_API_KEY', ''),
            cartesia_api_key=os.getenv('CARTESIA_API_KEY', ''),
        )


def prewarm(proc):
    """Prewarm the agent process to load models into memory."""
    logger.info("Prewarming agent process...")
    try:
        # Prewarm Silero VAD model
        silero.VAD.load()
        logger.info("Silero VAD model loaded successfully")
    except Exception as e:
        logger.warning(f"Prewarming failed: {e}")


async def setup_mcp_tools() -> list:
    """
    Connect to the custom MCP server and load available tools.

    Returns:
        List of MCP tools that can be used by the voice agent.
    """
    try:
        # Create MCP server connection using stdio transport
        mcp_server = MCPServerStdio(
            command="uv",
            args=["run", "python", "mcp_server.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            client_session_timeout_seconds=30
        )

        # Initialize the MCP server connection
        await mcp_server.initialize()
        logger.info("MCP server initialized successfully")

        # List available tools from the MCP server
        tools = await mcp_server.list_tools()
        logger.info(f"Loaded {len(tools)} tools from MCP server")

        for tool in tools:
            if hasattr(tool, '_raw_schema'):
                logger.info(f"  - {tool._raw_schema.get('name', 'unknown')}")

        return tools

    except Exception as e:
        logger.error(f"Failed to setup MCP tools: {e}", exc_info=True)
        return []


async def appointment_entrypoint(ctx: JobContext):
    """Entry point for appointment reminder agent with MCP tools."""
    try:
        logger.info(f"Starting appointment reminder agent in room: {ctx.room.name}")

        # Create configuration
        config = AgentConfig.from_env()

        # Validate API keys
        if not all([config.deepgram_api_key, config.groq_api_key, config.cartesia_api_key]):
            logger.error("Missing required API keys")
            return

        # Create STT with Deepgram Nova-3
        stt = deepgram.STT(
            api_key=config.deepgram_api_key,
            model="nova-3",
            language="en-US"
        )

        # Create TTS with Cartesia Sonic-3
        tts = cartesia.TTS(
            api_key=config.cartesia_api_key,
            model="sonic-3",
            voice="alicia"
        )

        # Setup MCP tools
        mcp_tools = await setup_mcp_tools()

        # Create voice agent session with MCP tools
        session = voice.AgentSession(
            stt=stt,
            llm=llm.openai.LLM(
                base_url="https://api.groq.com/openai/v1",
                api_key=config.groq_api_key,
                model="llama-3.3-70b-versatile"
            ),
            tts=tts,
        )

        # Start the session with tools
        await session.start(
            room=ctx.room,
            agent=voice.Agent(
                instructions=APPOINTMENT_REMINDER_PROMPT,
                tools=mcp_tools if mcp_tools else [],
            ),
        )

        logger.info("Voice agent started successfully with MCP tools")

    except Exception as e:
        logger.error(f"Error in appointment_entrypoint: {e}", exc_info=True)
        raise


async def lead_qualification_entrypoint(ctx: JobContext):
    """Entry point for lead qualification agent with MCP tools."""
    try:
        logger.info(f"Starting lead qualification agent in room: {ctx.room.name}")

        # Create configuration
        config = AgentConfig.from_env()

        # Validate API keys
        if not all([config.deepgram_api_key, config.groq_api_key, config.cartesia_api_key]):
            logger.error("Missing required API keys")
            return

        # Create STT with Deepgram Nova-3
        stt = deepgram.STT(
            api_key=config.deepgram_api_key,
            model="nova-3",
            language="en-US"
        )

        # Create TTS with Cartesia Sonic-3
        tts = cartesia.TTS(
            api_key=config.cartesia_api_key,
            model="sonic-3",
            voice="alicia"
        )

        # Setup MCP tools
        mcp_tools = await setup_mcp_tools()

        # Create voice agent session with MCP tools
        session = voice.AgentSession(
            stt=stt,
            llm=llm.openai.LLM(
                base_url="https://api.groq.com/openai/v1",
                api_key=config.groq_api_key,
                model="mixtral-8x7b-32768"
            ),
            tts=tts,
        )

        # Start the session with tools
        await session.start(
            room=ctx.room,
            agent=voice.Agent(
                instructions=LEAD_QUALIFICATION_PROMPT,
                tools=mcp_tools if mcp_tools else [],
            ),
        )

        logger.info("Voice agent started successfully with MCP tools")

    except Exception as e:
        logger.error(f"Error in lead_qualification_entrypoint: {e}", exc_info=True)
        raise


def main():
    """Main entry point for the agent worker."""
    try:
        # Validate environment variables
        required_vars = [
            'LIVEKIT_URL',
            'LIVEKIT_API_KEY',
            'LIVEKIT_API_SECRET',
            'DEEPGRAM_API_KEY',
            'GROQ_API_KEY',
            'CARTESIA_API_KEY'
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please set these in your .env file")
            return

        logger.info("Starting LiveKit agent worker with MCP tool support...")

        # Start the worker with appointment entrypoint (can be changed to lead_qualification_entrypoint)
        cli.run_app(
            WorkerOptions(
                entrypoint_fnc=appointment_entrypoint,
            )
        )

    except KeyboardInterrupt:
        logger.info("Agent worker stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
