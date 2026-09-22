from fastapi import APIRouter, HTTPException, status
from app.schemas import CommandRequest
from app.vehicle import vehicle_manager

router = APIRouter(prefix="/api/command", tags=["Commands"])


@router.post("")
async def execute_command(payload: CommandRequest):
    """
    The single canonical command-uplink endpoint. `command` and `mode`
    (when SET_MODE is used) are validated by CommandRequest itself — an
    unrecognized value never reaches the vehicle layer, it gets a 422
    straight from FastAPI/Pydantic.
    """
    try:
        success = await vehicle_manager.send_command(
            payload.command, mode=payload.mode, force=payload.force
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to uplink command '{payload.command}' to vehicle",
        )

    return {"status": "ACK", "dispatched": payload.command}
