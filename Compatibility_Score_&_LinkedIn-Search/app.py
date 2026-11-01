from flask import Flask, request, render_template, flash, jsonify, redirect
import fitz
import os
import google.generativeai as genai
import secrets
import re
import urllib.parse

app = Flask(__name__)

# Generate a random secret key ONCE and store it in the code (for non-production)
app.secret_key = secrets.token_hex(16)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set your Gemini API key (LESS SECURE - ONLY FOR PERSONAL, LOCAL USE)
genai.configure(api_key="AIzaSyBX6oXS2ScuOpBhgwHldbILDV0GFHD5B4I")

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

def generate_ats_analysis(resume_text, job_description_text):
    """Generates an ATS analysis using Gemini."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
        ## ATS Resume Scoring and Improvement Suggestions (Concise Output)

        **Task:** You are an Applicant Tracking System (ATS) expert. Analyze a resume and job description, providing a concise ATS score and targeted improvement suggestions.

        **Input:**
        1. **Resume Text:** {resume_text}
        2. **Job Description Text:** {job_description_text}
        3. **Scoring Parameters:**
            - Keyword Matching: 50%
            - Experience: 30%
            - Education: 10%
            - Spelling/Grammar Check: 10%

        **Output Format:**

        Strictly adhere to the following output format. Do not include any introductory or explanatory text outside of these sections.

        ```
        ATS Score: <score out of 100>
        Suggestions:
        <bullet point list of improvement suggestions and end every point with a *>
        ```

        **Example:**

        ```
        ATS Score: 75
        Suggestions:
        *   Add more quantifiable achievements to your work experience.
        *   Highlight skills that directly match the job description's keywords.
        *   Ensure consistent formatting throughout the resume.
        ```

        **Instructions:**

        1.  **ATS Score:** Provide a single numerical score out of 100 representing the resume's overall fit for the job description. Base this score on the following parameters:
            *   Keyword Matching (50%): How well the resume's keywords match those in the job description.
            *   Experience (30%): How relevant and substantial the candidate's experience is to the job requirements.
            *   Education (10%): The relevance of the candidate's education to the job requirements.
            *   Spelling/Grammar Check (10%): The accuracy of spelling and grammar in the resume.

        2.  **Suggestions:** Give a concise bullet-point list of 3-5 specific, actionable suggestions for improving the resume to better align with the job description and improve its ATS compatibility. Focus on concrete improvements related to keywords, experience, education, formatting, etc. Be direct and avoid lengthy explanations.
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred during Gemini analysis: {str(e)}"

def extract_ats_info(text):
    """Extracts ATS score and suggestions from a formatted text block."""
    try:
        # Extract ATS Score
        score_match = re.search(r"ATS Score:\s*(\d+)", text)
        ats_score = int(score_match.group(1)) if score_match else None

        # Extract Suggestions
        suggestions_match = re.search(r"Suggestions:\s*(.+)", text, re.DOTALL)
        suggestions_text = suggestions_match.group(1).strip() if suggestions_match else None

        if suggestions_text:
          suggestions = [s.strip() for s in suggestions_text.split('*') if s.strip()]
        else:
          suggestions = None
        return ats_score, suggestions
    except AttributeError: #Catch if regex doesn't find a match
        return None, None
    except Exception as e:
        print(f"An error occurred during extraction: {e}")
        return None, None

# Function to generate LinkedIn people search URL based on provided keywords
def generate_linkedin_people_search_url(keywords):
    base_url = "https://www.linkedin.com/search/results/people/"
    query_params = {
        "keywords": " ".join(keywords)  # Join the list of keywords into a single space-separated string
    }
    encoded_params = urllib.parse.urlencode(query_params)
    return f"{base_url}?{encoded_params}"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'resume' not in request.files:
            return jsonify({"success": False, "message": "No file part"})

        resume = request.files['resume']
        job_description_text = request.form.get('job_description')

        if resume.filename == '':
            return jsonify({"success": False, "message": "No selected file"})

        if resume and allowed_file(resume.filename):
            try:
                filename = os.path.join(app.config['UPLOAD_FOLDER'], resume.filename)
                resume.save(filename)
                with open(filename, 'rb') as f:
                    resume_text = extract_text_from_pdf(f)

                if "Error" in resume_text:
                    return jsonify({"success": False, "message": resume_text})

                analysis_result = generate_ats_analysis(resume_text, job_description_text)
                ats_score2, suggestions2 = extract_ats_info(analysis_result)
                

                # Return JSON response
                return jsonify({
                    "success": True,
                    "ats_score": ats_score2,
                    "suggestions": suggestions2,
                   
                })

            except Exception as e:
                return jsonify({"success": False, "message": f"An error occurred: {str(e)}"})
            finally:
                if os.path.exists(filename):
                    os.remove(filename)

        else:
            return jsonify({"success": False, "message": "Allowed file types are pdf"})

    # Handle GET request
    return render_template("index.html")

@app.route('/search_people', methods=['POST'])
def search_people():
    # Get the 'keywords' from the form input
    keywords = request.form.get('keywords')

    # Split the keywords by commas and strip any surrounding whitespace
    keywords_list = [kw.strip() for kw in keywords.split(',')]

    # Generate the LinkedIn people search URL
    search_url = generate_linkedin_people_search_url(keywords_list)

    # Redirect the user to the generated LinkedIn search URL
    return redirect(search_url)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    app.run(debug=True)