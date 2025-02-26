import spacy
from typing import List, Tuple, Optional

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
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise OSError(
                "The 'en_core_web_sm' model is not installed. Please install it using: `python -m spacy download en_core_web_sm`."
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
