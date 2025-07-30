from flask import Blueprint, render_template, request, flash, redirect, send_file, jsonify, Response
from flask_login import login_required, current_user
from app.models import db, Topic, Subtopic, Note, Notebook
from app.services.prompt_service import load_prompt_template
from app.services.llm_service import generate_llm_response
from fpdf import FPDF
import os
from io import BytesIO

note_bp = Blueprint('note', __name__)

@note_bp.route("/select", methods=["GET"])
@login_required
def select():
    topics = Topic.query.order_by(Topic.name).all()
    return render_template("select.html", topics=topics)

@note_bp.route("/generate", methods=["POST"])
@login_required
def generate_note():
    topic_id = request.form.get("topic_id")
    subtopic_id = request.form.get("subtopic_id")
    prompt_type = request.form.get("prompt_type")

    topic = Topic.query.get(topic_id)
    subtopic = Subtopic.query.get(subtopic_id)

    if not topic or not subtopic:
        flash("❌ Invalid topic or subtopic.", "danger")
        return redirect("/select")

    prompt = load_prompt_template(prompt_type, topic.name, subtopic.name)
    response = generate_llm_response(prompt)

    # Save to DB
    notebook = Notebook.query.filter_by(user_id=current_user.id).first()
    if not notebook:
        notebook = Notebook(user_id=current_user.id)
        db.session.add(notebook)
        db.session.commit()

    note = Note(topic_id=topic.id, subtopic_id=subtopic.id, content=response, notebook_id=notebook.id)
    db.session.add(note)
    db.session.commit()

    return render_template("note_result.html", note=note, topic=topic.name, subtopic=subtopic.name)

@note_bp.route("/download/<int:note_id>/<string:filetype>")
@login_required
def download_note(note_id, filetype):
    note = Note.query.get(note_id)

    if not note or note.notebook.user_id != current_user.id:
        flash("❌ Note not found or access denied.", "danger")
        return redirect("/select")

    filename = f"{note.topic.name}_{note.subtopic.name}.{filetype}"
    
    if filetype == "txt":
        content = note.content
        return Response(
            content,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )

    elif filetype == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for line in note.content.splitlines():
            pdf.multi_cell(0, 10, line)

        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        return send_file(
            pdf_output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )

    else:
        flash("❌ Unsupported file type.", "danger")
        return redirect("/select")

@note_bp.route("/api/subtopics/<int:topic_id>", methods=["GET"])
@login_required
def get_subtopics(topic_id):
    subtopics = Subtopic.query.filter_by(topic_id=topic_id).order_by(Subtopic.name).all()
    return jsonify({
        "subtopics": [{"id": s.id, "name": s.name} for s in subtopics]
    })
