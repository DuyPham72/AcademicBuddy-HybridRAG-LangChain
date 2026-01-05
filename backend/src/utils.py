import yaml
import os

def load_prompts():
    """
    Loads the prompts.yaml file from the config directory.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "config", "prompts.yaml")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompts file not found at: {path}")

    with open(path, "r") as f:
        return yaml.safe_load(f)