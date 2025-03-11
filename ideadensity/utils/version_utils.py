import importlib.metadata
import tomli
from pathlib import Path
import spacy

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

def get_spacy_version_info():
    """Get the spaCy version and model information.
    
    Returns:
        tuple: (spacy_version, model_name, model_version)
    """
    spacy_version = spacy.__version__
    try:
        nlp = spacy.load("en_core_web_sm")
        model_name = "en_core_web_sm"
        model_version = nlp.meta["version"]
    except:
        model_name = "en_core_web_sm"
        model_version = "not loaded"
    
    return spacy_version, model_name, model_version