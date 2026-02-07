"""Playground API endpoints for testing with example scenarios."""

import json
import random
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/playground", tags=["playground"])


class Ticket(BaseModel):
    """Single ticket from anonymized dataset."""
    conversationId: str
    customerId: str
    createdAt: str
    conversationType: str
    subject: str
    conversation: str


class RandomTicketRequest(BaseModel):
    """Request for random tickets."""
    count: Optional[int] = 1
    intent_filter: Optional[str] = None  # Filter by suspected intent


def load_tickets() -> List[Ticket]:
    """Load tickets from data file."""
    data_path = Path(__file__).parent.parent / "data" / "anonymized_tickets.json"
    
    if not data_path.exists():
        raise HTTPException(status_code=404, detail="Tickets file not found")
    
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return [Ticket(**ticket) for ticket in data]


def extract_first_customer_message(conversation: str) -> str:
    """Extract the first customer message from conversation."""
    lines = conversation.split('Customer\'s message: "')
    if len(lines) > 1:
        # Get first customer message
        first_msg = lines[1].split('"')[0]
        return first_msg.strip()
    
    # Fallback: return first 200 chars
    return conversation[:200]


def classify_intent(subject: str, conversation: str) -> str:
    """Simple rule-based intent classification for filtering."""
    text = (subject + " " + conversation).lower()
    
    if any(word in text for word in ["where", "tracking", "shipped", "delivery", "arrived", "status"]):
        return "wismo"
    elif any(word in text for word in ["wrong", "missing", "incorrect", "received"]):
        return "wrong_item"
    elif any(word in text for word in ["refund", "return", "money back"]):
        return "refund"
    elif any(word in text for word in ["cancel", "address", "change"]):
        return "order_mod"
    elif any(word in text for word in ["not working", "defect", "no effect", "quality"]):
        return "product_issue"
    elif any(word in text for word in ["subscription", "billing", "recurring"]):
        return "subscription"
    elif any(word in text for word in ["discount", "promo", "code", "coupon"]):
        return "discount"
    elif any(word in text for word in ["thank", "love", "great", "amazing"]):
        return "feedback"
    
    return "unknown"


@router.get("/tickets")
async def get_all_tickets():
    """Get all available test tickets."""
    tickets = load_tickets()
    
    # Add intent classification to each ticket
    enriched = []
    for ticket in tickets:
        ticket_dict = ticket.model_dump()
        ticket_dict["suggested_intent"] = classify_intent(ticket.subject, ticket.conversation)
        ticket_dict["first_message"] = extract_first_customer_message(ticket.conversation)
        enriched.append(ticket_dict)
    
    return {
        "total": len(enriched),
        "tickets": enriched
    }


@router.post("/random")
async def get_random_tickets(request: RandomTicketRequest):
    """Get random tickets for testing."""
    tickets = load_tickets()
    
    # Filter by intent if specified
    if request.intent_filter:
        filtered = []
        for ticket in tickets:
            intent = classify_intent(ticket.subject, ticket.conversation)
            if intent == request.intent_filter:
                filtered.append(ticket)
        tickets = filtered
    
    if not tickets:
        raise HTTPException(status_code=404, detail="No tickets found matching filter")
    
    # Select random tickets
    count = min(request.count, len(tickets))
    selected = random.sample(tickets, count)
    
    # Enrich with metadata
    result = []
    for ticket in selected:
        ticket_dict = ticket.model_dump()
        ticket_dict["suggested_intent"] = classify_intent(ticket.subject, ticket.conversation)
        ticket_dict["first_message"] = extract_first_customer_message(ticket.conversation)
        result.append(ticket_dict)
    
    return {
        "count": len(result),
        "tickets": result
    }


@router.get("/intents")
async def get_available_intents():
    """Get list of available intent categories with counts."""
    tickets = load_tickets()
    
    intent_counts = {}
    for ticket in tickets:
        intent = classify_intent(ticket.subject, ticket.conversation)
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    return {
        "intents": [
            {"name": intent, "count": count}
            for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)
        ],
        "total": len(tickets)
    }


__all__ = ["router"]
