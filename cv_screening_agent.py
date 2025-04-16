# === Automated CV Screening and Feedback AI Agent ===
# Step 1: Resume Extraction from Email

import imaplib
import email
import os
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import PyPDF2
import docx2txt
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables from .env
load_dotenv()

# Load credentials
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("APP_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
RESUME_FOLDER = "resumes"

# Ensure required variables are present
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set. Check your .env file.")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Create resumes folder if it doesn't exist
os.makedirs(RESUME_FOLDER, exist_ok=True)

def mask_pii(text):
    """Mask personal identifiable information in the text."""
    # Mask email addresses
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL]', text)
    
    # Mask names (assuming names are in Title Case and 2-3 words)
    text = re.sub(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})', '[NAME]', text)
    
    return text

def extract_batch_year(text):
    """Extract batch year from resume text."""
    # Look for patterns like "Batch of 2020" or "Graduated 2020"
    batch_patterns = [
        r'Batch\s+of\s+(\d{4})',
        r'Graduated\s+(\d{4})',
        r'Class\s+of\s+(\d{4})',
        r'(\d{4})\s+Batch'
    ]
    
    for pattern in batch_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return "Not found"

def extract_ai_experience(text):
    """Extract AI-related experience from resume text."""
    ai_keywords = [
        'machine learning', 'deep learning', 'artificial intelligence',
        'neural networks', 'nlp', 'computer vision', 'tensorflow',
        'pytorch', 'scikit-learn', 'data science', 'ml', 'ai'
    ]
    
    experience = []
    lines = text.split('\n')
    for line in lines:
        if any(keyword in line.lower() for keyword in ai_keywords):
            experience.append(line.strip())
    
    return experience

def fetch_resumes():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    typ, data = mail.search(None, 'UNSEEN')
    for num in data[0].split():
        typ, msg_data = mail.fetch(num, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()
            if filename and (filename.endswith(".pdf") or filename.endswith(".docx")):
                filepath = os.path.join(RESUME_FOLDER, filename)
                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))
                print(f"Saved resume: {filename}")


# Step 2: Resume Parsing and Scoring

def extract_text(filepath):
    if filepath.endswith(".pdf"):
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif filepath.endswith(".docx"):
        return docx2txt.process(filepath)
    return ""


def score_resume(resume_text, job_description):
    """Enhanced resume scoring with detailed criteria."""
    prompt = f"""
Analyze the following resume against the job description and provide a detailed evaluation.

[Job Description]
{job_description}

[Resume]
{resume_text}

Return a JSON response with the following structure:
{{
    "overall_score": <0-100>,
    "component_scores": {{
        "work_experience": <0-100>,
        "education": <0-100>,
        "skills": <0-100>,
        "formatting": <0-100>
    }},
    "jd_match_score": <0-100>,
    "strengths": [list of strengths],
    "weaknesses": [list of weaknesses],
    "suggestions": [list of suggestions],
    "relevant_keywords_found": [list of matching keywords],
    "missing_keywords": [list of missing important keywords]
}}

Focus on evaluating:
1. Work experience relevance and quality
2. Education alignment with requirements
3. Technical skills match
4. Formatting and clarity
5. Keyword matches with job description
"""
    
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return eval(response.choices[0].message.content)


# Step 3: Email Feedback to Candidate

def send_feedback_email(to_email, feedback, batch_year, ai_experience):
    """Enhanced email template with more detailed feedback."""
    message = MIMEMultipart()
    message['From'] = EMAIL
    message['To'] = to_email
    message['Subject'] = "Your Resume Evaluation Results"

    body = f"""
Dear Candidate,

Thank you for submitting your resume. Here is your detailed evaluation:

OVERALL CV SCORE: {feedback['overall_score']}/100
JD MATCH SCORE: {feedback['jd_match_score']}/100

SCORE BREAKDOWN:
• Work Experience: {feedback['component_scores']['work_experience']}/100
• Education: {feedback['component_scores']['education']}/100
• Skills: {feedback['component_scores']['skills']}/100
• Formatting: {feedback['component_scores']['formatting']}/100

BATCH YEAR: {batch_year}

RELEVANT AI EXPERIENCE:
{chr(10).join(f"- {exp}" for exp in ai_experience)}

KEY STRENGTHS:
{chr(10).join(f"- {strength}" for strength in feedback['strengths'])}

AREAS FOR IMPROVEMENT:
{chr(10).join(f"- {weakness}" for weakness in feedback['weaknesses'])}

SUGGESTIONS:
{chr(10).join(f"- {suggestion}" for suggestion in feedback['suggestions'])}

MATCHING KEYWORDS FOUND:
{chr(10).join(f"- {keyword}" for keyword in feedback['relevant_keywords_found'])}

MISSING KEYWORDS TO CONSIDER:
{chr(10).join(f"- {keyword}" for keyword in feedback['missing_keywords'])}

NEXT STEPS:
1. Review the feedback and suggestions provided
2. Update your resume addressing the areas for improvement
3. Consider gaining experience in the missing technical areas
4. Resubmit your updated resume for another evaluation

Best regards,
AI Resume Screening Team
"""
    
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to_email, message.as_string())


# Step 4: Main Pipeline

def main():
    fetch_resumes()
    job_description = open("job_description.txt").read()
    
    for file in os.listdir(RESUME_FOLDER):
        filepath = os.path.join(RESUME_FOLDER, file)
        resume_text = extract_text(filepath)
        
        # Mask PII
        masked_text = mask_pii(resume_text)
        
        # Extract additional information
        batch_year = extract_batch_year(resume_text)
        ai_experience = extract_ai_experience(resume_text)
        
        # Get detailed feedback
        feedback = score_resume(masked_text, job_description)
        
        # Use specific email address
        to_email = "Receiver's Email"
        
        # Send enhanced feedback
        send_feedback_email(to_email, feedback, batch_year, ai_experience)
        print(f"Feedback sent for: {file}")


if __name__ == "__main__":
    main()
