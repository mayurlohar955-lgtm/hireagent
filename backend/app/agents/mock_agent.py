


import random

async def generate_job_description(
    title, department, experience_min, experience_max,
    skills, location, employment_type,
    salary_min=None, salary_max=None, additional_context=None
):
    skills_str = ", ".join(skills[:3]) if skills else "relevant technologies"
    all_skills = ", ".join(skills) if skills else "relevant technologies"
    first_skill = skills[0] if skills else "relevant technologies"

    return {
        "description": (
            f"## {title} - {department}\n\n"
            f"**Location:** {location} | **Type:** {employment_type}\n\n"
            f"### About the Role\n"
            f"We are looking for a talented {title} to join our {department} team. "
            f"You will own key parts of our product and have real impact from day one.\n\n"
            f"### What You Will Do\n"
            f"- Build scalable systems using {skills_str}\n"
            f"- Collaborate with product and design to ship high-quality features\n"
            f"- Participate in architecture decisions and code reviews\n"
            f"- Mentor junior engineers and raise the engineering bar\n\n"
            f"### Requirements\n"
            f"- {experience_min}-{experience_max} years of relevant experience\n"
            f"- Strong proficiency in {all_skills}\n"
            f"- Track record of shipping production systems\n"
            f"- Clear written and verbal communication"
        ),
        "requirements": [
            f"{experience_min}-{experience_max} years experience",
            f"Proficiency in {first_skill}",
            "Experience with production systems",
            "Strong problem-solving skills",
        ],
        "skills_required": skills,
        "what_you_will_do": [
            "Build scalable APIs and backend services",
            "Contribute to system architecture",
            "Participate in code reviews",
        ],
        "what_we_offer": [
            "Competitive salary",
            "Flexible remote work",
            "Health insurance",
            "Learning budget Rs.50,000/year",
        ],
        "bias_flags": [],
    }


async def parse_resume(resume_text: str) -> dict:
    return {
        "name": "Demo Candidate",
        "email": "candidate@example.com",
        "phone": "+91 98765 43210",
        "location": "Pune, India",
        "experience_years": round(random.uniform(2, 8), 1),
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
        "education": [
            {
                "degree": "B.Tech",
                "field": "Computer Science",
                "institution": "COEP Pune",
                "year": 2020,
            }
        ],
        "previous_roles": [
            {
                "title": "Backend Engineer",
                "company": "TCS",
                "duration_months": 24,
                "description": "Built REST APIs and microservices",
            }
        ],
        "certifications": [],
        "languages": ["English", "Hindi", "Marathi"],
        "summary": "Experienced backend engineer with strong Python skills.",
    }


async def score_candidate(
    parsed_candidate, job_title, job_description,
    skills_required, experience_min, experience_max
) -> dict:
    skills_score     = round(random.uniform(55, 95), 1)
    experience_score = round(random.uniform(55, 95), 1)
    relevance_score  = round(random.uniform(55, 95), 1)
    total = round(
        skills_score * 0.4 + experience_score * 0.3 + relevance_score * 0.3, 1
    )
    first_skill = skills_required[0] if skills_required else "Python"

    return {
        "skills_score":     skills_score,
        "experience_score": experience_score,
        "relevance_score":  relevance_score,
        "total_score":      total,
        "strengths": [
            f"Strong {first_skill} skills",
            "Relevant industry experience",
        ],
        "gaps": ["Could improve cloud infrastructure knowledge"],
        "reasoning": (
            f"Good overall fit for {job_title}. "
            f"Skills align well with requirements."
        ),
        "recommendation": "yes" if total >= 70 else "maybe",
    }


async def screen_resume_from_bytes(
    pdf_bytes, job_title, job_description,
    skills_required, experience_min, experience_max
) -> dict:
    from app.agents.screening_agent import extract_text_from_pdf

    resume_text = extract_text_from_pdf(pdf_bytes)
    parsed      = await parse_resume(resume_text)
    scores      = await score_candidate(
        parsed, job_title, job_description,
        skills_required, experience_min, experience_max
    )
    return {
        "resume_text":      resume_text,
        "parsed_data":      parsed,
        "scores":           scores,
        "name":             parsed["name"],
        "email":            parsed["email"],
        "phone":            parsed["phone"],
        "location":         parsed["location"],
        "skills":           parsed["skills"],
        "experience_years": parsed["experience_years"],
        "education":        parsed["education"],
        "previous_roles":   parsed["previous_roles"],
    }