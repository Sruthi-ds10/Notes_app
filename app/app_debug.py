from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from io import BytesIO
from fpdf import FPDF
from models import db, User, Topic, Subtopic, Notebook, Note, CustomPrompt
from services.llm_service import generate_llm_response
import os
import glob
import unicodedata
import pandas as pd

# ------------------------
# App Config
# ------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, '../instance/app.db')}"
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# ------------------------
# Login Manager
# ------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------
# Routes
# ------------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# ------------------------
# Authentication
# ------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('select'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['email'].split('@')[0]
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
        else:
            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

# ------------------------
# Topic Selection & Prompt Page
# ------------------------
@app.route('/select')
@login_required
def select():
    topics = Topic.query.all()
    prompt_dir = os.path.join(basedir, 'prompts/templates/')
    prompt_types = []
    if os.path.exists(prompt_dir):
        prompt_files = glob.glob(os.path.join(prompt_dir, '*.txt'))
        prompt_types = [os.path.splitext(os.path.basename(p))[0] for p in prompt_files]
    custom_prompts = CustomPrompt.query.filter_by(user_id=current_user.id).all()
    return render_template('select.html', topics=topics, prompt_types=prompt_types, custom_prompts=custom_prompts)

# ------------------------
# API: Get Subtopics
# ------------------------
@app.route('/api/subtopics/<int:topic_id>')
@login_required
def get_subtopics(topic_id):
    subtopics = Subtopic.query.filter_by(topic_id=topic_id).all()
    return jsonify({"subtopics": [{"id": s.id, "name": s.name} for s in subtopics]})

# ------------------------
# Excel Upload for Topics & Subtopics
# ------------------------
ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_excel', methods=['POST'])
@login_required
def upload_excel():
    if 'excel_file' not in request.files:
        flash('No file part')
        return redirect(url_for('select'))

    file = request.files['excel_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('select'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(basedir, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        try:
            df = pd.read_excel(filepath)

            if 'Topic' not in df.columns or 'Subtopic' not in df.columns:
                flash('Excel must have columns: Topic and Subtopic')
                return redirect(url_for('select'))

            Subtopic.query.delete()
            Topic.query.delete()
            db.session.commit()

            for _, row in df.iterrows():
                topic_name = str(row['Topic']).strip()
                subtopic_name = str(row['Subtopic']).strip()
                if not topic_name or not subtopic_name:
                    continue

                topic = Topic.query.filter_by(name=topic_name).first()
                if not topic:
                    topic = Topic(name=topic_name)
                    db.session.add(topic)
                    db.session.flush()

                subtopic = Subtopic(name=subtopic_name, topic_id=topic.id)
                db.session.add(subtopic)

            db.session.commit()
            flash('Topics and Subtopics updated successfully!')
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    return redirect(url_for('select'))

# ------------------------
# Generate Answer
# ------------------------
@app.route('/generate', methods=['POST'])
@login_required
def generate():
    topic_id = request.form['topic_id']
    subtopic_id = request.form['subtopic_id']
    prompt_type = request.form.get('prompt_type', '').strip()
    custom_prompt = request.form.get('custom_prompt', '').strip()
    llm_provider = request.form.get('llm_provider', 'openai').lower()
    llm_api_key = request.form.get('llm_api_key', '').strip()

    # ✅ Validate LLM Provider
    if llm_provider not in ['openai', 'groq']:
        flash("Invalid LLM provider selected. Please choose OpenAI or Groq.")
        return redirect(url_for('select'))

    topic = Topic.query.get(topic_id)
    subtopic = Subtopic.query.get(subtopic_id)

    if not topic or not subtopic:
        flash("Invalid topic or subtopic selected.")
        return redirect(url_for('select'))

    if not prompt_type and not custom_prompt:
        flash("Please select an answer type or enter a custom prompt.")
        return redirect(url_for('select'))

    if prompt_type and not custom_prompt:
        prompt_path = os.path.join(basedir, f'prompts/templates/{prompt_type}.txt')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            template = f"[Error] Prompt file '{prompt_type}.txt' not found."

        filled_prompt = (
            template.replace("{{topic}}", topic.name)
                    .replace("{{subtopic}}", subtopic.name)
        )

        full_prompt = f"""
You are an AI tutor explaining a concept.

Topic: {topic.name}
Subtopic: {subtopic.name}
Answer Type: {prompt_type}

Explain clearly in plain text (no markdown, no bullet points).

Prompt:
{filled_prompt}
""".strip()

    else:
        full_prompt = f"""
You are an AI assistant.

Topic: {topic.name}
Subtopic: {subtopic.name}
Instruction: {custom_prompt}

Answer in plain English (paragraph style, no formatting).
""".strip()

        existing_prompt = CustomPrompt.query.filter_by(prompt_text=custom_prompt, user_id=current_user.id).first()
        if not existing_prompt:
            custom_prompt_entry = CustomPrompt(prompt_text=custom_prompt, answer_type="custom", user_id=current_user.id)
            db.session.add(custom_prompt_entry)
            db.session.commit()
        prompt_type = "custom"

    llm_response = generate_llm_response(full_prompt, provider=llm_provider, api_key=llm_api_key)

    if 'responses' not in session:
        session['responses'] = []
    session['responses'].append(llm_response)
    session['response_index'] = len(session['responses']) - 1

    session.update({
        'topic': topic.name,
        'subtopic': subtopic.name,
        'answer_type': prompt_type,
        'last_prompt': full_prompt
    })

    return render_template(
        'response.html',
        response=llm_response,
        topic=topic.name,
        subtopic=subtopic.name,
        answer_type=prompt_type,
        editable_prompt='',
        has_previous=len(session['responses']) > 1
    )

# ------------------------
# Regenerate Custom Prompt
# ------------------------
@app.route('/regenerate_custom', methods=['POST'])
@login_required
def regenerate_custom():
    custom_prompt_input = request.form.get('custom_prompt', '').strip()
    last_prompt = custom_prompt_input if custom_prompt_input else session.get('last_prompt', '')

    if not last_prompt:
        flash("No prompt available to regenerate.")
        return redirect(url_for('select'))

    llm_provider = request.form.get('llm_provider', 'openai').lower()
    llm_api_key = request.form.get('llm_api_key', '').strip()

    llm_response = generate_llm_response(last_prompt, provider=llm_provider, api_key=llm_api_key)

    if 'responses' not in session:
        session['responses'] = []
    session['responses'].append(llm_response)
    session['response_index'] = len(session['responses']) - 1
    session['last_prompt'] = last_prompt

    return render_template(
        'response.html',
        response=llm_response,
        topic=session['topic'],
        subtopic=session['subtopic'],
        answer_type=session['answer_type'],
        editable_prompt=last_prompt,
        has_previous=session['response_index'] > 0
    )

# ------------------------
# Word Explanation
# ------------------------
@app.route('/word_explanation', methods=['POST'])
@login_required
def word_explanation():
    word = request.form.get('word', '').strip()
    if not word:
        flash("Please enter a word to explain.")
        return redirect(url_for('select'))

    prompt = f"Explain the meaning of the word '{word}' in simple terms, with an example in one sentence."
    llm_response = generate_llm_response(prompt, provider='openai')

    return render_template(
        'response.html',
        response=llm_response,
        topic=session.get('topic', 'N/A'),
        subtopic=session.get('subtopic', 'N/A'),
        answer_type="Word Explanation",
        editable_prompt='',
        has_previous=False
    )

# ------------------------
# Previous & Next Response
# ------------------------
@app.route('/previous_response')
@login_required
def previous_response():
    if 'responses' in session and session['response_index'] > 0:
        session['response_index'] -= 1
    return render_template(
        'response.html',
        response=session['responses'][session['response_index']],
        topic=session['topic'],
        subtopic=session['subtopic'],
        answer_type=session['answer_type'],
        editable_prompt=session.get('last_prompt', ''),
        has_previous=session['response_index'] > 0
    )

@app.route('/next_response')
@login_required
def next_response():
    if 'responses' in session and session['response_index'] < len(session['responses']) - 1:
        session['response_index'] += 1
    return render_template(
        'response.html',
        response=session['responses'][session['response_index']],
        topic=session['topic'],
        subtopic=session['subtopic'],
        answer_type=session['answer_type'],
        editable_prompt=session.get('last_prompt', ''),
        has_previous=session['response_index'] > 0
    )

# ------------------------
# Notebook & Download
# ------------------------
@app.route('/save', methods=['POST'])
@login_required
def save():
    content = request.form['note']
    topic = Topic.query.filter_by(name=session['topic']).first()
    subtopic = Subtopic.query.filter_by(name=session['subtopic']).first()
    notebook = Notebook.query.filter_by(user_id=current_user.id).first()
    if not notebook:
        notebook = Notebook(title='Default', user_id=current_user.id)
        db.session.add(notebook)
        db.session.commit()
    note = Note(
        content=content,
        topic_id=topic.id if topic else None,
        subtopic_id=subtopic.id if subtopic else None,
        note_type=session.get('answer_type'),
        notebook_id=notebook.id
    )
    db.session.add(note)
    db.session.commit()
    flash("Note saved to your notebook.")
    return redirect(url_for('notebook'))

@app.route('/notebook')
@login_required
def notebook():
    notebook = Notebook.query.filter_by(user_id=current_user.id).first()
    notes = notebook.notes if notebook else []
    return render_template('notebook.html', notebook=notes)

@app.route('/download/<filetype>')
@login_required
def download(filetype):
    notebook = Notebook.query.filter_by(user_id=current_user.id).first()
    notes = notebook.notes if notebook else []
    if not notes:
        flash('No notes available to download.')
        return redirect(url_for('notebook'))

    content = "\n\n---\n\n".join(note.content for note in notes)

    if filetype == 'txt':
        return send_file(BytesIO(content.encode('utf-8')), mimetype='text/plain', as_attachment=True, download_name='notebook.txt')

    elif filetype == 'pdf':
        clean_content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore').decode('ascii')
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in clean_content.split('\n'):
            pdf.multi_cell(0, 10, txt=line)
        pdf_output = pdf.output(dest='S').encode('latin1')
        pdf_bytes = BytesIO(pdf_output)
        return send_file(pdf_bytes, mimetype='application/pdf', as_attachment=True, download_name='notebook.pdf')

    else:
        flash("Unsupported format")
        return redirect(url_for('notebook'))

# ------------------------
# App Start
# ------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)  