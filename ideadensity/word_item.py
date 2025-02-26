from typing import List, Tuple


class WordListItem:
    """
    Represents a single word or token in a text, along with its properties.

    Attributes:
        token (str): The actual word or token.
        tag (str): The part-of-speech tag for the token.
        is_word (bool): Indicates if the token is considered a word.
        is_prop (bool): Indicates if the token is considered a proposition.
        rule_number (int): The number of the rule that was applied to this token in determining if is a proposition.
    """

    def __init__(
        self,
        token: str = "",
        tag: str = "",
        is_word: bool = False,
        is_proposition: bool = False,
        rule_number: int = 0,
    ):
        self.token = token
        self.tag = tag
        self.is_word = is_word
        self.is_proposition = is_proposition
        self.rule_number = rule_number
        self.lowercase_token = token.lower()


class WordList:
    """
    Represents a list of WordListItems, typically corresponding to a full text.

    This class is responsible for creating and storing WordListItems based on
    tagged text input.

    Attributes:
        items (List[WordListItem]): The list of WordListItems.
    """

    DEFAULT_ITEM_COUNT = 10

    def __init__(self, tagged_text: List[Tuple[str, str]]):
        """
        Initializes a WordList from tagged text.

        Args:
            tagged_text (List[Tuple[str, str]]): A list of (word, tag) tuples.

        If tagged_text is empty, initializes with DEFAULT_ITEM_COUNT empty WordListItems.
        Otherwise, creates a WordListItem for each word in the tagged text.
        """
        self.items = [WordListItem()] * self.DEFAULT_ITEM_COUNT
        for tagged_word in tagged_text:
            self.items.append(
                WordListItem(tagged_word[0], tagged_word[1], False, False, 0)
            )
