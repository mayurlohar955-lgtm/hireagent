


import anthropic
import json
import re
from typing import Optional

def _get_client():
    return anthropic.Anthropic()

BIAS_PATTERNS = [
    r"\b(rockstar|ninja|guru|wizard|he/she|manpower|mankind)\b",
    r"\b(young|energetic team|digital native|recent graduate only)\b"
    r"\b(culture fit|beer|ping.?pong|fraternity)\b"
    r"\b(ivy league|top.?tier university)\b"
]

def detect_bias(text: str)->list[str]:
    flags = []
    text_lower = text.lower()
    for pattern in BIAS_PATTERNS:
        matches = re.findall(pattern, text_lower)
        flags.extend(matches)
    return list(set(flags))

async def generate_job_description(
        title: str,
        department: str,
        experience_min: int,
        experience_max: int,
        skills: list[str],
        location: str,
        employment_type:str,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        additional_context: Optional[str] = None,
)->dict:
    
    salary_info = ""
    if salary_min and salary_max:
        salary_info = f"Salary range: {salary_min:,} - {salary_max:,} per annum"

    prompt = f"""You are an expert HR professional writing an inclusive, compelling job description.

Generate a complete job description for:
- Title: {title}
- Department: {department}
- Location: {location}
- Employment type: {employment_type}
- Experience required: {experience_min} - {experience_max} years
- Key skills: {', '.join(skills)}

{salary_info}
{f'Additional context: {additional_context}' if additional_context else ''}

Rules:
1. Use inclusive, gender-neutral language
2. Focus on what the candidate will DO and ACHIEVE, not just requirements
3. Be specific about impact, not vague about "passion or "culture fit"
4. List only truly required skills as requirement - not a wish list
5. Keep requirements realistic for the experience level started

Return ONLY valid JSON in this exact structure, nothing else:
{{
  "description": "Full multi-paragraph job description in markdown",
  "requirements": ["Requirement 1", "Requirement 2", ...],
  "skills_required": ["Skill 1", "Skill 2", ...],
  "what_you_will_do": ["Responsibility 1", "Responsibility 2", ...],
  "what_we_offer": ["Benefit 1", "Benefit 2", ...]
}}"""
    
    response = _get_client().messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    result = json.loads(raw)

    # Run bias detection on the generated description
    full_text = result["description"] + " " + " ".join(result.get("requirements", []))
    result["bias_flags"] = detect_bias(full_text)

    return result


async def improve_job_description(existing_jd: str) -> dict:
    """
    Take an existing JD and rewrite it to be more inclusive and compelling.
    Returns: { improved_description, changes_made, bias_flags }
    """

    prompt = f"""You are an expert HR consultant improving a job description.

Existing JD:
{existing_jd}

Rewrite this job description to:
1. Remove any biased or exclusionary language
2. Make requirements more realistic and inclusive
3. Focus on outcomes over credentials
4. Use gender-neutral language throughout
5. Make it compelling — explain WHY someone would want this role

Return ONLY valid JSON:
{{
  "improved_description": "Improved full JD in markdown",
  "changes_made": ["Change 1 explanation", "Change 2 explanation", ...],
  "bias_flags": ["Any remaining concerns..."]
}}"""

    response = _get_client().messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)






