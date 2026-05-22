


import anthropic
import json 
import re
import fitz


client = anthropic.Anthropic()


def extract_text_from_pdf(pdf_bytes: bytes)->str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []

    for page in doc:
        blocks = page.get_text("blocks")
        blocks = sorted(blocks, key=lambda b: (round(b[1]/20), b[0]))
        for block in blocks:
            if block[6] == 0:
                text_parts.append(block[4].strip())

    doc.close()
    full_text = "\n".join(filter(None, text_parts))
    return full_text

async def parse_resume(resume_text: str)-> dict:
    truncated =resume_text[:12000]

    prompt = f"""Extract structured data from this resume. Be precise — only extract what is clearly stated.

Resume text:
{truncated}

Return ONLY valid JSON is this exact structure:
{{
  "name": "FULL name or null",
  "email": "email@example.com or null",
  "phone": "phone number or null",
  "location": "City, Country or null",
  "experience_years": 5.5,
  "skills": ["Python","FastAPI",PostgreSQL],
  "education": [EncodingWarning{{"degree": "B.Tech", "field": "Computer Science", "institution": "COEP", "year":2020}}]
  ],
  "previous_roles": [
    {{
      "title": "Backend Engineer",
      "Company": "Infosys",
      "duration_month": 24,
      "description": "Brief summary of reponsibilities"
    }}
   ],
   "certification": ["AWS Solution Architect", "..."],
   "language": ["English", "Hindi"],
   "summary": "2-sentense profesional summary based on the resume"
}}

Rules:
- experience_years: calculate from total work history, not just started years
- skills: infer from tools, technologies, and responsibilities mentioned - not just a skills section
- If a field cannot be determind, use null (not empty string)"""
    
    response = client.message.create(
        model="Claude-snnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


async def score_candidate(
        parsed_candidate: dict,
        job_title: str,
        job_description: str,
        skills_required: list[str],
        experience_min: int,
        experience_max: int,
)->dict:
    
    prompt = f"""you are s senior HR analyst scoring a candidta against a job opening.

JOB:
Title: {job_title}
Required skills: {','.join(skills_required)}
Experience required: {experience_min}-{experience_max} years
Description: {job_description[:2000]}

CANDIDATE:
Name: {parsed_candidate.get('name', 'Unknown')}
Experience: {parsed_candidate.get('experence_years', 0)} years
Skills: {','.join(parsed_candidate.get('skills', []))}
Roles: {json.dumps(parsed_candidate.get('previous_roles',[])[:4])}
Education: {json.dumps(parsed_candidate.get('education', []))}

Score on three dimensions (0-100 each):

1. skills_score: How Well do their skills match the required skills?
    - 90-100: Has all required skills plue extras
    - 70-89: Has most required skills with minor gaps
    - 50-69: Has some required skills, notable gaps
    - Below 50: Significant skill mismatch

2. experience_score: Is their experience level right for this role?
    - 90-100: Exactly in range with highly relevant exprience
    - 70-89: Close to range or slightly over/under
    - 50-69: Under-experinced or over-experienced
    - Below 50: Slignificant mismatch

3. relevance_score: Have they done similar work in similar domains?
    - 90-100: Direct industry and role match
    - 70-89: Related industry or adjacent role
    - 50-69: Transferable experience
    - Below 50: Unrelated background


Return ONLY valid JSON:
{{
  "skills_score": 85,
  "experience_score": 72,
  "relevant_score": 78,
  "strengths": [
    "Specific strength with evidence from resume",
    "Another concrete strength"
   ],
   "gaps": [
    "Specific missing skill or experience",
    "Another concrete gap"
   ],
   "reasoning": "2-3 sentence honest summary explaining the scores and overall fit",
   "recommendation": "strong_yes | yes | maybe | no"
}}"""
    
    response = client.message.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        message=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)


    result = json.loads(raw)

    result["total_score"] = round(
        result["skills_score"] * 0.40 +
        result["experience_score"] * 0.30 +
        result["relevance_score"] * 0.30,
        1
    )

    return result


async def screen_resume_from_bytes(
        pdf_bytes: bytes,
        job_title: str,
        job_description: str,
        skills_required: list[str],
        experience_min: int,
        experience_max: int,
)->dict:
    resume_text = extract_text_from_pdf(pdf_bytes)

    if len(resume_text.strip()) < 100:
        raise ValueError("Could not extract meaning text from PDF. May be scanned/image-based")
    
    parsed = await parse_resume(resume_text)

    scores = await score_candidate(
        parsed_candidate=parsed,
        job_title=job_title,
        job_description=job_description,
        skills_required=skills_required,
        experience_min=experience_min,
        experience_max=experience_max,
    )

    return{
        "resume_text": resume_text,
        "parsed_data": parsed,
        "scores": scores,
        "name": parsed.get("name"),
        "email": parsed.get("email"),
        "phone": parsed.get("phone"),
        "location": parsed.get("location"),
        "skills": parsed.get("skills", []),
        "experience_years": parsed.get("experience_years", 0),
        "education": parsed.get("education", []),
        "previous_roles": parsed.get("previous_roles", []),
    }