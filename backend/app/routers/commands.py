from fastapi import APIRouter, HTTPException, status
from app.schemas import CommandRequest
from app.vehicle import vehicle_manager

router = APIRouter(prefix="/api/command", tags=["Commands"])

@router.post("")
async def execute_command(payload: CommandRequest):
    cmd = payload.command.upper()
    if cmd not in ["ARM", "DISARM", "SET_MODE"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported command '{payload.command}'"
        )

    success = await vehicle_manager.send_command(cmd, mode=payload.mode)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to uplink command '{cmd}' to vehicle"
        )

    return {"status": "ACK", "dispatched": cmd}