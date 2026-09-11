from fastapi import FastAPI, Query, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import (
    FileResponse,
    StreamingResponse,
    JSONResponse,
    RedirectResponse
)
from upstash_redis.asyncio import Redis
from vercel.blob import AsyncBlobClient
import os
import re
import json
import httpx
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()

security = HTTPBearer()
redis_client = None

SUBSCRIPTIONS_HASH = "subscriptions"
VALID_TYPES = {"none", "basic", "extended"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    
    rest_url = os.getenv("UPSTASH_REDIS_REST_URL")
    rest_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    
    if not rest_url or not rest_token:
        raise RuntimeError("UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN are required")
    
    try:
        redis_client = Redis.from_env()
        print(f"✅ Connected to Upstash Redis")
        
        await redis_client.ping()
        print("✅ Redis ping successful")
        
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        raise
    
    yield
    
    if redis_client:
        await redis_client.close()
        print("🔒 Redis connection closed")

app = FastAPI(
    title="Subscription API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

ADMIN_TOKENS = os.getenv("ADMIN_TOKENS", "").split(",") if os.getenv("ADMIN_TOKENS") else []

def get_current_time() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if not ADMIN_TOKENS or token not in ADMIN_TOKENS:
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return token
    
BLOB_URL = "https://sf9o8bhy9rirx6lg.public.blob.vercel-storage.com"

IS_DEVELOPMENT = os.getenv("ENVIRONMENT") == "development"

# ============ ALLOWED TRIGGERS (управление контентом по подписке) ============
if IS_DEVELOPMENT:
    ALLOWED_TRIGGERS_FILE = "allowed_triggers-dev.json"
else:
    ALLOWED_TRIGGERS_FILE = "allowed_triggers.json"

ALLOWED_TRIGGERS_URL = f"{BLOB_URL}/{ALLOWED_TRIGGERS_FILE}"
ALLOWED_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
TIER_NAME_PATTERN = re.compile(r"^[a-z0-9_\-]{1,30}$")

DEFAULT_ALLOWED_TRIGGERS = {
    "free": [
        "GET:index.html?aicc_sid=",
        "GET:mode=home",
        "GET:cabinet",
        "GET:qti_return.html"
    ],
    "premium": [
        "GET:index.html?aicc_sid=",
        "GET:mode=home",
        "GET:cabinet",
        "GET:qti_return.html",
        "POST:qti_return.html",
        "GET:quiz1.js",
        "GET:quiz2.js",
        "GET:data/video",
        "GET:/loc_web/",
        "POST:handler.html"
    ],
    "pro": "ALL"
}

FILENAME_PATTERN = re.compile(r"^[\w.\- ]+$")

@app.get("/api/download")
async def download_file(
    filename: str = Query(..., min_length=1, max_length=255, description="Name of the file to download")
):
    if not FILENAME_PATTERN.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_url = f"{BLOB_URL}/updates/{filename}"
    print(f"download requested: {file_url}")
    
    file_info = await check_file_availability(file_url)
    
    if not file_info["available"]:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {filename}"
        )
    
    return await proxy_file(file_url, file_info["size"], filename)

@app.get("/api/subscription/status")
async def get_subscription_status(
    username: str = Query(..., min_length=2, max_length=50)
):
    # Читаем ВСЕ поля подписки
    raw = await redis_client.hget(SUBSCRIPTIONS_HASH, username)
    data = json.loads(raw)
    if not data:
        return {
            "username": username,
            "status": "not_found",
            "is_active": False,
            "expires_at": None,
            "expires_at_iso": None,
            "seconds_remaining": 0,
            "days_remaining": 0,
            "type": "none"
        }

    # Извлекаем expiry
    timestamp_str = data.get("expiry")
    sub_type = data.get("type", "none")  # новое поле

    if timestamp_str is None:
        # Странная ситуация: запись есть, но expiry нет
        return {
            "username": username,
            "status": "invalid",
            "is_active": False,
            "expires_at": None,
            "expires_at_iso": None,
            "seconds_remaining": 0,
            "days_remaining": 0,
            "type": sub_type
        }

    try:
        expires_at = int(timestamp_str)
    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid subscription data")

    current_time = get_current_time()
    is_active = current_time < expires_at
    seconds_remaining = expires_at - current_time if is_active else 0

    user = {
        "username": username,
        "status": "active" if is_active else "expired",
        "is_active": is_active,
        "expires_at": expires_at,
        "expires_at_iso": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
        "seconds_remaining": seconds_remaining,
        "days_remaining": round(seconds_remaining / 86400, 1) if is_active else 0,
        "type": sub_type
    }
    print(user)
    return user

@app.post("/api/subscription/admin/add")
async def add_subscription(
    username: str = Query(..., minlength=2, maxlength=50),
    duration_days: int = Query(..., gt=0, le=3650),
    type: str = Query("none", description="Тип подписки: none/basic/extended"),
    admin: str = Depends(verify_admin)
):
    if type not in VALID_TYPES:
        type = "basic"

    currenttime = get_current_time()
    new_expiry = currenttime + (duration_days * 86400)

    # Сохраняем оба поля в Redis Hash
    await redis_client.hset(SUBSCRIPTIONS_HASH, username, {
        "expiry": str(new_expiry),
        "type": type
    })

    user = {
        "success": True,
        "username": username,
        "duration_days": duration_days,
        "type": type,
        "expires_at": new_expiry,
        "expires_at_iso": datetime.fromtimestamp(new_expiry, tz=timezone.utc).isoformat()
    }
    print(user)
    return user

@app.put("/api/subscription/admin/extend")
async def extend_subscription(
    username: str = Query(..., min_length=2, max_length=50),
    extra_days: int = Query(..., gt=0, le=365),
    admin: str = Depends(verify_admin)
):
    timestamp_str = await redis_client.hget(SUBSCRIPTIONS_HASH, username)
    if timestamp_str is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    try:
        current_expiry = int(timestamp_str)
    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid subscription data")
    
    current_time = get_current_time()
    base_time = max(current_expiry, current_time)
    new_expiry = base_time + (extra_days * 86400)
    
    await redis_client.hset(SUBSCRIPTIONS_HASH, username, str(new_expiry))
    
    return {
        "success": True,
        "username": username,
        "old_expires_at": current_expiry,
        "new_expires_at": new_expiry,
        "extended_by_days": extra_days,
        "expires_at_iso": datetime.fromtimestamp(new_expiry, tz=timezone.utc).isoformat()
    }

@app.delete("/api/subscription/admin/revoke")
async def revoke_subscription(
    username: str = Query(..., min_length=2, max_length=50),
    admin: str = Depends(verify_admin)
):
    deleted = await redis_client.hdel(SUBSCRIPTIONS_HASH, username)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"success": True, "username": username, "action": "revoked"}

@app.get("/api/subscription/admin/list")
async def list_all_subscriptions(
    admin: str = Depends(verify_admin),
    include_expired: bool = Query(True, description="Include expired subscriptions"),
    limit: int = Query(None, ge=1, le=1000, description="Limit results (optional)")
):
    all_subscriptions = await redis_client.hgetall(SUBSCRIPTIONS_HASH)
    
    if not all_subscriptions:
        return {
            "total": 0,
            "subscriptions": {},
            "active_count": 0,
            "expired_count": 0
        }
    
    result = {}
    current_time = get_current_time()
    active_count = 0
    expired_count = 0
    print(all_subscriptions)
    for username, data_str in all_subscriptions.items():
        try:
            data = json.loads(data_str)
            timestamp_str = data.get("expiry")
            timestamp = int(timestamp_str)
            is_active = timestamp > current_time
            
            if is_active:
                active_count += 1
            else:
                expired_count += 1
            
            if not include_expired and not is_active:
                continue
            
            result[username] = {
                "expires_at": timestamp,
                "expires_at_iso": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
                "is_active": is_active,
                "days_remaining": round((timestamp - current_time) / 86400, 1) if is_active else 0,
                "type": data.get("type", "none")
            }
        except (ValueError, TypeError):
            result[username] = {"error": "Invalid data format"}
    print (result)
    if limit and len(result) > limit:
        sorted_items = sorted(
            result.items(),
            key=lambda x: (x[1].get("is_active", False), x[1].get("expires_at", 0)),
            reverse=True
        )
        result = dict(sorted_items[:limit])
    
    return {
        "total": len(all_subscriptions),
        "active_count": active_count,
        "expired_count": expired_count,
        "subscriptions": result
    }

@app.get("/api/subscription/admin/stats")
async def get_subscription_stats(admin: str = Depends(verify_admin)):
    all_subscriptions = await redis_client.hgetall(SUBSCRIPTIONS_HASH)
    
    if not all_subscriptions:
        return {
            "total": 0,
            "active": 0,
            "expired": 0,
            "expiring_soon": 0,
            "average_days_remaining": 0
        }
    
    current_time = get_current_time()
    active = 0
    expired = 0
    expiring_soon = 0
    total_days = 0
    
    for timestamp_str in all_subscriptions.values():
        try:
            timestamp = int(timestamp_str)
            if timestamp > current_time:
                active += 1
                days_remaining = (timestamp - current_time) / 86400
                total_days += days_remaining
                if days_remaining < 7:
                    expiring_soon += 1
            else:
                expired += 1
        except (ValueError, TypeError):
            pass
    
    return {
        "total": len(all_subscriptions),
        "active": active,
        "expired": expired,
        "expiring_soon": expiring_soon,
        "average_days_remaining": round(total_days / active, 1) if active > 0 else 0
    }

@app.delete("/api/subscription/admin/clear")
async def clear_all_subscriptions(admin: str = Depends(verify_admin)):
    
    await redis_client.delete(SUBSCRIPTIONS_HASH)
    return {
        "success": True,
        "action": "cleared all subscriptions"
    }

# ============ ALLOWED TRIGGERS ENDPOINTS ============

def validate_triggers(rules) -> dict:
    """Валидирует структуру allowed_triggers.

    Ожидаемый формат:
    {
      "free": ["GET:index.html?aicc_sid=", ...],
      "pro": "ALL"
    }
    """
    if not isinstance(rules, dict) or not rules:
        raise HTTPException(
            status_code=400,
            detail="Rules must be a non-empty object: {\"tier\": [\"GET:path\", ...] | \"ALL\"}"
        )

    validated = {}
    for tier, value in rules.items():
        tier = str(tier).strip().lower()
        if not TIER_NAME_PATTERN.match(tier):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier name: '{tier}' (allowed: a-z, 0-9, _, -, max 30 chars)"
            )

        if isinstance(value, str):
            if value.strip().upper() == "ALL":
                validated[tier] = "ALL"
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tier '{tier}': string value must be 'ALL'"
                )
        elif isinstance(value, list):
            clean_rules = []
            for item in value:
                if not isinstance(item, str):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Tier '{tier}': each rule must be a string"
                    )
                rule = item.strip()
                if not rule:
                    continue
                match = re.match(
                    r"^(" + "|".join(ALLOWED_HTTP_METHODS) + r"):(.+)$",
                    rule,
                    re.IGNORECASE
                )
                if not match:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Tier '{tier}': invalid rule '{rule}'. "
                            f"Expected format 'METHOD:path', "
                            f"METHOD one of {sorted(ALLOWED_HTTP_METHODS)}"
                        )
                    )
                clean_rules.append(f"{match.group(1).upper()}:{match.group(2)}")
            validated[tier] = clean_rules
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Tier '{tier}': value must be a list of rules or 'ALL'"
            )

    return validated


async def write_triggers_to_blob(rules: dict) -> dict:
    """Записывает rules в allowed_triggers.json на Vercel Blob."""
    token = os.getenv("BLOB_READ_WRITE_TOKEN")
    if not token:
        raise HTTPException(
            status_code=503,
            detail="BLOB_READ_WRITE_TOKEN is not configured"
        )

    payload = json.dumps(rules, ensure_ascii=False, indent=2).encode("utf-8")

    try:
        client = AsyncBlobClient(token=token)
        blob = await client.put(
            ALLOWED_TRIGGERS_FILE,
            payload,
            access="public",
            content_type="application/json",
            add_random_suffix=False,
            overwrite=True,
            cache_control_max_age=60
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to write triggers to blob: {str(e)}"
        )

    return {"url": blob.url, "pathname": blob.pathname}


@app.get("/api/triggers")
async def get_allowed_triggers():
    """Публичное чтение allowed_triggers (для системы контроля контента)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(ALLOWED_TRIGGERS_URL)
            if response.status_code == 200:
                return {
                    "source": "blob",
                    "file": ALLOWED_TRIGGERS_FILE,
                    "rules": response.json()
                }
    except Exception:
        pass

    return {
        "source": "default",
        "file": ALLOWED_TRIGGERS_FILE,
        "rules": DEFAULT_ALLOWED_TRIGGERS
    }


@app.put("/api/triggers/admin")
async def save_allowed_triggers(
    rules: dict = Body(...),
    admin: str = Depends(verify_admin)
):
    """Сохраняет правила allowed_triggers в Vercel Blob."""
    validated = validate_triggers(rules)
    blob_info = await write_triggers_to_blob(validated)

    return {
        "success": True,
        "file": ALLOWED_TRIGGERS_FILE,
        "rules": validated,
        **blob_info
    }


@app.post("/api/triggers/admin/reset")
async def reset_allowed_triggers(admin: str = Depends(verify_admin)):
    """Сбрасывает правила к значениям по умолчанию."""
    blob_info = await write_triggers_to_blob(DEFAULT_ALLOWED_TRIGGERS)

    return {
        "success": True,
        "file": ALLOWED_TRIGGERS_FILE,
        "rules": DEFAULT_ALLOWED_TRIGGERS,
        **blob_info
    }


@app.get("/api/health")
async def health_check():
    try:
        await redis_client.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"disconnected: {str(e)}"
    
    return {
        "status": "ok",
        "service": "subscription-api",
        "version": "2.0.0",
        "redis": redis_status,
        "storage_type": "hash",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api")
async def api_root():
    return {
        "service": "Subscription API",
        "version": "2.0.0",
        "storage": "Redis Hash",
        "endpoints": {
            "health": "/api/health",
            "status": "/api/subscription/status?username={username}",
            "admin_list": "/api/subscription/admin/list",
            "admin_stats": "/api/subscription/admin/stats",
            "docs": "/api/docs"
        }
    }

async def proxy_file(url: str, file_size: int, filename: str = "update.zip"):
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch file"
                )
            
            return StreamingResponse(
                iter([response.content]),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Length": str(len(response.content)),
                    "X-File-Source": "blob-proxy",
                    "Cache-Control": "no-cache, no-store"
                }
            )          
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Storage timeout - try using redirect endpoint"
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Proxy download failed: {str(e)}"
        )

async def check_file_availability(url: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.head(url, timeout=5.0)
            if response.status_code == 200:
                size = int(response.headers.get("content-length", 0))
                return {
                    "available": True,
                    "size": size,
                    "content_type": response.headers.get("content-type", "application/zip")
                }
            else:
                return {"available": False, "status_code": response.status_code}
                
        except httpx.TimeoutException:
            return {"available": False, "error": "Timeout"}
        except Exception as e:
            return {"available": False, "error": str(e)}

async def fallback_to_github():
    return JSONResponse(
        status_code=503,
        content={
            "error": "Storage unavailable",
            "fallback": "https://github.com/your-repo/releases/latest/download/update.zip"
        }
    )
