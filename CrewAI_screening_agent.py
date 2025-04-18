from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
import imaplib
import email
import os
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import PyPDF2
import docx2txt
from dotenv import load_dotenv
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Load credentials
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("APP_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RESUME_FOLDER = "resumes"

# Ensure required variables are present
if not all([EMAIL, PASSWORD, OPENAI_API_KEY]):
    raise ValueError("Missing required environment variables. Check your .env file.")

# Create resumes folder if it doesn't exist
os.makedirs(RESUME_FOLDER, exist_ok=True)

# Initialize OpenAI
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=OPENAI_API_KEY
)

def mask_pii(text):
    """Mask personal identifiable information in the text."""
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL]', text)
    text = re.sub(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})', '[NAME]', text)
    return text

def extract_batch_year(text):
    """Extract batch year from resume text."""
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

def extract_text(filepath):
    """Extract text from PDF or DOCX files."""
    try:
        if filepath.endswith(".pdf"):
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
        elif filepath.endswith(".docx"):
            return docx2txt.process(filepath)
        return ""
    except Exception as e:
        logger.error(f"Error extracting text from {filepath}: {str(e)}")
        return ""

# Define tools
extract_text_tool = Tool(
    name="extract_text",
    func=extract_text,
    description="Extract text from PDF or DOCX files"
)

mask_pii_tool = Tool(
    name="mask_pii",
    func=mask_pii,
    description="Mask personal identifiable information in text"
)

extract_ai_experience_tool = Tool(
    name="extract_ai_experience",
    func=extract_ai_experience,
    description="Extract AI-related experience from text"
)

extract_batch_year_tool = Tool(
    name="extract_batch_year",
    func=extract_batch_year,
    description="Extract batch year from resume text"
)

# Define Agents
resume_parser = Agent(
    role='Resume Parser',
    goal='Extract and process resume information accurately',
    backstory='Expert in parsing and extracting information from resumes',
    tools=[extract_text_tool, mask_pii_tool],
    llm=llm
)

skills_analyzer = Agent(
    role='Skills Analyzer',
    goal='Analyze technical skills and experience',
    backstory='Expert in evaluating technical skills and AI experience',
    tools=[extract_ai_experience_tool, extract_batch_year_tool],
    llm=llm
)

evaluator = Agent(
    role='Resume Evaluator',
    goal='Provide comprehensive resume evaluation',
    backstory='Expert in evaluating resumes against job requirements',
    llm=llm
)

feedback_composer = Agent(
    role='Feedback Composer',
    goal='Create detailed and constructive feedback',
    backstory='Expert in composing professional and helpful feedback',
    llm=llm
)

def create_tasks(filepath, job_description):
    """Create tasks for the crew to process a resume."""
    
    # Task 1: Parse Resume
    parse_resume = Task(
        description=f"""
        Parse the resume at {filepath}:
        1. Extract text from the document
        2. Mask PII information
        3. Return the processed text
        """,
        agent=resume_parser,
        expected_output="Processed resume text with masked PII"
    )

    # Task 2: Analyze Skills
    analyze_skills = Task(
        description="""
        Analyze the parsed resume for:
        1. Technical skills
        2. AI/ML experience
        3. Extract batch year
        4. Return detailed analysis
        """,
        agent=skills_analyzer,
        expected_output="Detailed skills analysis",
        context=[parse_resume]
    )

    # Task 3: Evaluate Resume
    evaluate_resume = Task(
        description=f"""
        Evaluate the resume against this job description:
        {job_description}
        
        Provide:
        1. Overall score (0-100)
        2. Component scores
        3. JD match score
        4. Keywords analysis
        """,
        agent=evaluator,
        expected_output="Resume evaluation scores and analysis",
        context=[parse_resume, analyze_skills]
    )

    # Task 4: Compose Feedback
    compose_feedback = Task(
        description="""
        Create detailed feedback including:
        1. Scores breakdown
        2. Strengths and weaknesses
        3. Suggestions for improvement
        4. Next steps
        Return in a structured format
        """,
        agent=feedback_composer,
        expected_output="Structured feedback for the candidate",
        context=[evaluate_resume]
    )

    return [parse_resume, analyze_skills, evaluate_resume, compose_feedback]

def send_feedback_email(to_email, feedback):
    """Send the feedback email to the candidate."""
    try:
        message = MIMEMultipart()
        message['From'] = EMAIL
        message['To'] = to_email
        message['Subject'] = "Your Resume Evaluation Results"

        # Convert CrewAI output to string
        feedback_str = str(feedback)
        message.attach(MIMEText(feedback_str, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, to_email, message.as_string())
        logger.info(f"Feedback email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send feedback email: {str(e)}")
        raise

def main():
    try:
        # Read job description
        with open("job_description.txt", "r") as f:
            job_description = f.read()
        
        # Process each resume
        for file in os.listdir(RESUME_FOLDER):
            if not file.endswith(('.pdf', '.docx')):
                continue
                
            filepath = os.path.join(RESUME_FOLDER, file)
            logger.info(f"Processing resume: {file}")
            
            # Create crew for this resume
            crew = Crew(
                agents=[resume_parser, skills_analyzer, evaluator, feedback_composer],
                tasks=create_tasks(filepath, job_description),
                process=Process.sequential
            )

            # Execute the crew's tasks
            result = crew.kickoff()

            # Send feedback email
            to_email = "Receiver email"  # Specific email address
            send_feedback_email(to_email, result)
            logger.info(f"Completed processing: {file}")
            
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
