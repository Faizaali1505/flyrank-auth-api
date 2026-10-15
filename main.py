import os
from dotenv import load_dotenv
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Auth API")

print("Server running and connected to Supabase")


class AuthBody(BaseModel):
    email: str | None = None
    password: str | None = None


@app.post("/auth/signup", status_code=201, summary="Create a new account")
def signup(body: AuthBody):
    if not body.email or not body.password:
        return JSONResponse(status_code=400, content={"error": "Email and password are required"})
    try:
        result = supabase.auth.sign_up({"email": body.email, "password": body.password})
    except Exception as e:
        print("signup error:", e)
        return JSONResponse(status_code=400, content={"error": getattr(e, "message", str(e))})
    if result.user is None:
        return JSONResponse(status_code=400, content={"error": "Signup failed"})
    return {"user": result.user.model_dump(mode="json")}


@app.post("/auth/login", summary="Log in and get tokens")
def login(body: AuthBody):
    if not body.email or not body.password:
        return JSONResponse(status_code=400, content={"error": "Email and password are required"})
    try:
        result = supabase.auth.sign_in_with_password({"email": body.email, "password": body.password})
    except Exception as e:
        print("login error:", e)
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})
    if result.session is None:
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})
    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
    }
    

@app.get("/public/info", summary="Public info (no login needed)")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", summary="Private profile (login needed)")
def protected_profile(authorization: str | None = Header(default=None)):
    parts = (authorization or "").split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        return JSONResponse(status_code=401, content={"error": "Access token required"})

    token = parts[1]

    try:
        result = supabase.auth.get_user(token)
    except Exception as e:
        print("token verify error:", e)
        return JSONResponse(status_code=401, content={"error": "Invalid or expired token"})

    if result is None or result.user is None:
        return JSONResponse(status_code=401, content={"error": "Invalid or expired token"})

    user = result.user
    return {
        "id": user.id,
        "email": user.email,
        "created_at": str(user.created_at),
    }
    
    
    
 
    