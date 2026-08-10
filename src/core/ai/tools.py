"""
Tool Registry - AI Backend Tool Discovery

Allows LLMs to discover available tools during voice calls.
This enables the AI to automatically find and use the availability checker.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from datetime import datetime, timezone


# Tool metadata for LLM discovery
class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    example: Any = None


class Tool(BaseModel):
    name: str
    description: str
    category: str
    parameters: List[ToolParameter]
    endpoint: str
    method: str = "POST"


# Available tools registry
AVAILABLE_TOOLS: List[Tool] = [
    Tool(
        name="check_availability",
        description="Check restaurant table availability for a specific time and party size",
        category="restaurant_operations",
        parameters=[
            ToolParameter(
                name="restaurantId",
                type="string",
                description="Restaurant identifier or name",
                example="resto-123",
            ),
            ToolParameter(
                name="bookingTimestamp",
                type="string",
                description="ISO timestamp for desired booking time",
                example="2024-02-06T19:00:00Z",
            ),
            ToolParameter(
                name="partySize",
                type="integer",
                description="Number of people in the dining party",
                example=4,
            ),
        ],
        endpoint="/v1/ai/check-availability",
        method="POST",
    )
]

# Tool registry router
router = APIRouter(prefix="/v1/tools", tags=["tools"])


@router.get("/discover", response_model=List[Tool])
async def discover_tools():
    """
    Discover available AI tools for LLM integration.

    This endpoint allows LLMs to discover what tools are available
    during voice calls and automatically use them.
    """
    return AVAILABLE_TOOLS


@router.get("/{tool_name}", response_model=Tool)
async def get_tool_details(tool_name: str):
    """
    Get detailed information about a specific tool.
    """
    tool = next((t for t in AVAILABLE_TOOLS if t.name == tool_name), None)
    if not tool:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return tool


@router.post("/{tool_name}/execute")
async def execute_tool(tool_name: str, parameters: Dict[str, Any]):
    """
    Execute a tool with given parameters.

    This provides a unified interface for LLMs to execute tools
    without needing to know specific endpoints.
    """
    tool = next((t for t in AVAILABLE_TOOLS if t.name == tool_name), None)
    if not tool:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=501, detail=f"Tool '{tool_name}' not implemented"
        )

    # Route to the appropriate tool handler
    if tool_name == "check_availability":
        from src.core.ai.availability import AvailabilityRequest, check_availability

        # Validate required parameters
        required_params = ["restaurantId", "bookingTimestamp", "partySize"]
        missing_params = [
            param
            for param in required_params
            if param not in parameters or parameters[param] is None
        ]

        if missing_params:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required parameters: {', '.join(missing_params)}",
            )

        # Validate party size
        party_size = parameters.get("partySize")
        if not isinstance(party_size, int) or party_size < 1 or party_size > 20:
            raise HTTPException(
                status_code=400, detail="Party size must be an integer between 1 and 20"
            )

        # Convert parameters to AvailabilityRequest format
        availability_request = AvailabilityRequest(
            restaurant_id=parameters.get("restaurantId"),
            booking_timestamp=parameters.get("bookingTimestamp"),
            party_size=parameters.get("partySize"),
            request_context={
                "source": "tool_execution",
                "session_id": parameters.get("sessionId", "tool_exec"),
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            },
        )
        return await check_availability(availability_request)

    from fastapi import HTTPException

    raise HTTPException(status_code=501, detail=f"Tool '{tool_name}' not implemented")
