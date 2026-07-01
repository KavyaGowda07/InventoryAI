# utils/helper.py
import os
import sys

# Add the project root directory to the Python path so it can find your prompts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts.system_prompt import SYSTEM_PROMPT
from utils.csv_loader import load_inventory_context

def build_final_prompt(user_question: str, data_file_path: str = None) -> str:
    """
    Assembles the System Rules, Converted Excel Data, and User Question
    into a single unified prompt payload for the AI model.
    """
    # 1. Fetch the text representation of your file, or use a placeholder if empty
    if data_file_path and os.path.exists(data_file_path):
        inventory_data_text = load_inventory_context(data_file_path)
    else:
        inventory_data_text = "No inventory file uploaded yet."
    
    # 2. Safely inject data and the user query into the System Prompt template
    final_prompt = SYSTEM_PROMPT.format(
        inventory_data=inventory_data_text,
        user_question=user_question
    )
    
    return final_prompt

# 3. Local Execution Test
if __name__ == "__main__":
    print("Assembling test prompt payload...")
    
    sample_question = "Show all CC devices in D-203."
    test_payload = build_final_prompt(user_question=sample_question)
    
    print("\n--- Final Assembled Prompt Layout Preview ---")
    print(test_payload[:800]) # Prints the first 800 characters to show the structure
    print("\n... [Remaining payload packaged below] ...")
