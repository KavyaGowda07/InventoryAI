# utils/llm.py
import os
import pandas as pd
from google import genai
from dotenv import load_dotenv

# Import your unified prompt building module
from utils.helper import build_final_prompt

# 1. Initialize API Credentials
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

def find_best_column(columns, keywords):
    """Scans dataset columns for matching semantic keywords to allow dynamic inputs."""
    for col in columns:
        clean_col = str(col).strip().lower()
        if any(kw in clean_col for kw in keywords):
            return col
    return None

def calculate_smart_analytics(file_path: str) -> str:
    """
    Computes precise asset analytics using Pandas to ensure absolute numerical
    accuracy before formatting into the context envelope.
    """
    if not file_path or not os.path.exists(file_path):
        return "No database data available for analysis."
        
    try:
        # Load active database format
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        df = df.fillna("N/A")
        cols = df.columns.tolist()
        
        # Dynamically map flexible header structures
        type_col = find_best_column(cols, ["type", "category", "item", "product", "model"])
        room_col = find_best_column(cols, ["room", "lab", "location", "place", "zone"])
        uid_col = find_best_column(cols, ["uid", "id", "serial", "code", "tag"])
        
        analysis_blocks = []
        
        # Analytics Feature 1: Total Device/Item Type Breakdowns
        if type_col:
            type_counts = df[type_col].value_counts().to_dict()
            type_str = ", ".join([f"{k}: {v} units" for k, v in type_counts.items()])
            analysis_blocks.append(f"Precise Total Asset Category Breakdown: [{type_str}]")
            
        # Analytics Feature 2: High Density Location Identification
        if room_col:
            room_counts = df[room_col].value_counts()
            if not room_counts.empty:
                top_room = room_counts.index[0]
                top_room_count = room_counts.iloc[0]
                analysis_blocks.append(f"Location Concentration Lead: Sector/Room '{top_room}' holds the most records with exactly {top_room_count} registered assets.")
        
        # Analytics Feature 3: Data Integrity Scan (Detect Duplicates)
        if uid_col:
            duplicates = df[df.duplicated(subset=[uid_col], keep=False)]
            if not duplicates.empty:
                dup_list = duplicates[uid_col].unique().tolist()
                analysis_blocks.append(f"⚠️ INTEGRITY ALERT: Duplicate Unique IDs detected in system registry: {dup_list}")
            else:
                analysis_blocks.append("Registry Integrity Verification: Confirmed. Zero duplicate identification strings found across items.")
                
        if not analysis_blocks:
            return "No matching columns detected for detailed calculations. Relying purely on raw contextual extraction."
            
        return "\n".join(analysis_blocks)
    except Exception as e:
        return f"Analytics Engine processing skip: {str(e)}"

def get_response(system_prompt: str, inventory_data: str, user_question: str, file_path: str = None) -> str:
    """
    Assembles structural instructions, pre-computed analytics proofs, 
    and raw database context records into the ultimate context envelope.
    """
    # 1. Generate the base context structure containing rules and raw data strings
    base_compiled_prompt = build_final_prompt(user_question=user_question, data_file_path=file_path)
    
    # 2. Pull programmatic analytics calculations directly from pandas
    pre_computed_analytics = calculate_smart_analytics(file_path)
    
    # 3. Inject pandas proof layers into the prompt layout context seamlessly
    final_payload = f"""
{base_compiled_prompt}

------------------------------------
SYSTEM VERIFIED ANALYTICS METRICS (Use for absolute numerical queries):
{pre_computed_analytics}
------------------------------------
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=final_payload,
        )
        return response.text
    except Exception as e:
        return f"An error occurred while calling Gemini: {e}"

if __name__ == "__main__":
    print("AI Core module updated with analytics systems successfully.")
