"""
Settings API Routes — read and write radio.conf fields.

Only allowlisted fields are exposed. Writes are done in-place,
preserving comments and structure. A file lock prevents concurrent
corruption.
"""

import asyncio
import fcntl
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator, model_validator

logger = logging.getLogger(__name__)

router = APIRouter()

# Candidate paths for radio.conf (same order as main.py)
_CONF_CANDIDATES = [
    Path("/app/config/radio.conf"),
    Path(__file__).parent.parent.parent.parent / "config" / "radio.conf",
]

# Fields that may be read or written via the API
ALLOWLIST: Dict[str, type] = {
    "HOTSPOT_SSID": str,
    "HOTSPOT_PASSWORD": str,
    "DEFAULT_VOLUME": int,
    "MIN_VOLUME": int,
    "MAX_VOLUME": int,
    "NOTIFICATION_VOLUME": int,
    "ROTARY_CLOCKWISE_INCREASES": bool,
    "ROTARY_VOLUME_STEP": int,
    "ROTARY_DEBOUNCE": float,
    "LONG_PRESS_DURATION": float,
    "TRIPLE_PRESS_INTERVAL": float,
}

# All fields require a restart to take effect
RESTART_REQUIRED = set(ALLOWLIST.keys())


def _conf_path() -> Path:
    for p in _CONF_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("radio.conf not found")


def _read_conf(path: Path) -> Dict[str, str]:
    """Return allowlisted key→value pairs from radio.conf."""
    result: Dict[str, str] = {}
    with open(path, "r") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in stripped:
                    continue
                key, _, value = stripped.partition("=")
                key = key.strip()
                if key in ALLOWLIST:
                    result[key] = value.strip()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    return result


def _write_conf(path: Path, updates: Dict[str, str]) -> List[str]:
    """
    Write only the keys in `updates` back to radio.conf in-place.
    Returns list of keys that were actually changed.
    """
    changed: List[str] = []

    with open(path, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            lines = f.readlines()
            new_lines = []
            written = set()

            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key = stripped.partition("=")[0].strip()
                    if key in updates:
                        old_val = stripped.partition("=")[2].strip()
                        new_val = updates[key]
                        if old_val != new_val:
                            # Preserve any inline comment after the value
                            new_lines.append(f"{key}={new_val}\n")
                            changed.append(key)
                        else:
                            new_lines.append(line)
                        written.add(key)
                        continue
                new_lines.append(line)

            f.seek(0)
            f.writelines(new_lines)
            f.truncate()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    return changed


def _coerce(key: str, raw: str) -> Any:
    """Coerce a raw string value from conf to its Python type."""
    t = ALLOWLIST[key]
    if t is bool:
        return raw.lower() in ("true", "1", "yes")
    return t(raw)


# ── Models ────────────────────────────────────────────────────────────────────

class SettingsPayload(BaseModel):
    HOTSPOT_SSID: Optional[str] = None
    HOTSPOT_PASSWORD: Optional[str] = None
    DEFAULT_VOLUME: Optional[int] = None
    MIN_VOLUME: Optional[int] = None
    MAX_VOLUME: Optional[int] = None
    NOTIFICATION_VOLUME: Optional[int] = None
    ROTARY_CLOCKWISE_INCREASES: Optional[bool] = None
    ROTARY_VOLUME_STEP: Optional[int] = None
    ROTARY_DEBOUNCE: Optional[float] = None
    LONG_PRESS_DURATION: Optional[float] = None
    TRIPLE_PRESS_INTERVAL: Optional[float] = None

    @field_validator("HOTSPOT_PASSWORD")
    @classmethod
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError("HOTSPOT_PASSWORD must be at least 8 characters (WPA2)")
        return v

    @field_validator("DEFAULT_VOLUME", "MIN_VOLUME", "MAX_VOLUME", "NOTIFICATION_VOLUME")
    @classmethod
    def volume_range(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Volume must be between 0 and 100")
        return v

    @field_validator("ROTARY_VOLUME_STEP")
    @classmethod
    def step_range(cls, v):
        if v is not None and not (1 <= v <= 20):
            raise ValueError("ROTARY_VOLUME_STEP must be between 1 and 20")
        return v

    @field_validator("ROTARY_DEBOUNCE")
    @classmethod
    def debounce_range(cls, v):
        if v is not None and not (0.01 <= v <= 1.0):
            raise ValueError("ROTARY_DEBOUNCE must be between 0.01 and 1.0")
        return v

    @field_validator("LONG_PRESS_DURATION")
    @classmethod
    def long_press_range(cls, v):
        if v is not None and not (0.5 <= v <= 10.0):
            raise ValueError("LONG_PRESS_DURATION must be between 0.5 and 10.0")
        return v

    @field_validator("TRIPLE_PRESS_INTERVAL")
    @classmethod
    def triple_press_range(cls, v):
        if v is not None and not (0.1 <= v <= 2.0):
            raise ValueError("TRIPLE_PRESS_INTERVAL must be between 0.1 and 2.0")
        return v

    @model_validator(mode="after")
    def volume_ordering(self):
        mn = self.MIN_VOLUME
        df = self.DEFAULT_VOLUME
        mx = self.MAX_VOLUME
        if mn is not None and df is not None and mn > df:
            raise ValueError("MIN_VOLUME must be ≤ DEFAULT_VOLUME")
        if df is not None and mx is not None and df > mx:
            raise ValueError("DEFAULT_VOLUME must be ≤ MAX_VOLUME")
        if mn is not None and mx is not None and mn > mx:
            raise ValueError("MIN_VOLUME must be ≤ MAX_VOLUME")
        return self


class SettingsResponse(BaseModel):
    changed: List[str]
    restart_required: List[str]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/settings")
async def get_settings() -> Dict[str, Any]:
    """Return current values of all allowlisted radio.conf fields."""
    try:
        path = _conf_path()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="radio.conf not found")

    try:
        raw = _read_conf(path)
        return {k: _coerce(k, v) for k, v in raw.items()}
    except Exception as e:
        logger.error(f"Failed to read settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to read configuration")


@router.put("/settings", response_model=SettingsResponse)
async def put_settings(payload: SettingsPayload) -> SettingsResponse:
    """Write changed allowlisted fields back to radio.conf in-place."""
    try:
        path = _conf_path()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="radio.conf not found")

    # Build string repr of only the fields provided in the request
    updates: Dict[str, str] = {}
    for key in ALLOWLIST:
        val = getattr(payload, key, None)
        if val is None:
            continue
        if isinstance(val, bool):
            updates[key] = str(val).lower()
        else:
            updates[key] = str(val)

    if not updates:
        return SettingsResponse(changed=[], restart_required=[])

    try:
        changed = await asyncio.to_thread(_write_conf, path, updates)
    except Exception as e:
        logger.error(f"Failed to write settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to write configuration")

    restart_required = [k for k in changed if k in RESTART_REQUIRED]
    logger.info(f"Settings updated: {changed}")
    return SettingsResponse(changed=changed, restart_required=restart_required)
