from flask import Flask, request, render_template, flash, redirect, url_for
import fitz
import os
import google.generativeai as genai
import secrets
import re

app = Flask(__name__)

# Generate a random secret key ONCE and store it in the code (for non-production)
app.secret_key = secrets.token_hex(16)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set your Gemini API key (LESS SECURE - ONLY FOR PERSONAL, LOCAL USE)
genai.configure(api_key="AIzaSyDXEANIyCVOANTVBOGnMGOmrR8okcqc7ic")


def extract_text_from_pdf(pdf_file):
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except fitz.fitz.FileDataError:
        return "Error: Invalid PDF file."
    except Exception as e:
        return f"An error occurred during PDF processing: {str(e)}"

def ATS_score(resume_text):
    """Generates an ATS analysis using Gemini."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
        ## 📊 ATS Resume Strength Analysis

        ### **Task:**  
        You are a professional resume analyzer with expertise in **Applicant Tracking Systems (ATS)**. Your job is to **analyze the resume text and score it** based on **ATS compatibility, keyword optimization, readability, and structure**.

        ---

        **📌 Input:**
        **Resume Text:**
         ```
         {resume_text}
         ```
         ---

        ### **📊 Expected Output Format (Table Format)**
         
         The response should be structured **exactly** in the following table format:

         Final ATS Score: (X)  ** (X should be multiply of 10)

         Distribution :

          Keyword Optimization  :        ⚠️ X/10 ,Evaluate the presence of job-relevant keywords (e.g., skills, industry terms). 
          Section Headings    :          ⚠️ X/10 ,   Assess the clarity of sections (e.g., "Define Yourself" should be "Soft Skills"). 
          Formatting & Readability :     ⚠️ X/10  ,  Ensure proper font usage, spacing, and bullet points. 
          Work Experience  :             ⚠️ X/10                  Check if experience is listed properly and quantified where possible. 
          Project Descriptions :         ⚠️ X/10 , Assess whether project descriptions are detailed and include impact metrics. 
          Education Section :            ✅ X/10 , Evaluate the structure and clarity of education details. 
          Skills Section :               ⚠️ X/10 , Ensure tech skills and soft skills are clearly categorized. 
          Contact Information:           ⚠️ X/10 , Verify if all essential contact details are ATS-readable (no special characters). 
          LinkedIn/GitHub :              ⚠️ X/10 ,Check if professional profile links are included. 

        
        Comments : 
          Strengths: List key strengths of the resume.  
          Areas to Improve: List specific improvement points. (Write in short way)


        ATS-Friendly Resume Improvements :(based on the given resume in the bellow format explain every point) 

         * Standard Section Headings: Use industry-standard headings like "Experience", "Projects", "Education".
         * Keyword Optimization: Improve keyword usage by matching job descriptions.
         * Formatting: Use consistent bullet points, font, and spacing for readability.
         * Experience Section: Ensure quantifiable results are included (e.g., "Improved accuracy by 20%").
         * Final Suggestions: Add LinkedIn and GitHub for credibility.

         ---

         📢 **Important:**  
         - Follow the table format **exactly** as shown.  
         - **Use emojis (✅, ⚠️, ❌) for scores** to improve readability. 
             (if the score is equal to  8 or above it then ✅)
             (if the score is equal to  5 or above it  but less than 8 then ⚠️)
             (if the score is  less than 5 then ❌)
            
         - Keep responses **concise yet informative**.  

         """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred during Gemini analysis: {str(e)}"
    

def parse_ats_report(ats_report):
    """Parses the ATS report string into structured dictionaries."""

    try:
        # Final ATS Score
        final_score_match = re.search(r"Final ATS Score:\s*(\d+)", ats_report)
        final_ats_score = int(final_score_match.group(1)) if final_score_match else None

        # Distribution (using a more robust approach)
        distribution = {}
        distribution_matches = re.findall(r"([a-zA-Z\s&]+):\s*(✅|⚠️|❌)\s*(\d+/10)", ats_report)
        for category, emoji, score in distribution_matches:
            distribution[category.strip()] = f"{emoji} {score}"

        # Comments
        comments = {}
        comments_matches = re.findall(r"(Strengths|Areas to Improve):\s*(.+?)(?=\n|$)", ats_report, re.DOTALL) #Improved Regex
        for key, value in comments_matches:
            comments[key.strip()] = value.strip()

        # ATS-Friendly Resume Improvements
        improvements = {}
        improvements_matches = re.findall(r"(?:\*\s*)([a-zA-Z\s]+):\s*(.+)", ats_report)
        for key, value in improvements_matches:
            improvements[key.strip()] = value.strip()

        return {
            "final_ats_score": final_ats_score,
            "distribution": distribution,
            "comments": comments,
            "improvements": improvements,
        }

    except AttributeError as e:
        print(f"AttributeError during parsing: {e}")
        return None  # Or handle the error as needed
    except Exception as e:
        print(f"An error occurred during parsing: {e}")
        return None




# EXTRACT EMPLOYEE INFORMATION
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
      "location": location,
      "summary": summary,  # Add this line to return summary
      "skills": skills,
        # Add this line to return location
      "experience": experience_sections,
      "certifications": certification_sections,
      "education": education_sections,
      
    }
  except Exception as e:
    print(f"Error during extraction: {e}")
    return None    

def emp_details(resume_text):
    """Generates an ATS analysis using Gemini."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
        ## Extract Resume Information in a Human-Readable Format
    
        **Task:** You are an expert resume parser. Extract key information from the provided resume text and format it in a human-readable way.
    
        **Input:**
        ```
        {resume_text}
        ```
    
        **Instructions:**

1.  **Human-Readable Output:** Present the extracted information in a clear and concise manner, using labels like "Name," "Email," and "Skills."
2.  **Key Information:** Extract the following information, if present in the resume:
    *   **Name:** The candidate's full name. 
    *   **First_Name:** The candidate's First name

    *   **Email:** The candidate's email address.
    *   **Mobile No:** The candidate's contact number
    *   **Location:**  The candidate's city if have
    *   **Professional Summary:** The candidate's profile summary if have 

    *   **Skills:** A list of skills mentioned in the resume, separated by commas. 
        (GAP VACANT LINE)
    *   **Experience:** A list of experience mentioned in the resume, separated by bullets. If no experience mentioned, just mention " * no experience" and if domain experiance present in the resume by any chance , then just include that domain experiace details under Experiance section using * bullet. **Each experience point should be enclosed within two asterisks (**) like this: **Experience Point Text**. **Remove any bullet points or indentation before each experience point.**
        (GAP VACANT LINE)
    *   **Certification:** A list of certifications mentioned in the resume, separated by bullets. If no certification, just mention " * no certification found".
        (GAP VACANT LINE)
    *   **Education:** A list of level of education & percentage if mentioned, separated by bullets.

3.  **Handling Missing Information:** If a piece of information is not found in the resume, omit the corresponding label from the output.
4.  **Data Cleaning:** Clean up extracted text (e.g., remove extra whitespace, newlines).
5.  **Don't miss any section which are mentioned on the point 2, if any section is missing just mention that section and write that section is missing    
6.  **In the resume,experiance section if any particular heading is bold and other section is not then include that non bold part also and keep it inside '**---**'**

**Example Input:**
    
        ```
        Soubarna Das
        something@gmail.com
    
        Skills: Java, Python, Machine Learning, Natural Language Processing
    
        Experience
        Software Engineer, Acme Corp, Jan 2020 - Present
        Developed web applications...
    
        Education
        B.S. Computer Science, University X, 2016-2020..
        ```
    
        **Example Output: the output template should be strictlt followed**
    
        ```
        Name: Soubarna Das
        First_Name: Soubarna
        Email: soubarna.das@capgemini.com
        Mobile No: +91 9163766182
        Location: Kolkata
        Professional Summary: (Missing from the provided resume)
        Skills: Python, C++, JAVA, JavaScript, HTML, CSS, BOOTSTRAP, REACT, FLASK, Gen AI & LLM, ECM (OpenText, SharePoint), MS Azure, Power BI, MySQL, Business Analysis and Development, Excellent Communication.

        Experience: (include all the points within ** points ** : like this)
        *   **Gen-Garage POC – Pixel - Craft: Developer (Backend, Frontend). Designed and implemented a user-friendly web application that empowers users to both create unique images from text prompts using AI and enhance existing photos with a powerful image editor.  Used Python, Streamlit, APIs, HTML, CSS, and JavaScript.**
        *   **Gen-Garage POC – HR AI Assistant: Developer (Back-end, Front-end). Developed an AI-driven HR platform streamlining recruitment and employee management.  Features included an HR dashboard for candidate tracking and AI-powered interviews, an employee dashboard with resume generation and analytics, and secure login/signup functionality. Used Python, Flask, React, and APIs.**
        Domain Experience:  (This section was present but lacked specific details in the provided resume.)


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
        ```
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred during Gemini analysis: {str(e)}"
    


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'resume' not in request.files:
            flash('No file part')
            return redirect(request.url)

        resume = request.files['resume']

        if resume.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if resume and allowed_file(resume.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], resume.filename)
            try:
                resume.save(filename)
                with open(filename, 'rb') as f:
                    resume_text = extract_text_from_pdf(f)

                if "Error" in resume_text:
                    flash(resume_text)
                    return redirect(request.url)

                ats_report = ATS_score(resume_text)
                parsed_data = parse_ats_report(ats_report)
                employee_data = emp_details(resume_text)

                details = extract_resume_info(employee_data)
                
                
            
                ats_score = parsed_data["final_ats_score"]
                distribution = parsed_data["distribution"]
                comments = parsed_data["comments"]
                Suggestions = parsed_data["improvements"]

                return render_template("analysis_result.html", ats_report=ats_report,ats_score=ats_score , distribution = distribution, comments=comments, Suggestions=Suggestions,employee_data=employee_data,details=details)

            except Exception as e:
                flash(f"An error occurred: {str(e)}")
                return redirect(request.url)
            finally:
                os.remove(filename)
        else:
            flash('Allowed file types are pdf')
            return redirect(request.url)

    return render_template("index.html")


@app.route("/results")
def results():
    ats_report = request.args.get('ats_report')
    ats_score = request.args.get('ats_score')
    distribution = request.args.get('distribution')
    comments =  request.args.get('comments')
    Suggestions = request.args.get('Suggestions')
    employee_data = request.args.get('employee_data')
    details = request.args.get('details')
    
    if ats_report is None:
        flash("No analysis results found. Please submit a resume.")
        return redirect(url_for('index'))
    if ats_score is None:
        flash("No ats score generated")
        return redirect(url_for('index'))
    if distribution is None:
        flash("No distribution generated")
        return redirect(url_for('index'))
    if comments is None:
        flash("No comments generated")
        return redirect(url_for('index'))
    if Suggestions is None:
        flash("No Suggestions generated")
        return redirect(url_for('index'))
    if details is None:
        flash ("No Suggestion generated")
        return redirect(url_for('index'))
   
    return render_template("analysis_result.html", ats_report=ats_report,ats_score=ats_score,distribution=distribution,comments=comments,Suggestions=Suggestions,employee_data=employee_data,details=details)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    app.run(debug=True)







# f"""
#         ## 📊 ATS Resume Strength Analysis

#         ### **Task:**  
#         You are a professional resume analyzer with expertise in **Applicant Tracking Systems (ATS)**. Your job is to **analyze the resume text and score it** based on **ATS compatibility, keyword optimization, readability, and structure**.

#         ---

#         **📌 Input:**
#         **Resume Text:**
#          ```
#          {resume_text}
#          ```
#          ---

#         ### **📊 Expected Output Format (Table Format)**
         
#          The response should be structured **exactly** in the following table format:

#          | **Category**                                 | **Score (Out of 10)** | **Comments & Suggestions** |
#          |-----------------------------------------------|-----------------------|----------------------------|
#          | **Keyword Optimization**                       | ⚠️ X/10                 | Evaluate the presence of job-relevant keywords (e.g., skills, industry terms). |
#          | **Section Headings**                           | ⚠️ X/10                 | Assess the clarity of sections (e.g., "Define Yourself" should be "Soft Skills"). |
#          | **Formatting & Readability**                   | ⚠️ X/10                 | Ensure proper font usage, spacing, and bullet points. |
#          | **Work Experience**                           | ❌ X/10                 | Check if experience is listed properly and quantified where possible. |
#          | **Project Descriptions**                       | ✅ X/10                 | Assess whether project descriptions are detailed and include impact metrics. |
#          | **Education Section**                          | ✅ X/10                 | Evaluate the structure and clarity of education details. |
#          | **Skills Section**                             | ⚠️ X/10                 | Ensure tech skills and soft skills are clearly categorized. |
#          | **Contact Information**                        | ⚠️ X/10                 | Verify if all essential contact details are ATS-readable (no special characters). |
#          | **LinkedIn/GitHub**                           | ❌ X/10                 | Check if professional profile links are included. |

#          ### **🔹 Final ATS Score: X/10 (Overall Summary)**
#          ✅ **Strengths:** List key strengths of the resume.  
#          ⚠️ **Areas to Improve:** List specific improvement points.

#          ---

#          ### **🔹 ATS-Friendly Resume Improvements**
#          - **Standard Section Headings:** Use industry-standard headings like **"Experience"**, **"Projects"**, **"Education"**.
#          - **Keyword Optimization:** Improve keyword usage by **matching job descriptions**.
#          - **Formatting:** Use **consistent bullet points, font, and spacing** for readability.
#          - **Experience Section:** Ensure **quantifiable results** are included (e.g., "Improved accuracy by 20%").
#          - **Final Suggestions:** Add **LinkedIn and GitHub** for credibility.

#          ---

#          📢 **Important:**  
#          - Follow the table format **exactly** as shown.  
#          - **Use emojis (✅, ⚠️, ❌) for scores** to improve readability.  
#          - Keep responses **concise yet informative**.  

#          """