# AI-Powered CV Screening Agent

> **IMPORTANT NOTE**: This application requires your own credentials to function properly. You must use:
> - Your own Gmail account and generate an App Password for it
> - Your own OpenAI API key (get one from [OpenAI's platform](https://platform.openai.com/))
> - Never share or commit your credentials
> - The example credentials in the code are placeholders and won't work. 

An automated resume screening and evaluation system that uses AI to analyze resumes, provide detailed feedback, and send personalized evaluation emails to candidates.

## Example Output

Here's an example of how the automated feedback email looks:

### Part 1: Overall Scores and Breakdown
![CV Evaluation Part 1](https://github.com/KarimaMinal/ElintAI_assignment/blob/main/screenshots/Screenshot%202025-04-17%20000304.png))

### Part 2: Experience and Skills Analysis
![CV Evaluation Part 2](https://github.com/KarimaMinal/ElintAI_assignment/blob/main/screenshots/Screenshot%202025-04-17%20000335.png))

### Part 3: Keywords and Next Steps
![CV Evaluation Part 3](https://github.com/KarimaMinal/ElintAI_assignment/blob/main/screenshots/Screenshot%202025-04-17%20000403.png))


## Features

- **Automated Resume Processing**
  - Extracts resumes from email attachments (PDF, DOCX)
  - Masks personal identifiable information (PII)
  - Extracts batch year and AI-related experience

- **Intelligent Resume Evaluation**
  - Overall CV scoring (0-100)
  - Component-wise scoring:
    - Work Experience
    - Education
    - Skills
    - Formatting
  - JD-CV match score
  - Keyword analysis
  - AI experience detection

- **Detailed Feedback Generation**
  - Strengths analysis
  - Areas for improvement
  - Actionable suggestions
  - Matching keywords
  - Missing keywords
  - Next steps

- **Automated Email Communication**
  - Personalized feedback emails
  - Professional formatting
  - Comprehensive evaluation breakdown

## Prerequisites

- Python 3.8 or higher
- Gmail account with App Password
- OpenAI API key
- Internet connection

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cv-screening-agent
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the following variables:
```env
EMAIL=your-email@gmail.com
APP_PASSWORD=your-gmail-app-password
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
```

4. Create a `job_description.txt` file with the target job description.

## Usage

1. Place resumes in the `resumes` folder (PDF or DOCX format)

2. Run the script:
```bash
python cv_screening_agent.py
```

3. The script will:
   - Process all resumes in the folder
   - Generate detailed evaluations
   - Send feedback emails to candidates

## Project Structure

```
cv-screening-agent/
├── cv_screening_agent.py    # Main script
├── requirements.txt         # Python dependencies
├── .env                    # Environment variables
├── job_description.txt     # Target job description
└── resumes/               # Folder for resume files
```

## Features in Detail

### Resume Processing
- Supports PDF and DOCX formats
- Automatically masks sensitive information
- Extracts key information like batch year and AI experience

### Scoring System
- Comprehensive evaluation across multiple dimensions
- Weighted scoring based on job requirements
- Keyword matching and analysis
- AI experience detection and evaluation

### Email Feedback
- Professional email template
- Detailed score breakdown
- Actionable feedback and suggestions
- Next steps for improvement

## Security

- PII masking for privacy
- Secure email handling
- Environment variable protection
- No hardcoded credentials
- Always use your own API keys and credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the repository or contact the maintainers.

## Acknowledgments

- OpenAI for providing the GPT API
- PyPDF2 for PDF processing
- docx2txt for DOCX processing 

###
