from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi import HTTPException, FastAPI, Depends, Request, Form, Query
from fastapi.responses import RedirectResponse
import requests
import os, json, uuid
from dotenv import load_dotenv
from database.embed import Agent

from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Database setup
DATABASE_URL = "sqlite:///./sessions.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SessionModel(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    data = Column(String)

Base.metadata.create_all(bind=engine)

# Custom session middleware
class CustomSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("session_id")
        
        # Create a new session if one doesn't exist
        if not session_id:
            session_id = str(uuid.uuid4())
            request.state.session = {}
            request.state.new_session = True
        else:
            # Load existing session from database
            db = SessionLocal()
            try:
                db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
                if db_session:
                    request.state.session = json.loads(db_session.data)
                else:
                    request.state.session = {}
                    request.state.new_session = True
            finally:
                db.close()
        
        # Process the request
        response = await call_next(request)
        
        # Save session to database
        db = SessionLocal()
        try:
            session_data = json.dumps(request.state.session)
            db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if db_session:
                db_session.data = session_data
            else:
                db_session = SessionModel(id=session_id, data=session_data)
                db.add(db_session)
            db.commit()
        finally:
            db.close()
        
        # Set session cookie if it's a new session
        if getattr(request.state, "new_session", False):
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                max_age=3600,
                samesite="lax"
            )
        
        return response

app.add_middleware(CustomSessionMiddleware)


# URLs
load_dotenv()
REDIRECT_URI = 'https://linkedout-a6rv.onrender.com/callback'
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
PROFILE_URL = 'https://api.linkedin.com/v2/userinfo'
EMAIL_URL = 'https://api.linkedin.com/v2/emailAddress'



# Routes(urls) and Methods
@app.get('/')
def home(request:Request):
    return templates.TemplateResponse('new.html', {"request": request})


@app.get('/login')
def login():
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20profile%20email%20w_member_social"
    )
    return RedirectResponse(url=auth_url)

@app.get('/logout')
def logout(request:Request):
    request.state.session.clear()
    response = RedirectResponse(url='/')
    for c in request.cookies:
        response.delete_cookie(c)
    response.delete_cookie("session")
    return response


@app.get('/callback', response_class=HTMLResponse)
async def callback(request:Request):
    try:
        code = request.query_params.get('code')
        if not code:
            raise HTTPException(status_code=400, detail="Authorization failed")
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        token_response = requests.post(TOKEN_URL, data=token_data)
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Error getting access token")

        token_json = token_response.json()
        access_token = token_json.get('access_token')
        if not access_token:
            raise HTTPException(status_code=400, detail="Error getting access token")
        
        # Storing the access token in the session
        request.state.session['access_token'] = access_token

        profile_response = requests.get(PROFILE_URL, headers={
            'Authorization': f'Bearer {access_token}',
            'X-Restli-Protocol-Version': '2.0.0',
        })

        profile_data = profile_response.json()
        request.state.session['profile_data'] = profile_data

        return templates.TemplateResponse('new.html', {"request": request, "user_details": profile_data})
    
    except Exception as e:
        return f"Exception : {e}"



class PostData(BaseModel):
    domain: str
    value: str

@app.post('/post')
async def post_on_linkedin(request: Request, data : PostData):
    try:
        profile_data = request.state.session.get('profile_data')
        access_token = request.state.session.get('access_token')

        if not access_token or not profile_data:
            raise HTTPException(status_code=400, detail="Invalid session data")
        agent = Agent(data)
        result = agent.execute()
        if result is None:
            return "Error in 'execute()' function"
        post_url = "https://api.linkedin.com/v2/ugcPosts"
        post_data = {
            "author": f"urn:li:person:{profile_data['sub']}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": result,
                    },
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        post_response = requests.post(post_url, headers={
                'Authorization': f'Bearer {access_token}',
                'X-Restli-Protocol-Version': '2.0.0',},
                json=post_data)
        
        if post_response.status_code == 201:
            return True
        else:
            raise HTTPException(status_code=post_response.status_code, detail=post_response.text)

    except Exception as e:
        print(f"Exception in /post : {str(e)}")
        return f"Exception in /post : {str(e)}"



@app.post('/receive_topic')
async def topic(request: Request, data: str=Form(...)):
    topic = data.get('value')
    agent = Agent(topic)
    result = agent.execute()
    profile_data = request.state.session['profile_data']
    return templates.TemplateResponse('greet.html', {"request":request,"user_details":profile_data ,"message":result})



