"""Tests for tools.py module."""

import pytest
from tools import CalendarTools, CRMTools, ToolRegistry


@pytest.mark.asyncio
class TestCalendarTools:
    """Test suite for CalendarTools class."""

    async def test_check_availability_returns_available_slots(self):
        calendar = CalendarTools()
        result = await calendar.check_availability("2024-01-15")

        assert "date" in result
        assert result["date"] == "2024-01-15"
        assert "available_slots" in result
        assert isinstance(result["available_slots"], list)

    async def test_check_availability_with_preferred_time(self):
        calendar = CalendarTools()
        result = await calendar.check_availability(
            "2024-01-15",
            preferred_time="10:00 AM"
        )

        assert "date" in result
        assert "preferred_time_available" in result
        assert isinstance(result["preferred_time_available"], bool)

    async def test_book_appointment_success(self):
        calendar = CalendarTools()
        result = await calendar.book_appointment(
            patient_name="John Doe",
            date="2024-01-15",
            time="10:00 AM"
        )

        assert result["success"] is True
        assert "confirmed" in result["message"].lower()
        assert result["appointment_details"]["patient_name"] == "John Doe"
        assert result["appointment_details"]["date"] == "2024-01-15"
        assert result["appointment_details"]["time"] == "10:00 AM"

    async def test_book_appointment_duplicate_slot(self):
        calendar = CalendarTools()

        # Book first appointment
        await calendar.book_appointment(
            patient_name="John Doe",
            date="2024-01-15",
            time="10:00 AM"
        )

        # Try to book same slot
        result = await calendar.book_appointment(
            patient_name="Jane Smith",
            date="2024-01-15",
            time="10:00 AM"
        )

        assert result["success"] is False
        assert "already booked" in result["message"].lower()

    async def test_cancel_appointment_success(self):
        calendar = CalendarTools()

        # Book an appointment first
        await calendar.book_appointment(
            patient_name="John Doe",
            date="2024-01-15",
            time="10:00 AM"
        )

        # Cancel it
        result = await calendar.cancel_appointment(
            patient_name="John Doe",
            date="2024-01-15",
            time="10:00 AM"
        )

        assert result["success"] is True
        assert "cancelled" in result["message"].lower()

    async def test_cancel_appointment_not_found(self):
        calendar = CalendarTools()
        result = await calendar.cancel_appointment(
            patient_name="John Doe",
            date="2024-01-15",
            time="10:00 AM"
        )

        assert result["success"] is False
        assert "appointment" in result["message"].lower() and "found" in result["message"].lower()

    async def test_cancel_appointment_name_mismatch(self):
        calendar = CalendarTools()

        # Book with one name
        await calendar.book_appointment(
            patient_name="John Doe",
            date="2024-01-15",
            time="10:00 AM"
        )

        # Try to cancel with different name
        result = await calendar.cancel_appointment(
            patient_name="Jane Smith",
            date="2024-01-15",
            time="10:00 AM"
        )

        assert result["success"] is False
        assert "does not match" in result["message"].lower()


@pytest.mark.asyncio
class TestCRMTools:
    """Test suite for CRMTools class."""

    async def test_create_lead_success(self):
        crm = CRMTools()
        result = await crm.create_lead(
            name="John Doe",
            company="Acme Corp",
            phone="+1234567890",
            email="john@example.com"
        )

        assert result["success"] is True
        assert result["lead"]["name"] == "John Doe"
        assert result["lead"]["company"] == "Acme Corp"
        assert result["lead"]["phone"] == "+1234567890"
        assert result["lead"]["email"] == "john@example.com"
        assert result["lead"]["status"] == "new"
        assert "id" in result["lead"]

    async def test_create_lead_without_email(self):
        crm = CRMTools()
        result = await crm.create_lead(
            name="John Doe",
            company="Acme Corp",
            phone="+1234567890"
        )

        assert result["success"] is True
        assert result["lead"]["email"] is None

    async def test_score_lead_not_found(self):
        crm = CRMTools()
        result = await crm.score_lead(lead_id="nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    async def test_score_lead_high_qualification(self):
        crm = CRMTools()

        # Create a lead first
        lead_result = await crm.create_lead(
            name="John Doe",
            company="Acme Corp",
            phone="+1234567890"
        )
        lead_id = lead_result["lead"]["id"]

        # Score with high values
        result = await crm.score_lead(
            lead_id=lead_id,
            company_size=1000,
            has_budget=True,
            timeline="immediate",
            urgency="high"
        )

        assert result["success"] is True
        assert result["score"] >= 70
        assert result["qualification"] == "high"
        assert len(result["factors"]) > 0

    async def test_score_lead_low_qualification(self):
        crm = CRMTools()

        # Create a lead first
        lead_result = await crm.create_lead(
            name="John Doe",
            company="Small Co",
            phone="+1234567890"
        )
        lead_id = lead_result["lead"]["id"]

        # Score with low values
        result = await crm.score_lead(
            lead_id=lead_id,
            company_size=5,
            has_budget=False,
            timeline="exploring",
            urgency="low"
        )

        assert result["success"] is True
        assert result["qualification"] == "low"

    async def test_score_lead_medium_qualification(self):
        crm = CRMTools()

        # Create a lead first
        lead_result = await crm.create_lead(
            name="John Doe",
            company="Medium Co",
            phone="+1234567890"
        )
        lead_id = lead_result["lead"]["id"]

        # Score with medium values
        result = await crm.score_lead(
            lead_id=lead_id,
            company_size=150,
            has_budget=False,
            timeline="3 months"
        )

        assert result["success"] is True
        assert result["qualification"] in ["medium", "low"]

    async def test_update_lead_status_success(self):
        crm = CRMTools()

        # Create a lead first
        lead_result = await crm.create_lead(
            name="John Doe",
            company="Acme Corp",
            phone="+1234567890"
        )
        lead_id = lead_result["lead"]["id"]

        # Update status
        result = await crm.update_lead_status(
            lead_id=lead_id,
            status="qualified",
            notes="Great prospect"
        )

        assert result["success"] is True
        assert result["lead"]["status"] == "qualified"
        assert "Great prospect" in result["lead"]["notes"]

    async def test_update_lead_status_not_found(self):
        crm = CRMTools()
        result = await crm.update_lead_status(
            lead_id="nonexistent",
            status="qualified"
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    async def test_get_lead_summary_success(self):
        crm = CRMTools()

        # Create and score a lead
        lead_result = await crm.create_lead(
            name="John Doe",
            company="Acme Corp",
            phone="+1234567890"
        )
        lead_id = lead_result["lead"]["id"]

        await crm.score_lead(
            lead_id=lead_id,
            company_size=500,
            has_budget=True
        )

        result = await crm.get_lead_summary(lead_id)

        assert result["success"] is True
        assert result["summary"]["name"] == "John Doe"
        assert result["summary"]["company"] == "Acme Corp"
        assert result["summary"]["status"] == "new"
        assert result["summary"]["score"] > 0

    async def test_get_lead_summary_not_found(self):
        crm = CRMTools()
        result = await crm.get_lead_summary("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestToolRegistry:
    """Test suite for ToolRegistry class."""

    def test_get_all_tools(self):
        registry = ToolRegistry()
        tools = registry.get_all_tools()

        assert isinstance(tools, dict)
        assert "check_availability" in tools
        assert "book_appointment" in tools
        assert "cancel_appointment" in tools
        assert "create_lead" in tools
        assert "score_lead" in tools
        assert "update_lead_status" in tools
        assert "get_lead_summary" in tools

    def test_get_tool_schemas(self):
        registry = ToolRegistry()
        schemas = registry.get_tool_schemas()

        assert isinstance(schemas, list)
        assert len(schemas) > 0

        for schema in schemas:
            assert "type" in schema
            assert "function" in schema
            assert "name" in schema["function"]
            assert "parameters" in schema["function"]
