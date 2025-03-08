import csv
import os
import importlib.metadata
import tomli
from typing import Callable, List, Optional, Tuple, Any, TextIO
from pathlib import Path

from ideadensity.word_item import WordListItem, WordList
from ideadensity.utils.constants import SENTENCE_END
from Levenshtein import ratio

# Try to get package version from pyproject.toml
try:
    # First, try to get the version from the package metadata
    VERSION = importlib.metadata.version("ideadensity")
except importlib.metadata.PackageNotFoundError:
    # If that fails, try to find and read pyproject.toml
    try:
        current_dir = Path(__file__).resolve().parent
        # Search up to 3 levels up from current file to find pyproject.toml
        for _ in range(4):  # current dir + 3 levels up
            pyproject_path = current_dir / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomli.load(f)
                VERSION = pyproject_data.get("tool", {}).get("poetry", {}).get("version", "unknown")
                break
            current_dir = current_dir.parent
        else:
            VERSION = "unknown"  # If we can't find pyproject.toml
    except Exception:
        VERSION = "unknown"  # Fallback in case of any issues

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


def export_cpidr_to_csv(word_list: WordList, filepath: str) -> None:
    """
    Export token details from CPIDR analysis to a CSV file

    Args:
        word_list: The WordList containing token details
        filepath: Path where CSV file should be saved
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    
    # Define the header for the CSV file
    headers = ['Token', 'Tag', 'Is Word', 'Is Proposition', 'Rule Number']
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        
        # Write data rows
        for item in word_list.items:
            # Skip empty items (those initialized with default constructor)
            if not item.token and not item.tag:
                continue
                
            writer.writerow([
                item.token,
                item.tag,
                item.is_word,
                item.is_proposition,
                item.rule_number if item.is_proposition else ''
            ])


def export_depid_to_csv(dependencies: List[Tuple[Any, ...]], filepath: str) -> None:
    """
    Export token details from DEPID analysis to a CSV file

    Args:
        dependencies: The list of dependency tuples (token, dependency, head)
        filepath: Path where CSV file should be saved
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    
    # Define the header for the CSV file
    headers = ['Token', 'Dependency', 'Head']
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        
        # Write data rows
        for dep in dependencies:
            writer.writerow(dep)


def export_cpidr_to_txt(word_list: WordList, text: str, word_count: int, proposition_count: int, 
                      density: float, filepath: str) -> None:
    """
    Export CPIDR results to a text file in CPIDR-compatible format

    Args:
        word_list: The WordList containing token details
        text: Original analyzed text
        word_count: Number of words counted
        proposition_count: Number of propositions counted
        density: The idea density score
        filepath: Path where text file should be saved
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as txtfile:
        # Header with ideadensity version
        txtfile.write(f"ideadensity {VERSION}\n\n\n\n")
        
        # Original text (wrapped in quotes)
        txtfile.write(f'"{text[:50]}..."\n')
        
        # Token details
        for i, item in enumerate(word_list.items):
            # Skip empty tokens (those initialized with default constructor)
            if not item.token and not item.tag:
                continue
                
            # Format rule number (use spaces if 0)
            try:
                # Try to convert to int first to handle numeric rule numbers
                rule_num = str(int(item.rule_number)).zfill(3) if item.rule_number else "   "
            except (ValueError, TypeError):
                # If rule_number is not convertible to int, use "   "
                rule_num = "   "
            
            # Format is_word flag
            is_word_flag = "W" if item.is_word else " "
            
            # Format is_proposition flag
            is_prop_flag = "P" if item.is_proposition else " "
            
            # Format the line according to CPIDR format
            line = f" {rule_num} {item.tag:<4} {is_word_flag} {is_prop_flag} {item.token}\n"
            txtfile.write(line)
        
        # Summary section
        txtfile.write("\n\n")
        txtfile.write(f"     {proposition_count} propositions\n")
        txtfile.write(f"     {word_count} words\n")
        txtfile.write(f" {density:.3f} density\n")
