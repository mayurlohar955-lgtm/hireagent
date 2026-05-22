


import os 
import json 
from openai import OpenAI
from pydantic import BaseModel
from typing import List


class CandidateEvaluation(BaseModel):
    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    justification: str


def evaluate_resume_against_jd(resume_text: str, job_criteria: str)->dict:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert technical screening assistant. Analyze the candidate's resume "
                    "against the provided Job Criteria. Calculate an objective match score from 0 to 100, "
                    "extract matched/missing skill arrays, and provide a 2-sentence justification."
                )            
            },
            {"role": "user", "content": f"JOB CRITERIA:\n {job_criteria}\nCANDIDATE RESUME:\n{resume_text}"}
        ],
        response_format=CandidateEvaluation
    )
    return json.loads(response.choices[0].message.parsed)