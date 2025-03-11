import csv
import os
from typing import List, Tuple, Any, TextIO, Dict, Optional

from ideadensity.word_item import WordListItem, WordList
from ideadensity.utils.version_utils import VERSION, get_spacy_version_info


def export_cpidr_to_csv(word_list: WordList, filepath: str) -> None:
    """
    Export token details from CPIDR analysis to a CSV file

    Args:
        word_list: The WordList containing token details
        filepath: Path where CSV file should be saved
    """
    # Ensure directory exists
    os.makedirs(
        os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True
    )

    # Define the header for the CSV file
    headers = ["Token", "Tag", "Is Word", "Is Proposition", "Rule Number"]

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        # Write data rows
        for item in word_list.items:
            # Skip empty items (those initialized with default constructor)
            if not item.token and not item.tag:
                continue

            writer.writerow(
                [
                    item.token,
                    item.tag,
                    item.is_word,
                    item.is_proposition,
                    item.rule_number if item.is_proposition else "",
                ]
            )


def export_depid_to_csv(dependencies: List[Tuple[Any, ...]], filepath: str) -> None:
    """
    Export token details from DEPID analysis to a CSV file

    Args:
        dependencies: The list of dependency tuples (token, dependency, head)
        filepath: Path where CSV file should be saved
    """
    # Ensure directory exists
    os.makedirs(
        os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True
    )

    # Define the header for the CSV file
    headers = ["Token", "Dependency", "Head"]

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        # Write data rows
        for dep in dependencies:
            writer.writerow(dep)


def export_cpidr_to_txt(
    word_list: WordList,
    text: str,
    word_count: int,
    proposition_count: int,
    density: float,
    filepath: str,
    filename: str = None,
) -> None:
    """
    Export CPIDR results to a text file in CPIDR-compatible format

    Args:
        word_list: The WordList containing token details
        text: Original analyzed text
        word_count: Number of words counted
        proposition_count: Number of propositions counted
        density: The idea density score
        filepath: Path where text file should be saved
        filename: Optional filename to display in the export header (for file mode)
    """
    # Ensure directory exists
    os.makedirs(
        os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True
    )

    with open(filepath, "w", encoding="utf-8") as txtfile:
        # Header with ideadensity version and spaCy info
        spacy_version, model_name, model_version = get_spacy_version_info()
        txtfile.write(f"ideadensity {VERSION}\n")
        txtfile.write(
            f"Using spaCy {spacy_version}, {model_name} {model_version}\n\n\n"
        )

        # Original text or filename (wrapped in quotes)
        if filename:
            txtfile.write(f'"{filename}"\n')
        else:
            txtfile.write(f'"{text[:50]}..."\n')

        # Token details
        for i, item in enumerate(word_list.items):
            # Skip empty tokens (those initialized with default constructor)
            if not item.token and not item.tag:
                continue

            # Format rule number (use spaces if 0)
            try:
                # Try to convert to int first to handle numeric rule numbers
                rule_num = (
                    str(int(item.rule_number)).zfill(3) if item.rule_number else "   "
                )
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


def export_cpidr_multiple_files_to_txt(
    file_word_lists: List[WordList],
    file_names: List[str],
    filepath: str,
) -> None:
    """
    Export CPIDR results for multiple files to a text file in CPIDR-compatible format

    Args:
        file_word_lists: List of WordLists containing token details for each file
        file_names: List of filenames corresponding to each WordList
        filepath: Path where text file should be saved
    """
    # Ensure directory exists
    os.makedirs(
        os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True
    )

    with open(filepath, "w", encoding="utf-8") as txtfile:
        # Header with ideadensity version and spaCy info
        spacy_version, model_name, model_version = get_spacy_version_info()
        txtfile.write(f"ideadensity {VERSION}\n")
        txtfile.write(
            f"Using spaCy {spacy_version}, {model_name} {model_version}\n\n\n"
        )

        # Process each file
        for i, (word_list, filename) in enumerate(zip(file_word_lists, file_names)):
            # Add separation between files
            if i > 0:
                txtfile.write("\n\n\n")
            
            # Filename header
            txtfile.write(f'"{filename}"\n')
            
            # Word count and proposition count for this file
            word_count = sum(1 for item in word_list.items if item.is_word)
            proposition_count = sum(1 for item in word_list.items if item.is_proposition)
            
            # Calculate density
            density = 0.0
            if word_count > 0:
                density = proposition_count / word_count
            
            # Token details
            for item in word_list.items:
                # Skip empty tokens (those initialized with default constructor)
                if not item.token and not item.tag:
                    continue

                # Format rule number (use spaces if 0)
                try:
                    # Try to convert to int first to handle numeric rule numbers
                    rule_num = (
                        str(int(item.rule_number)).zfill(3) if item.rule_number else "   "
                    )
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

            # Summary section for this file
            txtfile.write("\n\n")
            txtfile.write(f"     {proposition_count} propositions\n")
            txtfile.write(f"     {word_count} words\n")
            txtfile.write(f" {density:.3f} density\n")
