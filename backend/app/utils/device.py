from typing import Optional
from app.models.daos import DeviceSnippet
from fastapi import Request

class DeviceContext(DeviceSnippet):
    deviceType: Optional[str] = "web"

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
