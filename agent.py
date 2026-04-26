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
)
from livekit.plugins import deepgram, cartesia, silero
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


class SimpleVoiceAgent:
    """Simple voice agent that manually handles the conversation flow."""

    def __init__(self, config: AgentConfig, system_prompt: str, model: str = "llama-3.3-70b-versatile"):
        self.config = config
        self.system_prompt = system_prompt
        self.model = model
        self.groq_client = AsyncOpenAI(
            api_key=config.groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.conversation_history = [{"role": "system", "content": system_prompt}]

    async def get_response(self, user_message: str) -> str:
        """Get response from Groq LLM."""
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})

            # Get response from Groq
            response = await self.groq_client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=1024
            )

            assistant_message = response.choices[0].message.content

            # Add assistant response to conversation history
            self.conversation_history.append({"role": "assistant", "content": assistant_message})

            return assistant_message

        except Exception as e:
            logger.error(f"Error getting Groq response: {e}")
            return "I apologize, I'm having trouble processing that right now."


def prewarm(proc):
    """Prewarm the agent process to load models into memory."""
    logger.info("Prewarming agent process...")
    try:
        # Prewarm Silero VAD model
        silero.VAD.load()
        logger.info("Silero VAD model loaded successfully")
    except Exception as e:
        logger.warning(f"Prewarming failed: {e}")


async def appointment_entrypoint(ctx: JobContext):
    """Entry point for appointment reminder agent."""
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

        # Create Groq client
        groq_client = AsyncOpenAI(
            api_key=config.groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )

        # Import and use Voice Agent Session
        from livekit.agents import voice, llm

        # Create a custom LLM adapter for Groq
        class GroqLLMAdapter:
            def __init__(self, client, model):
                self.client = client
                self.model = model

            async def chat(self, chat_ctx, tools=None):
                """Process chat with Groq API."""
                messages = []
                for msg in chat_ctx.messages:
                    if hasattr(msg, 'role'):
                        messages.append({
                            "role": msg.role,
                            "content": msg.content if hasattr(msg, 'content') else str(msg)
                        })

                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1024
                    )
                    return llm.ChatMessage(
                        role="assistant",
                        content=response.choices[0].message.content
                    )
                except Exception as e:
                    logger.error(f"Error in Groq LLM: {e}")
                    return llm.ChatMessage(
                        role="assistant",
                        content="I apologize, I'm having trouble processing that right now."
                    )

        # Create Groq LLM adapter
        groq_llm = GroqLLMAdapter(groq_client, "llama-3.3-70b-versatile")

        # Create voice agent session
        session = voice.AgentSession(
            stt=stt,
            llm=groq_llm,
            tts=tts,
        )

        # Start the session
        await session.start(
            room=ctx.room,
            agent=voice.Agent(
                instructions=APPOINTMENT_REMINDER_PROMPT,
            ),
        )

        logger.info("Voice agent started successfully")

    except Exception as e:
        logger.error(f"Error in appointment_entrypoint: {e}", exc_info=True)
        raise


async def lead_qualification_entrypoint(ctx: JobContext):
    """Entry point for lead qualification agent."""
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

        # Create Groq client
        groq_client = AsyncOpenAI(
            api_key=config.groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )

        # Import and use Voice Agent Session
        from livekit.agents import voice, llm

        # Create a custom LLM adapter for Groq
        class GroqLLMAdapter:
            def __init__(self, client, model):
                self.client = client
                self.model = model

            async def chat(self, chat_ctx, tools=None):
                """Process chat with Groq API."""
                messages = []
                for msg in chat_ctx.messages:
                    if hasattr(msg, 'role'):
                        messages.append({
                            "role": msg.role,
                            "content": msg.content if hasattr(msg, 'content') else str(msg)
                        })

                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1024
                    )
                    return llm.ChatMessage(
                        role="assistant",
                        content=response.choices[0].message.content
                    )
                except Exception as e:
                    logger.error(f"Error in Groq LLM: {e}")
                    return llm.ChatMessage(
                        role="assistant",
                        content="I apologize, I'm having trouble processing that right now."
                    )

        # Create Groq LLM adapter
        groq_llm = GroqLLMAdapter(groq_client, "mixtral-8x7b-32768")

        # Create voice agent session
        session = voice.AgentSession(
            stt=stt,
            llm=groq_llm,
            tts=tts,
        )

        # Start the session
        await session.start(
            room=ctx.room,
            agent=voice.Agent(
                instructions=LEAD_QUALIFICATION_PROMPT,
            ),
        )

        logger.info("Voice agent started successfully")

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

        logger.info("Starting LiveKit agent worker...")

        # Start the worker with both entrypoints
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
