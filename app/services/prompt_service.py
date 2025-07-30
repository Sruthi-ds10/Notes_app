import os

# Dynamically resolve the path to `prompts/templates/`
TEMPLATE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "prompts", "templates")
)

def load_prompt_template(prompt_type, topic, subtopic, user_feedback=""):
    """
    Load the prompt template for a given type and fill in placeholders.

    Args:
        prompt_type (str): Type of prompt (e.g., "definition", "interview")
        topic (str): Selected topic
        subtopic (str): Selected subtopic
        user_feedback (str): Optional feedback from user for regeneration

    Returns:
        str: Rendered prompt or error message
    """
    file_path = os.path.join(TEMPLATE_DIR, f"{prompt_type}.txt")

    if not os.path.exists(file_path):
        return f"❌ Prompt template for '{prompt_type}' not found at {file_path}"

    with open(file_path, "r", encoding="utf-8") as file:
        template = file.read()

    # Replace placeholders safely
    return (
        template.replace("{{topic}}", topic)
                .replace("{{subtopic}}", subtopic)
                .replace("{{user_feedback}}", user_feedback)
    )
