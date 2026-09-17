from fastapi import APIRouter, HTTPException
from app.schemas import VehicleCommand
from app.vehicle import vehicle_manager

router = APIRouter(prefix="/vehicle", tags=["Vehicle"])

@router.post("/command")
async def execute_command(cmd: VehicleCommand):
    try:
        await vehicle_manager.send_command(cmd.command, cmd.param1, cmd.param2)
        return {"status": "dispatched", "command": cmd.command}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
