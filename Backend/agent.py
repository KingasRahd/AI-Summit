from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph,START,END
import os
from schema import State,Profile
from langchain_core.messages import SystemMessage,AIMessage,HumanMessage,BaseMessage
from prompts import artifact_prompt
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.store.postgres import PostgresStore
from langgraph.store.memory import InMemoryStore
import requests
import httpx

#DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
#store = PostgresStore.from_conn_string(DB_URI)
#store.setup()
load_dotenv()
key=os.getenv('GOOGLE_API_KEY3')
model=ChatGoogleGenerativeAI(model='gemini-2.5-flash',api_key=key)
structured_llm=model.with_structured_output(Profile)
os.environ['HF_HOME']='D:/huggingface_cache'
embeddor=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

user_store=InMemoryStore()
job_store=InMemoryStore(index={'embed':embeddor,'dims':800})

def artifact(state:State):
    
    response=structured_llm.invoke(
        [
            SystemMessage(content=artifact_prompt),
            HumanMessage(content=f"Resume : {state['resume']} \nUID: {state['constraint']['uid']}")
        ]
    )

    user_store.put(
        namespace=('data',str(response.uid)),
        key='profile',
        value=response.model_dump()
    )

    # skills=", ".join([i for i in response.skills])
    # projects="\n".join(['\n'.join(j for j in i.features) for i in response.projects])
    # embeddings=embeddor.embed_documents([skills,projects])
    
    # user_store.put(
    #     namespace=('data',str(response.uid)),
    #     key='embeddings',
    #     value={'embeddings':embeddings}
    # )

    user_store.put(
        namespace=('data',str(response.uid)),
        key='constraint',
        value={'constraint':state['constraint']}
    )

    user_store.put(
        namespace=('data',str(response.uid)),
        key='success',
        value={}
    )

    user_store.put(
        namespace=('data',str(response.uid)),
        key='failure',
        value={}
    )

    return {'profile':response.model_dump(),'user_store':user_store,'job_store':job_store,'uid':str(response.uid)}

    

def ranker(state:State):
    url = f"http://127.0.0.1:8001/get_jobs"

    user_store=state['user_store']
    job_store=state['job_store']
    uid=state['uid']
    jobs = requests.get(url).json()
    skills=', '.join(user_store.get(('data',uid),key='profile').value['skills'])
    experience=', '.join(user_store.get(('data',uid),key='profile').value['experience'])
    if experience=='':
        experience='Fresher at work'
    projects='\n'.join('\n'.join(i['features']) for i in user_store.get(('data',uid),key='profile').value['projects'])

    success_item = user_store.get(('data', uid), key='success')
    success_jobs = success_item.value if success_item else {}

    for job in jobs:
        if job['job_id'] not in success_jobs:

            job_store.put(
                namespace=('jobs',uid,'profile'),
                key=job['job_id'],
                value={'data':job}
                )

            job_store.put(
                namespace=('jobs',uid,'requirement'),
                key=job['job_id'],
                value={'data':job['requirements']}
                )
            
            job_store.put(
                namespace=('jobs',uid,'responsibility'),
                key=job['job_id'],
                value={'data':job['responsibilities']}
                )
            try:
                job_store.put(
                    namespace=('jobs',uid,'qualification'),
                    key=job['job_id'],
                    value={'data':job['preferred_qualification']}
                    )
            except:
                job_store.put(
                    namespace=('jobs',uid,'qualification'),
                    key=job['job_id'],
                    value={'data':"Open to all"}
                    )
        else:pass

    skill_score={i.key:i.score for i in job_store.search(
        ('jobs',uid,'requirement'),
        query=skills
    )}

    resp_score={i.key:i.score for i in job_store.search(
        ('jobs',uid,'responsibility'),
        query=projects
    )}

    qual_score={i.key:i.score for i in job_store.search(
        ('jobs',uid,'qualification'),
        query=experience
    )}

    score=[
        {i:0.6*skill_score[i]+0.25*resp_score[i]+0.15*qual_score[i]} for i in skill_score
    ]

    print(skill_score)
    print(resp_score)
    print(qual_score)
    print(score)

    sorted_jobs = sorted(
    score,
    key=lambda x: list(x.values())[0],
    reverse=True
)
    print(sorted_jobs)
    return {'ranked_jobs':sorted_jobs}




def modifier(state:State):
    pass

async def executor(state:State):
    fl={}
    s={}
    uid=state['uid']
    print('in executor')

    if 'ranked_jobs' not in state:
        raise ValueError("ranked_jobs missing from state")

    jobs=state['ranked_jobs']
    url = "http://127.0.0.1:8001/apply"
    async with httpx.AsyncClient(timeout=30) as client:
        for job in jobs:
            with open(state['file_path'], "rb") as f:
                files = {
                    "file": ("resume.pdf", f, "application/pdf")
                }
                data = {
                    "job_id": list(job.keys())[0]
                }

                response = await client.post(
                    url,
                    files=files,
                    data=data
                )

            result=response.json()
            if result['status']=='success':
                job_profile=job_store.get(('jobs',uid,'profile'),result['job_id']).value['data']

                s[result['job_id']]=job_profile

                user_store.put(
        namespace=('data',uid),
        key='success',
        value=s
        )
            else:
        
                job_profile=job_store.get(('jobs',uid,'profile'),result['job_id']).value['data']

                fl[result['job_id']]=job_profile

                user_store.put(
        namespace=('data',uid),
        key='failure',
        value=fl
        )
            print(response.json())

            successful=user_store.get(('data',uid),'success').value
            failure=user_store.get(('data',uid),'failure').value

    return {'successful':successful,'failure':failure}




graph=StateGraph(State)

graph.add_node('artifact',artifact)
graph.add_node('ranker',ranker)
graph.add_node('executor',executor)

graph.add_edge(START,'artifact')
graph.add_edge('artifact','ranker')
graph.add_edge('ranker','executor')
graph.add_edge('executor',END)

workflow=graph.compile()





