"""
Custom MCP server for voice agent tools.
Exposes Calendar and CRM tools via Model Context Protocol.
"""

import asyncio
import logging
from typing import Any, Optional
from datetime import datetime
from mcp.server.models import InitializationOptions, ServerCapabilities
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


class CalendarTools:
    """Calendar integration tools for appointment management."""

    def __init__(self):
        self.appointments = {}

    def check_availability(
        self,
        date: str,
        preferred_time: Optional[str] = None
    ) -> dict[str, Any]:
        """Check appointment availability for a given date."""
        try:
            available_slots = self._generate_time_slots(date)

            if preferred_time:
                is_available = preferred_time in available_slots
                return {
                    "date": date,
                    "preferred_time_available": is_available,
                    "alternative_slots": available_slots[:3] if not is_available else []
                }

            return {
                "date": date,
                "available_slots": available_slots[:5]
            }

        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {"error": str(e)}

    def book_appointment(
        self,
        patient_name: str,
        date: str,
        time: str,
        appointment_type: str = "general"
    ) -> dict[str, Any]:
        """Book an appointment slot."""
        try:
            appointment_key = f"{date}_{time}"

            if appointment_key in self.appointments:
                return {
                    "success": False,
                    "message": "This time slot is already booked"
                }

            self.appointments[appointment_key] = {
                "patient_name": patient_name,
                "date": date,
                "time": time,
                "type": appointment_type,
                "created_at": datetime.now().isoformat()
            }

            logger.info(f"Appointment booked for {patient_name} on {date} at {time}")

            return {
                "success": True,
                "message": f"Appointment confirmed for {date} at {time}",
                "appointment_details": self.appointments[appointment_key]
            }

        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return {"success": False, "error": str(e)}

    def cancel_appointment(
        self,
        patient_name: str,
        date: str,
        time: str
    ) -> dict[str, Any]:
        """Cancel an existing appointment."""
        try:
            appointment_key = f"{date}_{time}"

            if appointment_key not in self.appointments:
                return {
                    "success": False,
                    "message": "No appointment found for this date and time"
                }

            if self.appointments[appointment_key]["patient_name"] != patient_name:
                return {
                    "success": False,
                    "message": "Appointment name does not match"
                }

            del self.appointments[appointment_key]

            logger.info(f"Appointment cancelled for {patient_name} on {date} at {time}")

            return {
                "success": True,
                "message": f"Appointment cancelled for {date} at {time}"
            }

        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            return {"success": False, "error": str(e)}

    def _generate_time_slots(self, date: str) -> list[str]:
        """Generate available time slots for a given date."""
        base_times = [
            "9:00 AM", "9:30 AM", "10:00 AM", "10:30 AM", "11:00 AM",
            "11:30 AM", "1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM",
            "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM"
        ]
        import random
        available = [slot for slot in base_times if random.random() > 0.3]
        return available


class CRMTools:
    """CRM integration tools for lead qualification and management."""

    def __init__(self):
        self.leads = {}
        self.lead_scores = {}

    def create_lead(
        self,
        name: str,
        company: str,
        phone: str,
        email: Optional[str] = None,
        notes: Optional[str] = None
    ) -> dict[str, Any]:
        """Create a new lead in the CRM."""
        try:
            lead_id = f"lead_{len(self.leads) + 1}"

            lead = {
                "id": lead_id,
                "name": name,
                "company": company,
                "phone": phone,
                "email": email,
                "notes": notes,
                "status": "new",
                "created_at": datetime.now().isoformat(),
                "score": 0
            }

            self.leads[lead_id] = lead

            logger.info(f"Lead created: {lead_id} - {name} from {company}")

            return {
                "success": True,
                "lead": lead
            }

        except Exception as e:
            logger.error(f"Error creating lead: {e}")
            return {"success": False, "error": str(e)}

    def score_lead(
        self,
        lead_id: str,
        company_size: Optional[int] = None,
        has_budget: Optional[bool] = None,
        timeline: Optional[str] = None,
        urgency: Optional[str] = None
    ) -> dict[str, Any]:
        """Score a lead based on qualification criteria."""
        try:
            if lead_id not in self.leads:
                return {"success": False, "error": "Lead not found"}

            score = 0
            factors = []

            if company_size:
                if company_size > 500:
                    score += 30
                    factors.append("Large enterprise (30 points)")
                elif company_size > 100:
                    score += 20
                    factors.append("Mid-sized company (20 points)")
                elif company_size > 10:
                    score += 10
                    factors.append("Small business (10 points)")

            if has_budget:
                score += 30
                factors.append("Budget available (30 points)")

            if timeline:
                if "immediate" in timeline.lower() or "asap" in timeline.lower():
                    score += 20
                    factors.append("Immediate timeline (20 points)")
                elif "month" in timeline.lower():
                    score += 15
                    factors.append("Short-term timeline (15 points)")
                elif "quarter" in timeline.lower():
                    score += 10
                    factors.append("Medium-term timeline (10 points)")

            if urgency:
                if urgency.lower() == "high":
                    score += 20
                    factors.append("High urgency (20 points)")
                elif urgency.lower() == "medium":
                    score += 10
                    factors.append("Medium urgency (10 points)")

            if score >= 70:
                qualification = "high"
            elif score >= 40:
                qualification = "medium"
            else:
                qualification = "low"

            self.leads[lead_id]["score"] = score
            self.leads[lead_id]["qualification"] = qualification
            self.lead_scores[lead_id] = score

            logger.info(f"Lead {lead_id} scored: {score} ({qualification})")

            return {
                "success": True,
                "lead_id": lead_id,
                "score": score,
                "qualification": qualification,
                "factors": factors
            }

        except Exception as e:
            logger.error(f"Error scoring lead: {e}")
            return {"success": False, "error": str(e)}

    def update_lead_status(
        self,
        lead_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> dict[str, Any]:
        """Update lead status and add notes."""
        try:
            if lead_id not in self.leads:
                return {"success": False, "error": "Lead not found"}

            self.leads[lead_id]["status"] = status
            self.leads[lead_id]["updated_at"] = datetime.now().isoformat()

            if notes:
                existing_notes = self.leads[lead_id].get("notes", "")
                self.leads[lead_id]["notes"] = f"{existing_notes}\n{notes}".strip()

            logger.info(f"Lead {lead_id} status updated to: {status}")

            return {
                "success": True,
                "lead": self.leads[lead_id]
            }

        except Exception as e:
            logger.error(f"Error updating lead status: {e}")
            return {"success": False, "error": str(e)}

    def get_lead_summary(self, lead_id: str) -> dict[str, Any]:
        """Get a summary of lead information."""
        try:
            if lead_id not in self.leads:
                return {"success": False, "error": "Lead not found"}

            lead = self.leads[lead_id]

            return {
                "success": True,
                "summary": {
                    "name": lead["name"],
                    "company": lead["company"],
                    "status": lead["status"],
                    "score": lead.get("score", 0),
                    "qualification": lead.get("qualification", "not scored")
                }
            }

        except Exception as e:
            logger.error(f"Error getting lead summary: {e}")
            return {"success": False, "error": str(e)}


# Create MCP server instance
server = Server("voice-agent-tools")

# Initialize tools
calendar_tools = CalendarTools()
crm_tools = CRMTools()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="check_availability",
            description="Check appointment availability for a given date. Returns available time slots and whether a preferred time is available.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                        "format": "date"
                    },
                    "preferred_time": {
                        "type": "string",
                        "description": "Preferred time slot (e.g., '10:00 AM', '2:30 PM')"
                    }
                },
                "required": ["date"]
            }
        ),
        Tool(
            name="book_appointment",
            description="Book an appointment slot for a patient. Confirms the booking and returns appointment details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "patient_name": {
                        "type": "string",
                        "description": "Full name of the patient"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                        "format": "date"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time slot (e.g., '10:00 AM', '2:30 PM')"
                    },
                    "appointment_type": {
                        "type": "string",
                        "description": "Type of appointment (default: 'general')",
                        "enum": ["general", "follow-up", "consultation", "emergency"]
                    }
                },
                "required": ["patient_name", "date", "time"]
            }
        ),
        Tool(
            name="cancel_appointment",
            description="Cancel an existing appointment. Requires patient name, date, and time to match.",
            inputSchema={
                "type": "object",
                "properties": {
                    "patient_name": {
                        "type": "string",
                        "description": "Full name of the patient"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                        "format": "date"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time slot (e.g., '10:00 AM', '2:30 PM')"
                    }
                },
                "required": ["patient_name", "date", "time"]
            }
        ),
        Tool(
            name="create_lead",
            description="Create a new lead in the CRM system. Returns the created lead with ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name of the contact"
                    },
                    "company": {
                        "type": "string",
                        "description": "Company name"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Phone number"
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address (optional)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes about the lead (optional)"
                    }
                },
                "required": ["name", "company", "phone"]
            }
        ),
        Tool(
            name="score_lead",
            description="Score a lead based on qualification criteria. Returns score, qualification level, and scoring factors.",
            inputSchema={
                "type": "object",
                "properties": {
                    "lead_id": {
                        "type": "string",
                        "description": "Lead ID (e.g., 'lead_1', 'lead_2')"
                    },
                    "company_size": {
                        "type": "integer",
                        "description": "Number of employees in the company"
                    },
                    "has_budget": {
                        "type": "boolean",
                        "description": "Whether the lead has available budget"
                    },
                    "timeline": {
                        "type": "string",
                        "description": "Implementation timeline (e.g., 'immediate', '1 month', 'next quarter')"
                    },
                    "urgency": {
                        "type": "string",
                        "description": "Urgency level",
                        "enum": ["low", "medium", "high"]
                    }
                },
                "required": ["lead_id"]
            }
        ),
        Tool(
            name="update_lead_status",
            description="Update a lead's status in the CRM. Can add additional notes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "lead_id": {
                        "type": "string",
                        "description": "Lead ID (e.g., 'lead_1', 'lead_2')"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status for the lead",
                        "enum": ["new", "contacted", "qualified", "proposal", "closed_won", "closed_lost"]
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes to add (optional)"
                    }
                },
                "required": ["lead_id", "status"]
            }
        ),
        Tool(
            name="get_lead_summary",
            description="Get a summary of lead information including name, company, status, score, and qualification.",
            inputSchema={
                "type": "object",
                "properties": {
                    "lead_id": {
                        "type": "string",
                        "description": "Lead ID (e.g., 'lead_1', 'lead_2')"
                    }
                },
                "required": ["lead_id"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""

    try:
        if name == "check_availability":
            result = calendar_tools.check_availability(
                date=arguments.get("date"),
                preferred_time=arguments.get("preferred_time")
            )

        elif name == "book_appointment":
            result = calendar_tools.book_appointment(
                patient_name=arguments["patient_name"],
                date=arguments["date"],
                time=arguments["time"],
                appointment_type=arguments.get("appointment_type", "general")
            )

        elif name == "cancel_appointment":
            result = calendar_tools.cancel_appointment(
                patient_name=arguments["patient_name"],
                date=arguments["date"],
                time=arguments["time"]
            )

        elif name == "create_lead":
            result = crm_tools.create_lead(
                name=arguments["name"],
                company=arguments["company"],
                phone=arguments["phone"],
                email=arguments.get("email"),
                notes=arguments.get("notes")
            )

        elif name == "score_lead":
            result = crm_tools.score_lead(
                lead_id=arguments["lead_id"],
                company_size=arguments.get("company_size"),
                has_budget=arguments.get("has_budget"),
                timeline=arguments.get("timeline"),
                urgency=arguments.get("urgency")
            )

        elif name == "update_lead_status":
            result = crm_tools.update_lead_status(
                lead_id=arguments["lead_id"],
                status=arguments["status"],
                notes=arguments.get("notes")
            )

        elif name == "get_lead_summary":
            result = crm_tools.get_lead_summary(
                lead_id=arguments["lead_id"]
            )

        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(
            type="text",
            text=str(result)
        )]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Main entry point for the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="voice-agent-tools",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    tools={}
                ),
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
