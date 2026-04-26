"""
Outbound call script using LiveKit SIP API.
Triggers outbound calls via Twilio SIP trunk.
"""

import os
import sys
import asyncio
import logging
import argparse
from typing import Optional
from datetime import datetime

from livekit import api
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class OutboundCallManager:
    """Manager for making outbound SIP calls through LiveKit using Twilio."""

    def __init__(self):
        """Initialize the outbound call manager."""
        self.livekit_url = os.getenv('LIVEKIT_URL', '')
        self.livekit_api_key = os.getenv('LIVEKIT_API_KEY', '')
        self.livekit_api_secret = os.getenv('LIVEKIT_API_SECRET', '')
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_from_number = os.getenv('TWILIO_FROM_NUMBER', '')
        self.livekit_sip_trunk_id = os.getenv('LIVEKIT_SIP_TRUNK_ID', '')
        self.twilio_trunk_domain = os.getenv(
            'TWILIO_TRUNK_DOMAIN',
            'TK2eda324c95caecb5e2637f605b1bb15c.sip.twilio.com'
        )

        # Validate environment variables
        self._validate_config()

        # Initialize LiveKit client
        self.client = api.LiveKitAPI(
            self.livekit_url,
            self.livekit_api_key,
            self.livekit_api_secret
        )

    def _validate_config(self):
        """Validate required configuration."""
        required_vars = [
            ('LIVEKIT_URL', self.livekit_url),
            ('LIVEKIT_API_KEY', self.livekit_api_key),
            ('LIVEKIT_API_SECRET', self.livekit_api_secret),
            ('TWILIO_ACCOUNT_SID', self.twilio_account_sid),
            ('TWILIO_AUTH_TOKEN', self.twilio_auth_token),
            ('TWILIO_FROM_NUMBER', self.twilio_from_number),
            ('LIVEKIT_SIP_TRUNK_ID', self.livekit_sip_trunk_id),
        ]

        missing = [var_name for var_name, var_value in required_vars if not var_value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        logger.info("Configuration validated successfully")

    def _format_phone_number(self, phone: str) -> str:
        """
        Format phone number to E.164 format.

        Args:
            phone: Phone number in various formats

        Returns:
            E.164 formatted phone number (e.g. +923284869835)
        """
        # Remove all non-numeric characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Ensure it starts with +
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned

        return cleaned

    def _create_sip_uri(self, phone_number: str) -> str:
        """
        Create full SIP URI using the Twilio trunk domain.

        Args:
            phone_number: E.164 formatted phone number

        Returns:
            Full SIP URI string (e.g. sip:+923284869835@TKxxx.sip.twilio.com)
        """
        return f"sip:{phone_number}@{self.twilio_trunk_domain}"

    async def make_outbound_call(
        self,
        phone_number: str,
        agent_type: str = "appointment",
        room_name: Optional[str] = None,
        custom_metadata: Optional[dict] = None
    ) -> dict:
        """
        Make an outbound SIP call.

        Args:
            phone_number: Phone number to call (e.g., +923284869835)
            agent_type: Type of agent ('appointment' or 'lead')
            room_name: Optional custom room name
            custom_metadata: Optional custom metadata for the SIP participant

        Returns:
            Dictionary with call details
        """
        try:
            # Format phone number to E.164
            formatted_number = self._format_phone_number(phone_number)
            logger.info(f"Making outbound call to {formatted_number}")

            # Generate room name if not provided
            if not room_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                room_name = f"outbound_call_{agent_type}_{timestamp}"

            # Build full SIP URI with Twilio trunk domain
            sip_uri = self._create_sip_uri(formatted_number)
            logger.info(f"SIP URI: {sip_uri}")
            logger.info(f"SIP From: {self.twilio_from_number}")

            # Prepare metadata
            sip_metadata = custom_metadata or {
                "agent_type": agent_type,
                "destination": formatted_number,
                "timestamp": datetime.now().isoformat(),
            }

            # Create room
            logger.info(f"Creating room: {room_name}")
            create_room_response = await self.client.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=300,  # 5 minutes
                    max_participants=10
                )
            )

            room_sid = create_room_response.sid if hasattr(create_room_response, 'sid') else "unknown"
            logger.info(f"Room created: {room_sid}")

            # Add SIP participant using the SIP trunk
            logger.info("Adding SIP participant for outbound call...")
            create_sip_participant_response = await self.client.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=room_name,
                    sip_call_to=formatted_number,               # E.164 phone number
                    sip_trunk_id=self.livekit_sip_trunk_id,
                    participant_identity=f"sip_call_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    participant_name=f"Outbound Call to {formatted_number}",
                    participant_metadata=(
                        f'{{"agent_type": "{agent_type}", "destination": "{formatted_number}"}}'
                    )
                )
            )

            participant_id = (
                create_sip_participant_response.participant_id
                if hasattr(create_sip_participant_response, 'participant_id')
                else "unknown"
            )
            logger.info(f"SIP participant added: {participant_id}")

            result = {
                "success": True,
                "room_name": room_name,
                "room_sid": room_sid,
                "participant_id": participant_id,
                "phone_number": formatted_number,
                "sip_uri": sip_uri,
                "agent_type": agent_type,
                "timestamp": datetime.now().isoformat()
            }

            logger.info("Outbound call initiated successfully")
            logger.info(f"Room: {room_name}")
            logger.info(f"Participant ID: {participant_id}")

            return result

        except Exception as e:
            logger.error(f"Error making outbound call: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "phone_number": phone_number
            }

    async def close(self):
        """Close the LiveKit client."""
        await self.client.aclose()
        logger.info("LiveKit client closed")


async def main():
    """Main entry point for outbound call script."""
    parser = argparse.ArgumentParser(
        description="Make outbound voice calls using LiveKit SIP"
    )
    parser.add_argument(
        "phone_number",
        help="Phone number to call (e.g., +923284869835)"
    )
    parser.add_argument(
        "--agent-type",
        choices=["appointment", "lead"],
        default="appointment",
        help="Type of agent to use (default: appointment)"
    )
    parser.add_argument(
        "--room-name",
        help="Custom room name (optional)"
    )
    parser.add_argument(
        "--metadata",
        help="Custom metadata as JSON string (optional)",
        default=None
    )

    args = parser.parse_args()

    # Parse custom metadata if provided
    custom_metadata = None
    if args.metadata:
        try:
            import json
            custom_metadata = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON metadata: {e}")
            sys.exit(1)

    # Create manager and make call
    manager = OutboundCallManager()

    try:
        result = await manager.make_outbound_call(
            phone_number=args.phone_number,
            agent_type=args.agent_type,
            room_name=args.room_name,
            custom_metadata=custom_metadata
        )

        if result["success"]:
            print("\n" + "=" * 50)
            print("OUTBOUND CALL INITIATED SUCCESSFULLY")
            print("=" * 50)
            print(f"Room Name:      {result['room_name']}")
            print(f"Room SID:       {result['room_sid']}")
            print(f"Participant ID: {result['participant_id']}")
            print(f"Phone:          {result['phone_number']}")
            print(f"SIP URI:        {result['sip_uri']}")
            print(f"Agent Type:     {result['agent_type']}")
            print(f"Timestamp:      {result['timestamp']}")
            print("=" * 50)
            print("\nMake sure your agent worker is running to handle this call!")
            print("Run: uv run python agent.py")
            print()
        else:
            print(f"\n[X] Failed to make outbound call: {result['error']}")
            sys.exit(1)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await manager.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Script stopped by user")
        sys.exit(0)