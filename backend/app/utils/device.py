from typing import Optional
from pydantic import BaseModel
from fastapi import Request

class DeviceContext(BaseModel):
    userAgent: Optional[str] = None
    os: Optional[str] = None
    osVersion: Optional[str] = None
    deviceType: str
    appVersion: Optional[str] = None
    deviceModel: Optional[str] = None
    locale: Optional[str] = None
    ip: Optional[str] = None

def parse_device(request: Request, default_type: str = "web") -> DeviceContext:
    headers = request.headers
    return DeviceContext(
        userAgent=headers["user-agent"] if "user-agent" in headers else None,
        os=headers["x-device-os"] if "x-device-os" in headers else None,
        osVersion=headers["x-device-os-version"] if "x-device-os-version" in headers else None,
        deviceType=headers["x-device-type"] if "x-device-type" in headers else default_type,
        appVersion=headers["x-app-version"] if "x-app-version" in headers else None,
        deviceModel=headers["x-device-model"] if "x-device-model" in headers else None,
        locale=headers["accept-language"] if "accept-language" in headers else None,
        ip=request.client.host if request.client else None,
    )
