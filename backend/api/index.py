from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from upstash_redis.asyncio import Redis
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Загружаем .env только для локальной разработки
if os.path.exists(".env"):
    load_dotenv()

security = HTTPBearer()
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    
    rest_url = os.getenv("UPSTASH_REDIS_REST_URL")
    rest_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    
    if not rest_url or not rest_token:
        raise RuntimeError("UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN are required")
    
    try:
        # Используем upstash_redis - просто передаем URL и токен
        redis_client = Redis(
            url=rest_url,
            token=rest_token
        )
        
        print(f"✅ Connected to Upstash Redis")
        
        # Проверка подключения (опционально)
        await redis_client.ping()
        print("✅ Redis ping successful")
        
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        raise
    
    yield
    
    # upstash_redis не требует явного закрытия, но для чистоты оставим
    if redis_client:
        await redis_client.close()
        print("🔒 Redis connection closed")

app = FastAPI(
    title="Subscription API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# ============ КОНФИГУРАЦИЯ ============
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

# ============ ПУБЛИЧНЫЙ ЭНДПОИНТ ============
@app.get("/api/subscription/status")
async def get_subscription_status(
    username: str = Query(..., min_length=2, max_length=50)
):
    timestamp_str = await redis_client.get(username)
    
    if timestamp_str is None:
        return {
            "username": username,
            "status": "not_found",
            "is_active": False,
            "expires_at": None,
            "seconds_remaining": 0
        }
    
    try:
        expires_at = int(timestamp_str)
    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid subscription data")
    
    current_time = get_current_time()
    is_active = current_time < expires_at
    
    return {
        "username": username,
        "status": "active" if is_active else "expired",
        "is_active": is_active,
        "expires_at": expires_at,
        "expires_at_iso": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
        "seconds_remaining": expires_at - current_time if is_active else 0,
        "days_remaining": round((expires_at - current_time) / 86400, 1) if is_active else 0
    }

# ============ АДМИНСКИЕ ЭНДПОИНТЫ ============
@app.post("/api/subscription/admin/add")
async def add_subscription(
    username: str = Query(..., min_length=2, max_length=50),
    duration_days: int = Query(..., gt=0, le=3650),
    admin: str = Depends(verify_admin)
):
    current_time = get_current_time()
    new_expiry = current_time + (duration_days * 86400)
    await redis_client.set(username, str(new_expiry))
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
    timestamp_str = await redis_client.get(username)
    if timestamp_str is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    current_expiry = int(timestamp_str)
    current_time = get_current_time()
    base_time = max(current_expiry, current_time)
    new_expiry = base_time + (extra_days * 86400)
    await redis_client.set(username, str(new_expiry))
    
    return {
        "success": True,
        "username": username,
        "old_expires_at": current_expiry,
        "new_expires_at": new_expiry,
        "extended_by_days": extra_days
    }

@app.delete("/api/subscription/admin/revoke")
async def revoke_subscription(
    username: str = Query(..., min_length=2, max_length=50),
    admin: str = Depends(verify_admin)
):
    deleted = await redis_client.delete(username)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"success": True, "username": username, "action": "revoked"}

@app.get("/api/subscription/admin/list")
async def list_all_subscriptions(admin: str = Depends(verify_admin)):
    keys = await redis_client.keys("*")
    if not keys:
        return {"total": 0, "subscriptions": {}}
    
    # upstash_redis не поддерживает pipeline, поэтому обрабатываем последовательно
    result = {}
    current_time = get_current_time()
    
    for key in keys:
        try:
            timestamp_str = await redis_client.get(key)
            if timestamp_str:
                timestamp = int(timestamp_str)
                result[key] = {
                    "expires_at": timestamp,
                    "expires_at_iso": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
                    "is_active": timestamp > current_time,
                    "days_remaining": round((timestamp - current_time) / 86400, 1) if timestamp > current_time else 0
                }
        except (ValueError, TypeError):
            result[key] = {"error": "Invalid data format"}
    
    return {"total": len(result), "subscriptions": result}

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
        "redis": redis_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api")
async def api_root():
    return {
        "service": "Subscription API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "status": "/api/subscription/status?username={username}",
            "docs": "/api/docs"
        }
    }
