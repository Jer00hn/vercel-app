from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import (
    FileResponse,
    StreamingResponse,
    JSONResponse,
    RedirectResponse
)
from upstash_redis.asyncio import Redis
import os
import httpx
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()

security = HTTPBearer()
redis_client = None

SUBSCRIPTIONS_HASH = "subscriptions"

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

if IS_DEVELOPMENT:
    VERSION_FILE = "version-dev.json"
    UPDATE_FILE = "update-dev.zip"
else:
    VERSION_FILE = "version.json"
    UPDATE_FILE = "update-bytecode.zip"

FILE_URL = f"{BLOB_URL}/{UPDATE_FILE}"
VERSION_URL = f"{BLOB_URL}/{VERSION_FILE}"

@app.get("/api/update/check")
async def check_update():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(VERSION_URL)
            
            if response.status_code == 200:
                return response.json()
            else:
                return JSONResponse(
                    status_code=404,
                    content={"error": "Version file not found"}
                )
                
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=503,
            content={"error": "Version check timeout"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/update/proxy")
async def download_proxy():
    print(f"check is aviable: {FILE_URL}")
    file_info = await check_file_availability(FILE_URL)
    
    if not file_info["available"]:
        return await fallback_to_github()
    
    return await proxy_file(FILE_URL, file_info["size"])

@app.get("/api/subscription/status")
async def get_subscription_status(
    username: str = Query(..., min_length=2, max_length=50)
):
    timestamp_str = await redis_client.hget(SUBSCRIPTIONS_HASH, username)
    
    if timestamp_str is None:
        return {
            "username": username,
            "status": "not_found",
            "is_active": False,
            "expires_at": None,
            "seconds_remaining": 0,
            "days_remaining": 0
        }
    
    try:
        expires_at = int(timestamp_str)
    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid subscription data")
    
    current_time = get_current_time()
    is_active = current_time < expires_at
    seconds_remaining = expires_at - current_time if is_active else 0
    
    return {
        "username": username,
        "status": "active" if is_active else "expired",
        "is_active": is_active,
        "expires_at": expires_at,
        "expires_at_iso": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
        "seconds_remaining": seconds_remaining,
        "days_remaining": round(seconds_remaining / 86400, 1) if is_active else 0
    }

@app.post("/api/subscription/admin/add")
async def add_subscription(
    username: str = Query(..., min_length=2, max_length=50),
    duration_days: int = Query(..., gt=0, le=3650),
    admin: str = Depends(verify_admin)
):
    current_time = get_current_time()
    new_expiry = current_time + (duration_days * 86400)
    
    await redis_client.hset(SUBSCRIPTIONS_HASH, username, str(new_expiry))
    
    return {
        "success": True,
        "username": username,
        "duration_days": duration_days,
        "expires_at": new_expiry,
        "expires_at_iso": datetime.fromtimestamp(new_expiry, tz=timezone.utc).isoformat()
    }

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
    
    for username, timestamp_str in all_subscriptions.items():
        try:
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
                "days_remaining": round((timestamp - current_time) / 86400, 1) if is_active else 0
            }
        except (ValueError, TypeError):
            result[username] = {"error": "Invalid data format"}
    
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

@app.get("/api/subscription/admin/clear")
async def clear_all_subscriptions(admin: str = Depends(verify_admin)):
    if not IS_DEVELOPMENT:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available in development mode"
        )
    
    await redis_client.delete(SUBSCRIPTIONS_HASH)
    return {
        "success": True,
        "action": "cleared all subscriptions"
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

async def proxy_file(url: str, file_size: int):
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(FILE_URL)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch file"
                )
            
            return StreamingResponse(
                iter([response.content]),
                media_type="application/zip",
                headers={
                    "Content-Disposition": "attachment; filename=update.zip",
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
