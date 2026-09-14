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
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator, model_validator

from core.config import parse_conf_lines

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
    with open(path, "r") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            parsed = parse_conf_lines(f)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    return {k: v for k, v in parsed.items() if k in ALLOWLIST}


def _write_conf(path: Path, updates: Dict[str, str]) -> List[str]:
    """
    Write only the keys in `updates` back to radio.conf atomically
    (tmp file in the same directory + rename, so power loss mid-write
    can never leave a truncated file). Returns keys actually changed.
    """
    # Defence-in-depth: a newline in a value would inject arbitrary
    # KEY=VALUE lines that main._load_radio_conf() loads into os.environ.
    for key, value in updates.items():
        if "\n" in value or "\r" in value:
            raise ValueError(f"Control characters not allowed in value for {key}")

    changed: List[str] = []

    # Dedicated lock file serialises writers across the whole
    # read → write-tmp → rename sequence (the conf file itself gets
    # replaced by the rename, so its own inode can't carry the lock).
    lock_path = path.with_name(path.name + ".lock")
    with open(lock_path, "w") as lock_f:
        fcntl.flock(lock_f, fcntl.LOCK_EX)
        try:
            with open(path, "r") as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key = stripped.partition("=")[0].strip()
                    if key in updates:
                        old_val = stripped.partition("=")[2].strip()
                        new_val = updates[key]
                        if old_val != new_val:
                            new_lines.append(f"{key}={new_val}\n")
                            changed.append(key)
                        else:
                            new_lines.append(line)
                        continue
                new_lines.append(line)

            tmp = path.with_name(path.name + ".tmp")
            try:
                with open(tmp, "w") as f:
                    f.writelines(new_lines)
                    f.flush()
                    os.fsync(f.fileno())
                os.chmod(tmp, path.stat().st_mode & 0o777)
                tmp.replace(path)
            except BaseException:
                tmp.unlink(missing_ok=True)
                raise
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)

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

    @field_validator("HOTSPOT_SSID", "HOTSPOT_PASSWORD")
    @classmethod
    def printable_ascii_only(cls, v, info):
        # Newlines would inject arbitrary KEY=VALUE lines into radio.conf,
        # which is loaded into os.environ at startup; other control chars
        # and non-ASCII break the plain key=value parseback.
        if v is not None and not re.fullmatch(r"[\x20-\x7e]*", v):
            raise ValueError(
                f"{info.field_name} must contain only printable ASCII characters"
            )
        return v

    @field_validator("HOTSPOT_SSID")
    @classmethod
    def ssid_length(cls, v):
        if v is not None and not (1 <= len(v.encode("utf-8")) <= 32):
            raise ValueError("HOTSPOT_SSID must be 1-32 bytes (802.11)")
        return v

    @field_validator("HOTSPOT_PASSWORD")
    @classmethod
    def password_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError("HOTSPOT_PASSWORD must be at least 8 characters (WPA2)")
        if v is not None and len(v) > 63:
            raise ValueError("HOTSPOT_PASSWORD must be at most 63 characters (WPA2)")
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
