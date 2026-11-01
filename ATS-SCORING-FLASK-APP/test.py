import re
def extract_resume_info(text):
  """Extracts resume information."""
  try:
    name_match = re.search(r"^Name:\s*(.*)", text, re.MULTILINE)
    first_name_match = re.search(r"^First_Name:\s*(.*)", text, re.MULTILINE)
    mobile_match = re.search(r"^Mobile No:\s*(.*)", text, re.MULTILINE)
    email_match = re.search(r"^Email:\s*([\w\.-]+@[\w\.-]+\.\w+)", text, re.MULTILINE)
    skills_match = re.search(r"^Skills:\s*(.*)", text, re.MULTILINE)
    location_match = re.search(r"^Location:\s*(.*)", text, re.MULTILINE)  # Add this line to find location
    summary_match = re.search(r"^Professional Summary:\s*(.*)", text, re.MULTILINE)  # Add this line to find professional summary

    sections = re.split(r"\n\s*\n", text) # Split into sections by double newlines

    experience_sections = []
    certification_sections = []
    education_sections = []

    in_experience = False
    in_certification = False
    in_education = False

    for section in sections:
      if section.startswith("Experience:"):
        in_experience = True
        in_certification = False
        in_education = False
        items = re.findall(r"^\*\s*(.+)", section, re.MULTILINE)
        experience_sections.extend([item.strip() for item in items])

      elif section.startswith("Certification:"):
        in_experience = False
        in_certification = True
        in_education = False
        items = re.findall(r"^\*\s*(.+)", section, re.MULTILINE)
        certification_sections.extend([item.strip() for item in items])
      elif section.startswith("Education:"):
        in_experience = False
        in_certification = False
        in_education = True
        items = re.findall(r"^\*\s*(.+)", section, re.MULTILINE)
        education_sections.extend([item.strip() for item in items])
      elif in_experience:
        items = re.findall(r"^\*\s*(.+)", section, re.MULTILINE)
        experience_sections.extend([item.strip() for item in items])
      elif in_certification:
        items = re.findall(r"^\*\s*(.+)", section, re.MULTILINE)
        certification_sections.extend([item.strip() for item in items])
      elif in_education:
        items = re.findall(r"^\*\s*(.+)", section, re.MULTILINE)
        education_sections.extend([item.strip() for item in items])

    name = name_match.group(1).strip() if name_match else None
    first_name = first_name_match.group(1).strip() if first_name_match else None
    mobile_number = mobile_match.group(1).strip() if mobile_match else None
    email = email_match.group(1).strip() if email_match else None
    skills = [s.strip() for s in skills_match.group(1).split(",")] if skills_match else None
    location = location_match.group(1).strip() if location_match else None  # Add this line to store location
    summary = summary_match.group(1).strip() if summary_match else None  # Add this line to store summary

    return {
      "name": name,
      "first_name": first_name,
      "mobile_number": mobile_number,
      "email": email,
      "skills": skills,
      "location": location,  # Add this line to return location
      "experience": experience_sections,
      "certifications": certification_sections,
      "education": education_sections,
      "summary": summary,  # Add this line to return summary
    }
  except Exception as e:
    print(f"Error during extraction: {e}")
    return None

# Example usage:
text = """

Name: Soubarna Das
First_Name: Soubarna
Email: soubarna.das@capgemini.com
Mobile No: +91 9163766182
Location: Kolkata
Professional Summary: (Missing from the provided resume)

Skills: Python, C++, JAVA, JavaScript, HTML, CSS, BOOTSTRAP, JS, REACT, FLASK, Gen AI & LLM, ECM (OpenText, SharePoint), MS Azure, Power BI, MySQL, Business Analysis and Development, Excellent Communication


Experience:
* **Capgemini, Bangalore, India (Nov 2023 - Present): AI/ML Technical Lead Analyst**
* **Engineered a Generative AI application using TensorFlow, Python, and GPT-3.5 to enhance regional dialect understanding and improve user interaction.**
* **Designed and trained NLP models for various regional dialects, achieving high accuracy in language recognition and response generation.**
    * Deployed a voice bot capable of managing 90% of routine inquiries, increasing overall team efficiency by 60%.
    * Collaborated on a project that enhanced forecasting capabilities for renewable and non-renewable energy consumption by 80% using AI/ML techniques.
    * Oversaw 10-12 projects, including 3 client projects and several internal initiatives.
    * Led a team to victory at the Generative AI hackathon during “re: publica Berlin 2024”.
    * Boosted social listening capabilities by 75% for TikTok by integrating advanced automated text generation and sentiment analysis tools using GPT-3 and BERT.
    * Elevated conversational AI performance by 85% by integrating GPT-3 and other generative models.
    * Extended the reach and accessibility of AI-driven solutions by 75% by tailoring them to meet regional needs.
* **Ministry of Electronics and Information Technology, New Delhi, India (Jul 2022 - Oct 2022): AI/ML Intern**
    * Developed a Sign Language Communication System for the SAHAYAK project, improving communication efficiency by 80% using advanced computer vision techniques.
    * Implemented real-time computer vision libraries like OpenCV and MediaPipe, resulting in a 95% increase in gesture recognition accuracy.
    * Enhanced image processing capabilities, significantly improving the reliability of sign language recognition.
    * Collaborated on AI/ML integration, boosting the SAHAYAK system’s effectiveness.


Domain Experience: (This section was present but lacked specific details in the provided resume.)


Certification:
* Agile Software Development – University of Minnesota – Coursera.
* OpenText ECM Content Server getting Started - Udemy.
* SAP Vendor Invoice Management (VIM) by OpenText - Udemy
* Microsoft Power BI for Business Intelligence  - Udemy 
* EF Solo: EF Level 16 - Upper Advanced - CEFR Level C2 
* Generative AI for Everyone - Coursera 
* Ocean Certification in SQL(L1 and L2)


Education:
* B.Tech. Information Technology, Meghnad Saha Institute of Technology, 2023, 8.97 CGPA
* H.S.C, Kalidhan Institution, 2019, 71.8%
* S.S.C, Gangapuri Siksha Sadan, 2017, 83.42%

"""

details = extract_resume_info(text)

if details:
    for key, value in details.items():  # Iterate through all key-value pairs
        print(f"{key.capitalize()}: {value}") # Print each key and value
else:
    print("Extraction failed.")
