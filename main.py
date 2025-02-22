from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi import HTTPException, FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime
import requests
from starlette.middleware.sessions import SessionMiddleware


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="secret_lang")

DATABASE_URL = 'sqlite:///database/test.db'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Session table
class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    data = Column(String, nullable=False)
    last_accessed = Column(DateTime, default=datetime.now())

# Data Structure
class SessionData(BaseModel):
    access_token: str
    profile_data: dict

# Creating the database table
Base.metadata.create_all(bind=engine)

# Helper function to create a session in the database
def create_session(db_session, data: str):
    session_id = str(uuid.uuid4())
    db_session.add(Session(id=session_id, data=data))
    db_session.commit()
    return session_id

# Helper function to get session data from the database
def get_session(db_session, session_id: str):
    return db_session.query(Session).filter(Session.id == session_id).first()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# URLs
REDIRECT_URI = 'http://localhost:8000/callback'
CLIENT_ID = '86jz9u3cqsznsq'
CLIENT_SECRET = 'WPL_AP1.tEJ51YCsRJRxkjFh.AE2FYQ=='
AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
PROFILE_URL = 'https://api.linkedin.com/v2/userinfo'
EMAIL_URL = 'https://api.linkedin.com/v2/emailAddress'


# Routes and Methods
@app.get('/')
def login():
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20profile%20email%20w_member_social"
    )
    return RedirectResponse(url=auth_url)


@app.get('/callback', response_class=HTMLResponse)
def callback(request:Request, db: Session = Depends(get_db)):
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
        request.session['access_token'] = access_token

        profile_response = requests.get(PROFILE_URL, headers={
            'Authorization': f'Bearer {access_token}',
            'X-Restli-Protocol-Version': '2.0.0',
        })

        profile_data = profile_response.json()

        # Storing the data of the user in the session
        request.session['profile_data'] = profile_data

        session_data = SessionData(access_token=access_token, profile_data=profile_data)
        session_id = create_session(db, str(session_data.model_dump()))

        # Storing the session id in the cookie (as a session identifier)
        request.session['session_id'] = session_id
        return f"Welcome {profile_data['given_name']}!!"
    
    except Exception as e:
        return f"Exception : {e}"


@app.get('/post')
async def post_on_linkedin(request: Request, db: Session = Depends(get_db)):
    try:
        session_id = request.session.get('session_id')
        if not session_id:
            raise HTTPException(status_code=400, detail="No session found")
        
        session_data = get_session(db, session_id)
        if not session_data:
            raise HTTPException(status_code=400, detail="Session not found")
        
        session_data_dict = eval(session_data.data)

        access_token = session_data_dict.get('access_token')
        profile_data = session_data_dict.get('profile_data')

        if not access_token or not profile_data:
            raise HTTPException(status_code=400, detail="Invalid session data")

        post_url = "https://api.linkedin.com/v2/ugcPosts"
        post_data = {
            "author": f"urn:li:person:{profile_data['sub']}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": "Testing Phase - I"
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
            return {"message": "Post created successfully."}
        else:
            raise HTTPException(status_code=post_response.status_code, detail=post_response.text)

    except Exception as e:
        return f"Exception in /post : {str(e)}"



# query = "Who is Sid?"
# agent = Agent(query)
# result = agent.execute()
# print(result)


