import pytest
from pydantic import ValidationError

from app.schemas.ticket import TicketCreate, TicketUpdate


def test_ticket_create_trims_whitespace():
    ticket = TicketCreate(
        subject="  Laptop issue  ",
        description="  Laptop is not starting.  ",
        category="  hardware  ",
    )

    assert ticket.subject == "Laptop issue"
    assert ticket.description == "Laptop is not starting."
    assert ticket.category == "hardware"


@pytest.mark.parametrize(
    "field,value",
    [
        ("subject", "     "),
        ("description", "          "),
        ("category", "     "),
    ],
)
def test_ticket_create_rejects_whitespace_only_values(field, value):
    data = {
        "subject": "Laptop issue",
        "description": "Laptop is not starting.",
        "category": "hardware",
    }

    data[field] = value

    with pytest.raises(ValidationError):
        TicketCreate(**data)


def test_ticket_update_trims_whitespace():
    ticket = TicketUpdate(subject="  Updated subject  ")

    assert ticket.subject == "Updated subject"


@pytest.mark.parametrize(
    "field",
    ["subject", "description", "category"],
)
def test_ticket_update_rejects_whitespace_only_values(field):
    with pytest.raises(ValidationError):
        TicketUpdate(**{field: "     "})


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"subject": None},
        {"description": None},
        {"category": None},
        {
            "subject": None,
            "description": None,
            "category": None,
        },
    ],
)
def test_ticket_update_rejects_empty_or_null_only_payloads(data):
    with pytest.raises(ValidationError):
        TicketUpdate(**data)


def test_ticket_update_accepts_one_valid_field():
    ticket = TicketUpdate(category="network")

    assert ticket.category == "network"
