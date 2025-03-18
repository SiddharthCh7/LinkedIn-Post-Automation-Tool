from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi import HTTPException, FastAPI, Depends, Request, Form, Query
from fastapi.responses import RedirectResponse
import requests
import os
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from database.embed import Agent

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="secret_lang2")


# URLs
load_dotenv()
REDIRECT_URI = 'https://linkedout-a6rv.onrender.com/callback'
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
PROFILE_URL = 'https://api.linkedin.com/v2/userinfo'
EMAIL_URL = 'https://api.linkedin.com/v2/emailAddress'



# Routes and Methods
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
    request.session.clear()
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
        request.session['access_token'] = access_token

        profile_response = requests.get(PROFILE_URL, headers={
            'Authorization': f'Bearer {access_token}',
            'X-Restli-Protocol-Version': '2.0.0',
        })

        profile_data = profile_response.json()
        request.session['profile_data'] = profile_data

        return templates.TemplateResponse('new.html', {"request": request, "user_details": profile_data})
    
    except Exception as e:
        return f"Exception : {e}"



class PostData(BaseModel):
    domain: str
    value: str

@app.post('/post')
async def post_on_linkedin(request: Request, data : PostData):
    try:
        profile_data = request.session.get('profile_data')
        access_token = request.session.get('access_token')

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
    profile_data = request.session['profile_data']
    return templates.TemplateResponse('greet.html', {"request":request,"user_details":profile_data ,"message":result})



