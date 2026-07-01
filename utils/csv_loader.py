# utils/csv_loader.py
import pandas as pd
import os

def find_best_column(columns, keywords):
    """Scans dataset columns for matching semantic keywords to allow dynamic inputs."""
    for col in columns:
        clean_col = str(col).strip().lower()
        if any(kw in clean_col for kw in keywords):
            return col
    return None

def load_inventory_context(file_path: str) -> str:
    """Reads inventory file and transforms it into structured text blocks for Gemini."""
    if not file_path or not os.path.exists(file_path):
        return "Error: No inventory database has been uploaded yet."
    
    try:
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
    except Exception as e:
        return f"Error reading the file: {str(e)}"
        
    # Replace empty/missing data cells safely with "N/A"
    df = df.fillna("N/A")
    text_blocks = []
    for _, row in df.iterrows():
        item_profile = []
        for column_name in df.columns:
            field_title = str(column_name).strip().replace("_", " ").title()
            field_value = str(row[column_name]).strip()
            item_profile.append(f"{field_title} : {field_value}")
        text_blocks.append("\n".join(item_profile))
        
    return "\n\n-----------------------\n\n".join(text_blocks)

def get_inventory_metrics(file_path: str) -> dict:
    """
    Dynamically calculates summary statistics. Returns 0 or falls back
    to general shapes if standard pillars like room/dept are missing.
    """
    default_metrics = {
        "total_assets": 0, 
        "departments": 0, 
        "rooms": 0, 
        "types": 0,
        "total_columns": 0,
        "has_special_data": False
    }
    
    if not file_path or not os.path.exists(file_path):
        return default_metrics
        
    try:
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        cols = df.columns.tolist()
        
        # Match inventory structures dynamically
        dept_col = find_best_column(cols, ["department", "dept", "branch", "team"])
        room_col = find_best_column(cols, ["room", "lab", "location", "place", "zone"])
        type_col = find_best_column(cols, ["type", "category", "item", "product", "model"])
        
        def get_clean_unique_count(dataframe, column_name):
            if column_name and column_name in dataframe.columns:
                clean_series = dataframe[column_name].fillna("Unassigned").astype(str).str.strip()
                clean_series = clean_series[clean_series != ""]
                return clean_series.nunique()
            return 0

        # Check if this file has your core tracking properties
        has_special_data = any([dept_col, room_col, type_col])

        return {
            "total_assets": len(df),
            "departments": get_clean_unique_count(df, dept_col),
            "rooms": get_clean_unique_count(df, room_col),
            "types": get_clean_unique_count(df, type_col),
            "total_columns": len(cols),
            "has_special_data": has_special_data
        }
    except Exception:
        return default_metrics
