import os
from pathlib import Path

project_name = "An_Ai"

folders = [
    f"{project_name}/app/routes",
    f"{project_name}/app/services",
    f"{project_name}/app/templates",
    f"{project_name}/static",
]

files = {
    f"{project_name}/run.py": "# Entry point using app factory\n",
    f"{project_name}/requirements.txt": "flask\nflask_sqlalchemy\npython-dotenv\n",
    f"{project_name}/.env": "# SECRET_KEY=your-secret-key\n# DATABASE_URL=sqlite:///app.db\n",
    f"{project_name}/README.md": "# An_Ai - LLM-Powered Notebook App\n",

    f"{project_name}/app/__init__.py": "# Flask app factory and DB init\n",
    f"{project_name}/app/config.py": "# Load configs from .env\n",
    f"{project_name}/app/prompts.py": "# Predefined prompt templates\n",
    f"{project_name}/app/models.py": "# SQLAlchemy models: User, Notebook, Note\n",

    f"{project_name}/app/routes/__init__.py": "# Routes package\n",
    f"{project_name}/app/routes/auth_routes.py": "# Login/logout endpoints\n",
    f"{project_name}/app/routes/note_routes.py": "# Topic -> Prompt -> Answer -> Save\n",

    f"{project_name}/app/services/__init__.py": "# Services package\n",
    f"{project_name}/app/services/llm_service.py": "# GROQ integration logic\n",
    f"{project_name}/app/services/export_service.py": "# Export notes as PDF/Word\n",
    f"{project_name}/app/services/prompt_service.py": "# Dynamic prompt rendering logic\n",

    f"{project_name}/app/templates/login.html": "<!-- Login UI -->\n",
    f"{project_name}/app/templates/select.html": "<!-- Topic/Subtopic Selector -->\n",
    f"{project_name}/app/templates/response.html": "<!-- Rendered LLM Response -->\n",
    f"{project_name}/app/templates/notebook.html": "<!-- User Notebook Page -->\n",
}

def create_structure():
    print(f"\n📁 Creating project: {project_name}")
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✅ Created folder: {folder}")

    for path, content in files.items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        print(f"📄 Created file: {path}")

    print("\n🎉 Project structure for 'An_Ai' created successfully!")

if __name__ == "__main__":
    create_structure()
