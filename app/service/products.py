import json
from  pathlib  import Path
from typing import List,Dict

DATA_FILE = Path(__file__).parent.parent / "data" / "products.json"

def load_products() -> List[Dict[str, any]]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Data file not found at {DATA_FILE}")
    with open(DATA_FILE, "r",encoding="utf-8") as file:
        return json.load(file)

def get_all_products() -> List[Dict[str]]:
    return load_products()