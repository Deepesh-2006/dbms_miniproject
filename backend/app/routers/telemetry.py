from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import redis
from app import nosql
from app.security import allow_roles, current_user

router = APIRouter(prefix="/telemetry", tags=["telemetry (redis)"])


class TelemetryIn(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed_kmph: float = Field(ge=0, le=250)
    fuel_level_pct: float = Field(ge=0, le=100)
    engine_temp_c: float | None = Field(default=None, ge=0, le=200)


class TelemetryPatch(BaseModel):
    speed_kmph: float | None = Field(default=None, ge=0, le=250)
    fuel_level_pct: float | None = Field(default=None, ge=0, le=100)
    engine_temp_c: float | None = Field(default=None, ge=0, le=200)


def _redis_call(fn):
    try:
        return fn()
    except redis.RedisError as exc:
        raise HTTPException(503, "Telemetry store (Redis) is unavailable") from exc


@router.put("/{vehicle_id}", status_code=200)
def upsert(vehicle_id: int, payload: TelemetryIn, _=Depends(allow_roles("admin", "fleet_manager"))):
    """CREATE: store the latest reading as a Redis hash with a TTL and index its position."""
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    def op():
        pipe = nosql.client.pipeline()
        pipe.hset(nosql.telemetry_key(vehicle_id), mapping=data)
        pipe.expire(nosql.telemetry_key(vehicle_id), nosql.TELEMETRY_TTL_SECONDS)
        pipe.geoadd(nosql.GEO_KEY, (payload.longitude, payload.latitude, str(vehicle_id)))
        pipe.execute()
    _redis_call(op)
    return {"vehicle_id": vehicle_id, **data}


@router.get("/nearby/search")
def nearby(latitude: float, longitude: float, radius_km: float = 50, _=Depends(current_user)):
    """READ: GEOSEARCH for vehicles within a radius of a point."""
    res = _redis_call(lambda: nosql.client.geosearch(nosql.GEO_KEY, longitude=longitude, latitude=latitude,
                                                      radius=radius_km, unit="km", withdist=True, sort="ASC"))
    return [{"vehicle_id": int(member), "distance_km": round(dist, 2)} for member, dist in res]


@router.get("/{vehicle_id}")
def read(vehicle_id: int, _=Depends(current_user)):
    """READ: latest reading and remaining TTL."""
    key = nosql.telemetry_key(vehicle_id)
    data = _redis_call(lambda: nosql.client.hgetall(key))
    if not data:
        raise HTTPException(404, "No live telemetry for this vehicle")
    return {"vehicle_id": vehicle_id, **data, "ttl_seconds": _redis_call(lambda: nosql.client.ttl(key))}


@router.get("")
def list_all(_=Depends(current_user)):
    def op():
        out = []
        for key in nosql.client.scan_iter(match="telemetry:vehicle:*", count=100):
            out.append({"vehicle_id": int(key.rsplit(":", 1)[1]), **nosql.client.hgetall(key)})
        return sorted(out, key=lambda r: r["vehicle_id"])
    return _redis_call(op)


@router.patch("/{vehicle_id}")
def update(vehicle_id: int, payload: TelemetryPatch, _=Depends(allow_roles("admin", "fleet_manager"))):
    """UPDATE: change individual fields of an existing reading (HSET on existing hash)."""
    key = nosql.telemetry_key(vehicle_id)
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(422, "No fields supplied")
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    if not _redis_call(lambda: nosql.client.exists(key)):
        raise HTTPException(404, "No live telemetry for this vehicle")
    _redis_call(lambda: nosql.client.hset(key, mapping=fields))
    return read(vehicle_id)


@router.delete("/{vehicle_id}", status_code=204)
def delete(vehicle_id: int, _=Depends(allow_roles("admin"))):
    """DELETE: remove the hash and the geo-index entry."""
    def op():
        pipe = nosql.client.pipeline()
        pipe.delete(nosql.telemetry_key(vehicle_id))
        pipe.zrem(nosql.GEO_KEY, str(vehicle_id))
        return pipe.execute()
    if not _redis_call(op)[0]:
        raise HTTPException(404, "No live telemetry for this vehicle")
