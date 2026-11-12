from groq import Groq
import gradio as gr
import os
import json
import re
from typing import Any
from dotenv import load_dotenv

# Load variables from .env into the environment
load_dotenv()

# Access the variables
grok_api_key = os.getenv('GROQ_API_KEY')
DEFAULT_MODEL = os.getenv('GROQ_MODEL')

def extract_json(text: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating a surrounding Markdown code fence."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise gr.Error(f"The model returned invalid structured output: {exc}") from exc

def generate_resume(job_description: str, user_details: str, cv_format):
    if not job_description or not job_description.strip():
        raise gr.Error("Please paste the job description.")
    if not user_details or not user_details.strip():
        raise gr.Error("Please enter the candidate's details.")

    client = Groq(api_key=grok_api_key)

    resume_prompt = """
            You are an expert resume writer.
            Use ONLY facts explicitly present in the candidate details. Do not invent employers,
            job titles, dates, qualifications, tools, certifications, achievements, metrics,
            project outcomes, or years of experience. You may improve wording and organization,
            but preserve the exact meaning. Do not imply the candidate has skills or experience
            not evidenced in the candidate details.

            Resume guidance:
            - Tailor the headline, summary, skills, and experience bullets to fit the job description.
            - Keep all facts strictly truthful and avoid keyword stuffing.
            - Prioritize the most relevant evidence for the role and use concise, impact-oriented bullets.
            - Do not fabricate numerical outcomes. Use placeholders only when clearly marked
            [ADD METRIC] and only if a metric would materially improve a genuine achievement.
            - If dates, contact details, education, or employer names are absent, omit those
            fields or sections rather than inventing them.
            - Return ONLY the polished, ATS-friendly Markdown resume. Do not include any JSON,
            job-fit scoring, gap analysis, introductory remarks, or closing commentary.
            """
    
    feedback_prompt = """
        You are an evidence-based job-fit analyst.
        Use ONLY facts explicitly present in the candidate details. Do not invent employers,
        job titles, dates, qualifications, tools, certifications, achievements, metrics,
        project outcomes, or years of experience. If a job requirement is not evidenced, mark
        it as a gap or as unclear; do not imply the candidate has that skill.

        Return ONLY one valid JSON object with no surrounding Markdown code fences or extra text,
        using exactly these keys:
        {
        "compatibility_percentage": integer from 0 to 100,
        "compatibility_summary": "brief explanation of the score",
        "strengths": ["evidence-backed match", "..."],
        "gaps": [
            {"area": "skill or requirement", "importance": "High|Medium|Low",
            "status": "No evidence|Limited evidence|Unclear",
            "note": "what the candidate has or has not supplied"}
        ],
        "recommendations": ["truthful next step or information to add", "..."]
        }

        Scoring guidance:
        - Score based on the essential responsibilities, required skills, experience level,
        domain knowledge, and qualifications in the job description.
        - Give credit only for evidence in the candidate details.
        - Missing critical requirements should materially reduce the score.
        - Do not treat an omitted detail as proof the candidate lacks the skill; label it
        "No evidence" or "Unclear" rather than asserting they cannot do it.
        - The score is an estimate, not a hiring prediction.
        - Do not generate a resume; output only the JSON feedback assessment.

        """

    user_prompt = f"""
        JOB DESCRIPTION
        ---------------
        {job_description}

        CANDIDATE DETAILS
        -----------------
        {user_details}

        """

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": resume_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        result = response.choices[0].message.content or ""
    except gr.Error:
        raise
    except Exception as exc:
        raise gr.Error(f"Generation failed: {exc}") from exc

    resume = result

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": feedback_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        result = extract_json(response.choices[0].message.content or "")
    except gr.Error:
        raise
    except Exception as exc:
        raise gr.Error(f"Generation failed: {exc}") from exc

    score = max(0, min(100, int(result.get("compatibility_percentage", 0))))
    # resume = str(result.get("resume_markdown", "")).strip()
    # if not resume:
    #     raise gr.Error("The model did not return a resume. Please try again.")
    summary = str(result.get("compatibility_summary", "")).strip()
    strengths = result.get("strengths", [])
    gaps = result.get("gaps", [])
    recommendations = result.get("recommendations", [])

    assessment = f"## Compatibility: {score}%\n\n{summary}\n\n"
    assessment += "## Strong matches\n"
    assessment += "\n".join(f"- {item}" for item in strengths) if strengths else "- No clear matches identified."
    assessment += "\n\n## Areas with limited or no evidence\n"
    if gaps:
        for gap in gaps:
            assessment += (
                f"- **{gap.get('area', 'Unspecified')}** — "
                f"{gap.get('importance', 'Unrated')} priority; "
                f"{gap.get('status', 'Unclear')}. "
                f"{gap.get('note', '')}"
                "\n"
            )
    else:
        assessment += "- No material gaps were identified from the supplied details.\n"
    assessment += "\n## Recommended improvements\n"
    assessment += "\n".join(f"- {item}" for item in recommendations) if recommendations else "- Add any missing evidence or quantified outcomes that can be verified."

    return resume, assessment

APP_TITLE = "CV Studio"
with gr.Blocks(title=APP_TITLE,
               theme=gr.themes.Soft(),
               css="""
                .markdown-output {
                background-color: #ffffff !important;
                border: 1px solid #d1d5db !important;
                border-radius: 8px;
                padding: 20px !important;
                color: #1f2937 !important;
                min-height: 250px;
                }
                """) as app:

    gr.Markdown("""
      <h1 style="
          text-align: center;
          border-bottom: 2px solid #2563eb;
          padding-bottom: 10px;
          margin-bottom: 20px;">
          CV Studio </h1>
      """)

    gr.Markdown(
        """
        Paste a job description and the candidate's background. Generate a truthful,
        ATS-friendly resume with a job-fit estimate and an evidence-based gap analysis.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            job_input = gr.Textbox(
                label="Job description",
                placeholder="Paste the complete job description here...",
                lines=18,
            )
        with gr.Column(scale=1):
            candidate_input = gr.Textbox(
                label="Candidate details",
                placeholder=(
                    "Paste your existing resume, experience, projects, skills, "
                    "education, certifications and achievements here..."
                ),
                lines=18,
            )

    with gr.Row():
        profile_picture = gr.Image(
          label="Professional Profile Picture",
          type="filepath",
          sources=["upload"],
          format="png",
          height=120,
          )
        cv_format = gr.Dropdown(
            choices=["Modern", "Word", "HTML", "Plain Text"],
            value="Modern",  # Default selected value
            label="CV Format",
            interactive=True,
            scale=1,
            )
        generate_btn = gr.Button("Generate tailored resume", variant="primary", scale=1)

    gr.Markdown("""
      <h1 style="
          text-align: center;
          border-bottom: 2px solid #2563eb;
          padding-bottom: 10px;
          margin-bottom: 20px;">
          Job-fit Assessment </h1>
      """)

    gr.Markdown("## Tailored resume")
    resume_output = gr.Markdown(
        value="Your generated resume will appear here.",
        line_breaks=True,
        elem_classes=["markdown-output"],
    )

    gr.Markdown("## Feedback")

    assessment = gr.Markdown(
        value="Your feedback for the provided job description will appear here.",
        line_breaks=True,
        elem_classes=["markdown-output"],
    )

    with gr.Row():
        with gr.Column(scale=1):
            generate_pdf = gr.Button("PDF Download", variant="primary", scale=1)

        with gr.Column(scale=1):
            generate_word = gr.Button("Word Download", variant="primary", scale=1)

    gr.Markdown(
        """
        ---
        **Important:** The compatibility score is an AI-generated estimate based only on
        the information supplied. Review every statement before using the resume.
        Missing information is reported as a lack of evidence, not automatically as a lack
        of ability.
        """
            )

    generate_btn.click(
        fn=generate_resume,
        inputs=[job_input, candidate_input, cv_format],
        outputs=[resume_output, assessment],
        )

app.launch()