
# 📄 CV Studio

**CV Studio** is an AI-powered career assistant that tailors your resume to any job description using strictly your real, verified background. Alongside a clean, ATS-friendly Markdown resume, it generates an honest compatibility score, highlights evidence-backed strengths, and identifies skill gaps without inventing facts or metrics.

## ✨ Key Features

* **Strict Fact-Preservation:** Uses only facts explicitly provided in your background—never fabricates employers, job titles, dates, tools, or metrics.
* **ATS-Friendly Markdown Resume:** Reorganizes and sharpens your summary, skills, and experience bullets to align naturally with the target role.
* **Evidence-Based Job-Fit Score:** Estimates role alignment (`0–100%`) based on essential responsibilities, required skills, and qualifications.
* **Transparent Gap Analysis:** Categorizes missing or unclear requirements by priority (`High`, `Medium`, `Low`) and gives actionable recommendations on what real evidence to add.

## 🚀 How to Use

1. **Paste the Job Description:** Copy the complete target job posting into the left input box.
2. **Enter Candidate Details:** Paste your existing resume, project notes, skills, education, and achievements into the right input box.
3. **Generate:** Click **Generate tailored resume** to receive your customized Markdown CV and detailed job-fit feedback.

## ⚙️ Environment Variables (For Self-Hosting)

If you duplicate this Space or run it locally, configure the following variables in your Space **Settings → Variables and secrets** (or a local `.env` file):

* `GROQ_API_KEY`: Your Groq API key.
* `GROQ_MODEL`: The Groq model ID to use (e.g., `llama-3.3-70b-versatile`).

## 🛠️ Tech Stack

* **Frontend:** [Gradio](https://gradio.app)
* **LLM Inference:** [Groq API](https://groq.com)
* **Language:** Python
