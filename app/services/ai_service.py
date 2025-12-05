from app.config import settings
from typing import Optional
import openai


def summarize_text(text: str, max_length: int = 100) -> Optional[str]:
    """
    Summarize text using OpenAI API.
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary
        
    Returns:
        Summary string or None if API key is not set
    """
    if not settings.openai_api_key:
        return None
    
    try:
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Summarize the following text in {max_length} words or less:"},
                {"role": "user", "content": text}
            ],
            max_tokens=max_length,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return None

