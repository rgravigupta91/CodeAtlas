from pydantic import BaseModel, Field
from typing import List, Optional
from llama_index.core.program import LLMTextCompletionProgram
from dotenv import load_dotenv

load_dotenv()

class Song(BaseModel):
    title: str
    length_seconds: int

class Album(BaseModel):
    name: str
    artist: str
    songs: List[Song]

class JiraEpic(BaseModel): 
    actors: str # = Optional[Field(description='person or system that interacts with the product or feature described in the story')]
    Components: List[str] #= Optional[Field(description='a subsection or part of a project that helps you organize and group')]

epic = """Epic Name:
User Authentication System

Epic Summary:
As a user, I want to securely sign up, sign in, and manage my session so that I can access protected features of the application.

Actors:
End User – registers, logs in/out, resets password.

System Admin – manages user accounts, roles.

Authentication Service – handles token issuance and validation.

Components:
Frontend (React) – login/signup forms, error handling.

Backend API (FastAPI/Django) – auth endpoints (/login, /signup, /logout, /refresh).

Database (PostgreSQL) – users table, session tokens.

Email Service – sends verification and password reset emails.

Security Layer – JWT, password hashing (bcrypt), rate limiting.

Acceptance Criteria:
Users can register with email/password.

Users receive verification email after registration.

Users can log in with valid credentials.

Authenticated users receive a valid JWT.

Tokens expire after N minutes, with refresh support.

Users can reset passwords via email.

Rate-limiting and lockout after N failed attempts.

Linked User Stories:
AUTH-101: User Registration Form

AUTH-102: Email Verification

AUTH-103: Login Functionality

AUTH-104: JWT Token Handling

AUTH-105: Password Reset Flow

AUTH-106: Admin User Management Panel"""

program = LLMTextCompletionProgram.from_defaults(
    output_cls=JiraEpic,
    prompt_template_str="""
Find the Actors and Components in the Jira Epic Story described below:
"{jira_epic}" """,
    verbose=True,
)
output = program(jira_epic=epic)
print(output)