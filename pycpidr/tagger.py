import spacy

_nlp = None


def get_nlp():
    """
    Load and return the spaCy English language model.

    Returns:
        spacy.lang.en.English: The loaded spaCy English language model.
    """
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def tag_text(text, nlp=None):
    """
    Perform part-of-speech tagging on the input text.

    Args:
        text (str): The input text to be tagged.
        nlp (spacy.lang.en.English, optional): A pre-loaded spaCy model. If None,
            the default model will be loaded.

    Returns:
        list of tuple: A list of (token, tag) pairs for each token in the input text.
    """
    if nlp is None:
        nlp = get_nlp()

    doc = nlp(text)
    tagged_tokens = [(token.text, token.tag_) for token in doc]

    return tagged_tokens
