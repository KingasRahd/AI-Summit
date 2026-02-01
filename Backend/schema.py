from pydantic import BaseModel,Field
from typing import List,Optional,TypedDict,List,Dict
from uuid import UUID


class Project(BaseModel):
    
    name:str=Field(description='name of the project')
    features:List[str]=Field(description='Contains all the features of the project',examples=[['Reduces lantency by 5%','Handles multiple logins from different devices']])
    link:Optional[str]=Field(description='contains the live/drive link of the project',examples=['www.myapp/vercel.in'])

class Profile(BaseModel):
    uid:UUID=Field(description='this is the UID of the user provided in constraint')
    name:str=Field(description='Name of the user')
    education:str=Field(description='Course of user and college name',examples=['B.Tech,Computer Science Engineering,Indian Institute of Technology Bombay','B.Tech,Mechanical Engineering,Amity University'])
    experience:List[str]=Field(description='Work experience of the user like internships, placements, past jobs',examples=[['Intern at quill.ai from Aug,2021-Sep,2021','Worked at Microsoft as SDE from 2021-present']])
    skills:List[str]=Field(description='Contains all the skillset of the user like languages,frameworks,soft skills',examples=['Python,FastAPI,Docker,Kubernetes'])
    profile_links:List[str]=Field(description='contains all the social links of the user like Github,LinkedIn,etc')
    projects:List[Project]

class Constraint(BaseModel):

    uid:UUID=Field(
        description="Unique ID of the user"
    )
    authorized: bool = Field(
        description="Whether the student is legally authorized to work in the target country"
    )
    visa_required: bool = Field(
        description="Whether the student requires visa sponsorship now or in the future"
    )
    remote_ok: bool = Field(
        description="Whether the student is open to remote roles"
    )
    relocate: bool = Field(
        description="Whether the student is willing to relocate for a role"
    )
    industry_experience: int = Field(
        description="Years of full-time industry experience (0 for students)",
        ge=0
    )
    max_appl_per_day: int = Field(
        description="Maximum number of applications the agent can submit per day",
        gt=0
    )
    match_threshold: int = Field(
        description="Minimum job match score (0–100) required to apply",
        ge=0,
        le=100
    )
    blocked_companies: List[str] = Field(
        default_factory=list,
        description="List of companies the agent must never apply to"
    )
    blocked_roles: List[str] = Field(
        default_factory=list,
        description="List of role titles or keywords the agent must avoid"
    )

    class State(TypedDict):
        resume:str
        constraint:dict

class State(TypedDict):
    resume:str
    constraint:dict
    profile:dict
    user_store:str
    job_store:str
    uid:str
    ranked_jobs:List[Dict]
    file_path:str
    successful:str
    failure:str


class JobRequest(BaseModel):
    job_id: str