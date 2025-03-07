import os
import pytest
import tempfile
import sys

# Import the function directly for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import read_text_from_file


class TestFileInput:
    def test_read_text_from_file(self):
        # Create a temporary file with test content
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
            test_content = "This is a test file content."
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            # Read text from the file
            result = read_text_from_file(temp_file_path)
            assert result == test_content
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    def test_read_text_from_nonexistent_file(self):
        # Test with a file that doesn't exist
        with pytest.raises(FileNotFoundError):
            read_text_from_file("nonexistent_file.txt")