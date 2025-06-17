from flask import Flask, request, send_file, render_template, jsonify
from dotenv import load_dotenv
from openai import OpenAI
from docx import Document
from docx.shared import Pt
from io import BytesIO
from datetime import date
import random
import os
import re

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

affirmations = [
    "Action is the foundational key to all success. – Pablo Picasso",
    "Small steps lead to big results.",
    "Discipline is choosing what you want most over what you want now.",
    "You don’t need more time. You need more focus.",
    "Start before you’re ready. Progress beats perfection.",
    "The cost of procrastination is the life you could have lived.",
    "Show up. Do the work. Trust the process.",
    "Your future is created by what you do today, not tomorrow.",
    "Consistency beats intensity every time.",
    "One focused hour today beats ten distracted ones tomorrow."
]

@app.route("/")
def home():
    return render_template("weekly.html")

@app.route("/daily")
def daily():
    return render_template("daily.html")

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route("/generate_daily", methods=["POST"])
def generate_daily():
    data = request.json
    goal = data.get("goal")
    export = data.get("export", False)

    prompt = f"""
Break this goal into 3–5 labeled objectives. Under each, list 2–4 small, clearly written tasks to complete.
Do not number or label the tasks. Do not include the phrase "Task A" etc.
Bold the objective titles only. Use this exact format:

Objective: Research Blog Topics
- Brainstorm 10 post ideas
- Analyze Google trends
- Choose 2 topics to write today

Goal: {goal}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content.strip()
    sections = raw.split("\n")
    parsed = []
    current_obj = None

    for line in sections:
        line = line.strip().replace("**", "")
        if not line:
            continue
        if line.lower().startswith("objective:"):
            if current_obj:
                parsed.append(current_obj)
            current_obj = {"objective": line.split(":", 1)[1].strip(), "tasks": []}
        elif line.startswith("- ") and current_obj:
            task_text = re.sub(r"^Task [A-Z]:\s*", "", line[2:].strip())
            current_obj["tasks"].append(task_text)

    if current_obj:
        parsed.append(current_obj)

    affirmation = random.choice(affirmations)

    if not export:
        return jsonify({
            "date": date.today().strftime("%B %d, %Y"),
            "goal": goal,
            "objectives": parsed,
            "affirmation": affirmation
        })

    # Generate Word doc
    doc = Document()
    doc.add_heading("\U0001F4C5 Stratify Daily Planner", 0)

    today = date.today().strftime("%B %d, %Y")
    date_paragraph = doc.add_paragraph(today)
    date_paragraph.runs[0].font.size = Pt(9)

    doc.add_paragraph(f"\n\U0001F3AF Today's Goal:\n{goal}", style='Intense Quote')

    tight_style = doc.styles.add_style('TightList', 1)
    tight_style.font.name = 'Calibri'
    tight_style.font.size = Pt(11)
    tight_para_format = tight_style.paragraph_format
    tight_para_format.space_before = Pt(2)
    tight_para_format.space_after = Pt(2)
    tight_para_format.line_spacing = 1.0

    for item in parsed:
        doc.add_paragraph("——————", style='TightList')
        p = doc.add_paragraph(item['objective'], style='TightList')
        p.runs[0].bold = True
        for task in item["tasks"]:
            doc.add_paragraph(f"☐ {task}", style='TightList')

    doc.add_paragraph("\n\U0001F4AC Affirmation of the Day:", style='TightList')
    doc.add_paragraph(affirmation, style='TightList')
    doc.add_paragraph("\nBuilt with precision by Stratify – Tactical Planning, Simplified.").runs[0].font.size = Pt(9)

    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)

    return send_file(
        file_stream,
        as_attachment=True,
        download_name="Stratify_Daily_Plan.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@app.route("/generate_weekly", methods=["POST"])
def generate_weekly():
    data = request.json
    goal = data.get("goal")
    export = data.get("export", False)

    prompt = f"""
Break this weekly goal into 3–5 labeled objectives. Assign them to specific days of the week (Mon–Sun).
Each day should contain 1 objective and 2–4 small, clearly written tasks. Do not number or label the tasks.
Format clearly like:

Monday – Objective: Title
- Task
- Task

Goal: {goal}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    breakdown = response.choices[0].message.content.strip()

    weekly_plan = []
    current_day = None
    for line in breakdown.split("\n"):
        line = line.strip().replace("**", "")
        if not line:
            continue
        match = re.match(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*–\s*Objective:\s*(.+)", line)
        if match:
            if current_day:
                weekly_plan.append(current_day)
            current_day = {"day": match.group(1), "objective": match.group(2), "tasks": []}
        elif line.startswith("- ") and current_day:
            task_text = re.sub(r"^Task [A-Z]:\s*", "", line[2:].strip())
            current_day["tasks"].append(task_text)
    if current_day:
        weekly_plan.append(current_day)

    affirmation = random.choice(affirmations)

    if not export:
        return jsonify({
            "date": date.today().strftime("%B %d, %Y"),
            "goal": goal,
            "weekly_plan": weekly_plan,
            "affirmation": affirmation
        })

    # Generate Word doc
    doc = Document()
    doc.add_heading("\U0001F9E0 Stratify Weekly Planner", 0)

    today = date.today().strftime("%B %d, %Y")
    date_paragraph = doc.add_paragraph(today)
    date_paragraph.runs[0].font.size = Pt(9)

    doc.add_paragraph(f"\n\U0001F3AF Weekly Goal:\n{goal}", style='Intense Quote')

    tight_style = doc.styles.add_style('TightList', 1)
    tight_style.font.name = 'Calibri'
    tight_style.font.size = Pt(11)
    tight_para_format = tight_style.paragraph_format
    tight_para_format.space_before = Pt(2)
    tight_para_format.space_after = Pt(2)
    tight_para_format.line_spacing = 1.0

    for item in weekly_plan:
        doc.add_paragraph("——————", style='TightList')
        p = doc.add_paragraph(f"{item['day']} – {item['objective']}", style='TightList')
        p.runs[0].bold = True
        for task in item["tasks"]:
            doc.add_paragraph(f"☐ {task}", style='TightList')

    doc.add_paragraph("\n\U0001F4AC Affirmation of the Week:", style='TightList')
    doc.add_paragraph(affirmation, style='TightList')
    doc.add_paragraph("\nBuilt with precision by Stratify – Tactical Planning, Simplified.").runs[0].font.size = Pt(9)

    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)

    return send_file(
        file_stream,
        as_attachment=True,
        download_name="Stratify_Weekly_Plan.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
