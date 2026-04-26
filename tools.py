"""
Optional LLM tool functions for the voice agent.
These can be integrated into the voice assistant for enhanced capabilities.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class CalendarTools:
    """Calendar integration tools for appointment management."""

    def __init__(self):
        """Initialize calendar tools."""
        # In production, this would connect to actual calendar APIs
        # (Google Calendar, Microsoft Outlook, etc.)
        self.appointments = {}

    async def check_availability(
        self,
        date: str,
        preferred_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check appointment availability for a given date.

        Args:
            date: Date string in format 'YYYY-MM-DD'
            preferred_time: Optional preferred time slot

        Returns:
            Dictionary with availability status and available slots
        """
        try:
            # Simulate availability check
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

    async def book_appointment(
        self,
        patient_name: str,
        date: str,
        time: str,
        appointment_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Book an appointment slot.

        Args:
            patient_name: Name of the patient
            date: Date string in format 'YYYY-MM-DD'
            time: Time slot (e.g., '10:00 AM')
            appointment_type: Type of appointment

        Returns:
            Dictionary with booking status
        """
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

    async def cancel_appointment(
        self,
        patient_name: str,
        date: str,
        time: str
    ) -> Dict[str, Any]:
        """
        Cancel an existing appointment.

        Args:
            patient_name: Name of the patient
            date: Date string in format 'YYYY-MM-DD'
            time: Time slot (e.g., '10:00 AM')

        Returns:
            Dictionary with cancellation status
        """
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
        # In production, this would query actual calendar availability
        base_times = [
            "9:00 AM", "9:30 AM", "10:00 AM", "10:30 AM", "11:00 AM",
            "11:30 AM", "1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM",
            "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM"
        ]

        # Randomly mark some slots as unavailable
        import random
        available = [slot for slot in base_times if random.random() > 0.3]
        return available


class CRMTools:
    """CRM integration tools for lead qualification and management."""

    def __init__(self):
        """Initialize CRM tools."""
        # In production, this would connect to actual CRM APIs
        # (Salesforce, HubSpot, Pipedrive, etc.)
        self.leads = {}
        self.lead_scores = {}

    async def create_lead(
        self,
        name: str,
        company: str,
        phone: str,
        email: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new lead in the CRM.

        Args:
            name: Contact name
            company: Company name
            phone: Phone number
            email: Optional email address
            notes: Optional notes about the lead

        Returns:
            Dictionary with created lead details
        """
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

    async def score_lead(
        self,
        lead_id: str,
        company_size: Optional[int] = None,
        has_budget: Optional[bool] = None,
        timeline: Optional[str] = None,
        urgency: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Score a lead based on qualification criteria.

        Args:
            lead_id: Lead identifier
            company_size: Number of employees
            has_budget: Whether budget is available
            timeline: Implementation timeline
            urgency: Urgency level (low, medium, high)

        Returns:
            Dictionary with lead score and qualification level
        """
        try:
            if lead_id not in self.leads:
                return {"success": False, "error": "Lead not found"}

            score = 0
            factors = []

            # Company size scoring (0-30 points)
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

            # Budget scoring (0-30 points)
            if has_budget:
                score += 30
                factors.append("Budget available (30 points)")

            # Timeline scoring (0-20 points)
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

            # Urgency scoring (0-20 points)
            if urgency:
                if urgency.lower() == "high":
                    score += 20
                    factors.append("High urgency (20 points)")
                elif urgency.lower() == "medium":
                    score += 10
                    factors.append("Medium urgency (10 points)")

            # Determine qualification level
            if score >= 70:
                qualification = "high"
            elif score >= 40:
                qualification = "medium"
            else:
                qualification = "low"

            # Update lead
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

    async def update_lead_status(
        self,
        lead_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update lead status and add notes.

        Args:
            lead_id: Lead identifier
            status: New status (new, contacted, qualified, proposal, closed_won, closed_lost)
            notes: Optional additional notes

        Returns:
            Dictionary with updated lead details
        """
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

    async def get_lead_summary(self, lead_id: str) -> Dict[str, Any]:
        """
        Get a summary of lead information.

        Args:
            lead_id: Lead identifier

        Returns:
            Dictionary with lead summary
        """
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


class ToolRegistry:
    """Registry for managing and accessing all agent tools."""

    def __init__(self):
        """Initialize tool registry."""
        self.calendar = CalendarTools()
        self.crm = CRMTools()

    def get_all_tools(self) -> Dict[str, Any]:
        """
        Get all available tools for LLM function calling.

        Returns:
            Dictionary mapping tool names to their functions
        """
        return {
            "check_availability": self.calendar.check_availability,
            "book_appointment": self.calendar.book_appointment,
            "cancel_appointment": self.calendar.cancel_appointment,
            "create_lead": self.crm.create_lead,
            "score_lead": self.crm.score_lead,
            "update_lead_status": self.crm.update_lead_status,
            "get_lead_summary": self.crm.get_lead_summary,
        }

    def get_tool_schemas(self) -> list[Dict[str, Any]]:
        """
        Get JSON schemas for all tools (for LLM function calling).

        Returns:
            List of tool schemas
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_availability",
                    "description": "Check appointment availability for a given date",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format"
                            },
                            "preferred_time": {
                                "type": "string",
                                "description": "Preferred time slot (optional)"
                            }
                        },
                        "required": ["date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "book_appointment",
                    "description": "Book an appointment slot",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "patient_name": {"type": "string"},
                            "date": {"type": "string"},
                            "time": {"type": "string"},
                            "appointment_type": {"type": "string"}
                        },
                        "required": ["patient_name", "date", "time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_lead",
                    "description": "Create a new lead in the CRM",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "company": {"type": "string"},
                            "phone": {"type": "string"},
                            "email": {"type": "string"},
                            "notes": {"type": "string"}
                        },
                        "required": ["name", "company", "phone"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "score_lead",
                    "description": "Score a lead based on qualification criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lead_id": {"type": "string"},
                            "company_size": {"type": "integer"},
                            "has_budget": {"type": "boolean"},
                            "timeline": {"type": "string"},
                            "urgency": {"type": "string"}
                        },
                        "required": ["lead_id"]
                    }
                }
            }
        ]
