from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

# Request Models
class StationStateUpdate(BaseModel):
    """Request model for updating station state"""
    enabled: bool = Field(..., description="Whether the station is enabled")

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True
            }
        }

class StationSettingsUpdate(BaseModel):
    current_cycles: int = Field(ge=0)
    motor_failures: int = Field(ge=0)
    switch_failures: int = Field(ge=0)

class TimerSettings(BaseModel):
    """Request model for setting timer"""
    hours: int = Field(ge=0, lt=100)
    minutes: int = Field(ge=0, lt=60)

    class Config:
        json_schema_extra = {
            "example": {
                "hours": 1,
                "minutes": 30
            }
        }

class SystemSettingsUpdate(BaseModel):
    """Request model for updating system settings"""
    cutoff_voltage: float = Field(..., ge=10.5, le=13.5, description="Cutoff voltage threshold (10.5-13.5V)")
    motor_current_threshold: float = Field(..., ge=50.0, le=200.0, description="Motor current threshold (50-200A)")
    switch_current_threshold: float = Field(..., ge=0.1, le=50.0, description="Switch current threshold (0.1-50A)")
    cycle_limit: int = Field(..., ge=1, le=1000000, description="Maximum cycle limit (1-1,000,000)")
    motor_failure_threshold: int = Field(..., ge=1, le=1000, description="Motor failure threshold (1-1,000)")
    switch_failure_threshold: int = Field(..., ge=1, le=1000, description="Switch failure threshold (1-1,000)")
    cycles_per_minute: int = Field(..., ge=1, le=12, description="Cycles per minute (1-12)")

    class Config:
        json_schema_extra = {
            "example": {
                "cutoff_voltage": 12.0,
                "motor_current_threshold": 0.5,
                "switch_current_threshold": 0.3,
                "cycle_limit": 100000,
                "motor_failure_threshold": 10,
                "switch_failure_threshold": 10,
                "cycles_per_minute": 6
            }
        }

    @field_validator('cutoff_voltage')
    @classmethod
    def validate_voltage(cls, v: float) -> float:
        if not 10.5 <= v <= 13.5:
            raise ValueError("Cutoff voltage must be between 10.5V and 13.5V")
        return round(v, 1)

    @field_validator('motor_current_threshold', 'switch_current_threshold')
    @classmethod
    def validate_current(cls, v: float, info) -> float:
        if info.field_name == 'motor_current_threshold' and not 50.0 <= v <= 200.0:
            raise ValueError("Motor current threshold must be between 50A and 200A")
        if info.field_name == 'switch_current_threshold' and not 0.1 <= v <= 50.0:
            raise ValueError("Switch current threshold must be between 0.1A and 50A")
        return round(v, 1)

# Response Models
class StationResponse(BaseModel):
    """Response model for station status"""
    id: int = Field(..., ge=1, le=4, description="Station ID (1-4)")
    enabled: bool = Field(..., description="Whether the station is enabled")
    motor_failures: int = Field(..., ge=0, description="Number of motor failures")
    switch_failures: int = Field(..., ge=0, description="Number of switch failures")
    current_cycles: int = Field(..., ge=0, description="Current cycle count")
    motor_current: float = Field(..., ge=0, description="Current motor current reading (A)")
    switch_current: float = Field(..., ge=0, description="Current switch current reading (A)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "enabled": True,
                "motor_failures": 0,
                "switch_failures": 0,
                "current_cycles": 100,
                "motor_current": 0.5,
                "switch_current": 0.3
            }
        }

class SystemStatusResponse(BaseModel):
    """Response model for system status"""
    machine_state: str = Field(..., description="Current machine state (on/off/disabled)")
    supply_voltage: float = Field(..., ge=0, description="Current supply voltage (V)")
    timer_active: bool = Field(..., description="Whether timer is active")
    timer_end_time: Optional[datetime] = Field(None, description="Timer end time in UTC")
    stations: List[StationResponse] = Field(..., description="List of station states")

    class Config:
        json_schema_extra = {
            "example": {
                "machine_state": "off",
                "supply_voltage": 13.2,
                "timer_active": True,
                "timer_end_time": "2024-03-21T15:30:00Z",
                "stations": [
                    {
                        "id": 1,
                        "enabled": True,
                        "motor_failures": 0,
                        "switch_failures": 0,
                        "current_cycles": 100,
                        "motor_current": 0.5,
                        "switch_current": 0.3
                    }
                ]
            }
        }

class SystemSettingsResponse(BaseModel):
    """Response model for system settings"""
    cutoff_voltage: float = Field(..., ge=10.0, le=15.0, description="Cutoff voltage threshold (V)")
    motor_current_threshold: float = Field(..., ge=0.1, le=200, description="Motor current threshold (A)")
    switch_current_threshold: float = Field(..., ge=0.1, le=50, description="Switch current threshold (A)")
    cycle_limit: int = Field(..., ge=1, le=1000000, description="Maximum cycle limit")
    motor_failure_threshold: int = Field(..., ge=1, le=1000, description="Motor failure threshold")
    switch_failure_threshold: int = Field(..., ge=1, le=1000, description="Switch failure threshold")
    cycles_per_minute: int = Field(..., ge=1, le=12, description="Cycles per minute (1-12)")

    class Config:
        json_schema_extra = {
            "example": {
                "cutoff_voltage": 12.0,
                "motor_current_threshold": 0.5,
                "switch_current_threshold": 0.3,
                "cycle_limit": 100000,
                "motor_failure_threshold": 10,
                "switch_failure_threshold": 10,
                "cycles_per_minute": 6
            }
        }

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = Field(..., description="Whether the operation was successful")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True
            }
        } 