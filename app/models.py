from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    notebooks = db.relationship('Notebook', backref='user', lazy=True)
    custom_prompts = db.relationship('CustomPrompt', backref='user', lazy=True)  # new

    def __repr__(self):
        return f"<User {self.username}>"


class Topic(db.Model):
    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    subtopics = db.relationship('Subtopic', backref='topic', lazy=True)

    def __repr__(self):
        return f"<Topic {self.name}>"


class Subtopic(db.Model):
    __tablename__ = 'subtopics'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)

    def __repr__(self):
        return f"<Subtopic {self.name}>"


class Notebook(db.Model):
    __tablename__ = 'notebooks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    notes = db.relationship('Note', backref='notebook', lazy=True)

    def __repr__(self):
        return f"<Notebook {self.title}>"


class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    subtopic_id = db.Column(db.Integer, db.ForeignKey('subtopics.id'), nullable=True)
    note_type = db.Column(db.String(50))  # summary, explanation, code
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebooks.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<Note {self.note_type} - {self.created_at}>"

class CustomPrompt(db.Model):
    __tablename__ = 'custom_prompts'

    id = db.Column(db.Integer, primary_key=True)
    prompt_name = db.Column(db.String(100), nullable=False)  # ✅ Add this line
    prompt_text = db.Column(db.Text, nullable=False)
    answer_type = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return f"<CustomPrompt {self.prompt_name} - {self.answer_type}>"




