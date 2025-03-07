import spacy
import os
import sys
from typing import List, Tuple, Optional
import pkg_resources
from pathlib import Path

_nlp = None


def get_nlp():
    """
    Load and return the spaCy English language model.

    Returns:
        spacy.lang.en.English: The loaded spaCy English language model.
    """
    global _nlp
    if _nlp is None:
        try:
            # First try: regular loading
            try:
                _nlp = spacy.load("en_core_web_sm")
                return _nlp
            except OSError:
                pass  # Continue to other methods
                
            # Second try: If running as a frozen application
            if getattr(sys, 'frozen', False):
                # Look in various locations relative to the executable
                base_dir = os.path.dirname(sys.executable)
                for possible_path in [
                    os.path.join(base_dir, "en_core_web_sm"),
                    os.path.join(base_dir, "en_core_web_sm", "en_core_web_sm"),
                    os.path.join(os.path.dirname(base_dir), "en_core_web_sm"),
                    # Try looking in the pyinstaller _MEIPASS directory
                    os.path.join(getattr(sys, '_MEIPASS', base_dir), "en_core_web_sm")
                ]:
                    if os.path.exists(possible_path):
                        print(f"Found model at: {possible_path}")
                        _nlp = spacy.load(possible_path)
                        return _nlp
                        
            # If we got here, we couldn't find the model
            raise OSError("Model not found")
        except Exception as e:
            raise OSError(
                f"The 'en_core_web_sm' model is not installed or accessible. Error: {str(e)}"
                "\nPlease install it using: `python -m spacy download en_core_web_sm`."
            )
    return _nlp


def tag_text(
    text: str, nlp: Optional[spacy.language.Language] = None
) -> List[Tuple[str, str]]:
    """
    Perform part-of-speech tagging on the input text.

    Args:
        text (str): The input text to be tagged.
        nlp (Optional[spacy.language.Language]): A pre-loaded spaCy model. If None,
            the default model will be loaded.

    Returns:
        List[Tuple[str, str]]: A list of (token, tag) pairs for each token in the input text.
    """
    if not isinstance(text, str):
        raise TypeError("Input text must be a string.")

    if nlp is None:
        nlp = get_nlp()

    doc = nlp(text)
    tagged_tokens = [(token.text, token.tag_) for token in doc]

    return tagged_tokens
