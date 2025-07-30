import os
from dotenv import load_dotenv

load_dotenv()

# Default values from environment (fallback)
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
DEFAULT_OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_GROQ_KEY = os.getenv("GROQ_API_KEY", "")
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

def generate_llm_response(prompt, provider=None, api_key=None, model=None, temperature=0.7):
    """
    Generate response from LLM dynamically based on provider and API key.

    :param prompt: User prompt text
    :param provider: 'openai' or 'groq' (default from env)
    :param api_key: API key provided by user (or fallback from env)
    :param model: Specific model (optional)
    :param temperature: Response randomness
    :return: LLM response text or error message
    """
    provider = (provider or DEFAULT_PROVIDER).lower()

    # ✅ Validate provider again as a safety net
    if provider not in ["openai", "groq"]:
        return "❌ Invalid provider. Only 'openai' or 'groq' are supported."

    # ✅ Pick correct key from user input or environment
    api_key = api_key or (DEFAULT_OPENAI_KEY if provider == "openai" else DEFAULT_GROQ_KEY)

    if not api_key:
        return f"❌ Missing API key for {provider.capitalize()}. Please provide it in the form or .env file."

    try:
        if provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            final_model = model or DEFAULT_OPENAI_MODEL

        elif provider == "groq":
            from groq import Groq
            client = Groq(api_key=api_key)
            final_model = model or DEFAULT_GROQ_MODEL

        # ✅ Make the request
        response = client.chat.completions.create(
            model=final_model,
            messages=[
                {"role": "system", "content": "You are an expert AI tutor. Explain clearly in simple terms."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=1200,
        )

        # ✅ Extract response text safely
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"❌ LLM Error: Unable to generate response. Details: {str(e)}"
