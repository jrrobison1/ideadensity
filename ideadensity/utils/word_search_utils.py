from typing import Callable, List, Optional, Tuple
from ideadensity.word_item import WordListItem
from ideadensity.utils.constants import SENTENCE_END
from Levenshtein import ratio

MAX_LOOKBACK = 10


def beginning_of_sentence(word_list_items: List[WordListItem], i: int) -> int:
    """
    Finds the index of the beginning of the sentence containing the word at index i.

    Args:
        word_list_items (List[WordListItem]): The list of word items to search through.
        i (int): The index of the current word.

    Returns:
        int: The index of the beginning of the sentence, or 0 if not found.
    """
    j = i - 1
    while j > 0 and (
        word_list_items[j].tag != SENTENCE_END and word_list_items[j].tag != ""
    ):
        j -= 1
    return j + 1


def is_repetition(first: str, second: str, threshold: float = 0.8) -> bool:
    """
    Determines whether a word is likely to be a repetition of another using a similarity score.

    Args:
        first (str): The first word (potentially incomplete).
        second (str): The second word to compare against.
        threshold (float): The similarity threshold (0.0 to 1.0) for considering words as repetitions.

    Returns:
        bool: True if the words are considered repetitions, False otherwise.
    """
    if not first or not second:
        return False

    first = first.lower()
    second = second.lower()

    if first == second:
        return True

    # Handle potential incomplete words (e.g., "hesi-" for "hesitation")
    if first.endswith("-"):
        first = first[:-1]
        return second.startswith(first) and len(second) - len(first) <= 6

    # Calculate similarity score
    similarity = ratio(first, second)

    # Check if similarity exceeds threshold and words are not common short words
    return (
        similarity >= threshold
        and len(first) > 3
        and first
        not in ("the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for")
    )


def search_backwards(
    word_list: List[WordListItem], i: int, condition: Callable[[WordListItem], bool]
) -> Optional[WordListItem]:
    """
    Search backwards in the word list for an item that satisfies the given condition.

    Args:
        word_list (List[WordListItem]): The list of word items to search through.
        i (int): The starting index for the backward search.
        condition (Callable[[WordListItem], bool]): A function that takes a WordListItem and returns a boolean.

    Returns:
        Optional[WordListItem]: The first WordListItem that satisfies the condition, or None if not found.

    Note:
        The search stops if it encounters a sentence end or reaches the beginning of the list.
        The search is limited to MAX_LOOKBACK items.
    """
    for j in range(i - 1, max(i - MAX_LOOKBACK, -1), -1):
        prev_word = word_list[j]
        if prev_word.tag == SENTENCE_END or prev_word.tag == "":
            break
        if condition(prev_word):
            return word_list[j]
    return None


