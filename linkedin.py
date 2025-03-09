from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import HTTPException, FastAPI, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uuid
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from database.embed import Agent


load_dotenv()

Base = declarative_base()
class SessionData(Base):
    __tablename__ = "session_data"

    id = Column(String, primary_key=True, index=True)
    access_token = Column(String, nullable=False)
    profile_data = Column(JSON, nullable=False)

    def __init__(self, access_token: str, profile_data: dict):
        self.access_token = access_token
        self.profile_data = profile_data



class LinkedInAutoPostApp:
    def __init__(self):
        self.app = FastAPI()
        self.app.add_middleware(SessionMiddleware, secret_key="secret_lang")
        self.templates = Jinja2Templates(directory="templates")
        self.database_url = 'sqlite:///database/test.db'
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()

        # Environment variables for LinkedIn OAuth
        self.REDIRECT_URI = 'http://localhost:8000/callback'
        self.CLIENT_ID = os.getenv('CLIENT_ID')
        self.CLIENT_SECRET = os.getenv('CLIENT_SECRET')
        self.AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
        self.TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
        self.PROFILE_URL = 'https://api.linkedin.com/v2/userinfo'
        self.EMAIL_URL = 'https://api.linkedin.com/v2/emailAddress'

        self._create_database_tables()
        self._add_routes()

    def _create_database_tables(self):
        # Session table
        class Session(self.Base):
            __tablename__ = "sessions"
            id = Column(String, primary_key=True, index=True)
            data = Column(String, nullable=False)
            last_accessed = Column(DateTime, default=datetime.now())

        self.Session = Session
        self.Base.metadata.create_all(bind=self.engine)

    def _add_routes(self):
        self.app.get('/')(self.login)
        self.app.get('/callback', response_class=HTMLResponse)(self.callback)
        self.app.get('/post')(self.post_on_linkedin)
        self.app.post('/receive_topic')(self.topic)

    # Helper functions
    def create_session(self, db_session, data: str):
        session_id = str(uuid.uuid4())
        db_session.add(self.Session(id=session_id, data=data))
        db_session.commit()
        return session_id

    def get_session(self, db_session, session_id: str):
        return db_session.query(self.Session).filter(self.Session.id == session_id).first()

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Routes and Methods
    async def login(self):
        auth_url = (
            f"https://www.linkedin.com/oauth/v2/authorization?"
            f"response_type=code"
            f"&client_id={self.CLIENT_ID}"
            f"&redirect_uri={self.REDIRECT_URI}"
            f"&scope=openid%20profile%20email%20w_member_social"
        )
        return RedirectResponse(url=auth_url)

    async def callback(self, request: Request, db: Session = Depends(get_db)):
        try:
            code = request.query_params.get('code')
            if not code:
                raise HTTPException(status_code=400, detail="Authorization failed")
            
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.REDIRECT_URI,
                'client_id': self.CLIENT_ID,
                'client_secret': self.CLIENT_SECRET
            }
            token_response = requests.post(self.TOKEN_URL, data=token_data)
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Error getting access token")

            token_json = token_response.json()
            access_token = token_json.get('access_token')
            if not access_token:
                raise HTTPException(status_code=400, detail="Error getting access token")
            
            request.session['access_token'] = access_token

            profile_response = requests.get(self.PROFILE_URL, headers={
                'Authorization': f'Bearer {access_token}',
                'X-Restli-Protocol-Version': '2.0.0',
            })

            profile_data = profile_response.json()

            # Storing the data of the user in the session
            request.session['profile_data'] = profile_data

            session_data = SessionData(access_token=access_token, profile_data=profile_data)
            session_id = self.create_session(db, str(session_data.model_dump()))

            # Storing the session id in the cookie (as a session identifier)
            request.session['session_id'] = session_id
            return self.templates.TemplateResponse('greet.html', {"request": request, "user_details": profile_data, "message": None})

        except Exception as e:
            return f"Exception : {e}"

    async def post_on_linkedin(self, request: Request, db: Session = Depends(get_db)):
        try:
            session_id = request.session.get('session_id')
            if not session_id:
                raise HTTPException(status_code=400, detail="No session found")
            
            session_data = self.get_session(db, session_id)
            if not session_data:
                raise HTTPException(status_code=400, detail="Session not found")
            
            session_data_dict = eval(session_data.data)

            access_token = session_data_dict.get('access_token')
            profile_data = session_data_dict.get('profile_data')

            if not access_token or not profile_data:
                raise HTTPException(status_code=400, detail="Invalid session data")

            topic = "Will AI replace humans?"
            agent = Agent(topic)
            result = agent.execute()
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
                'X-Restli-Protocol-Version': '2.0.0',
            }, json=post_data)

            if post_response.status_code == 201:
                return {"message": "Post created successfully."}
            else:
                raise HTTPException(status_code=post_response.status_code, detail=post_response.text)

        except Exception as e:
            return f"Exception in /post : {str(e)}"

    async def topic(self, request: Request, topic: str = Form(...)):
        agent = Agent(topic)
        result = agent.execute()
        return self.templates.TemplateResponse('greet.html', {"request": request, "user_details": None, "message": result})


# Initialize the app
linkedin_app = LinkedInAutoPostApp()
app = linkedin_app.app