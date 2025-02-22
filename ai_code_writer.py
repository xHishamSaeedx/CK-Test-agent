import os
import json
from typing import Union
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeneratedCode(BaseModel):
    code: str
    description: str
    expected_input: str
    expected_output: str
    tech_stack: list[str]
    code_locations: list[dict[str, int]] = [{"start": 1, "end": 1}]  # Added default value
    
    @property
    def primary_location(self) -> dict[str, int]:
        """Returns the first code location or a default if none exist"""
        return self.code_locations[0] if self.code_locations else {"start": 1, "end": 1}

# Initialize Groq model
model = GroqModel(
    'llama-3.3-70b-versatile', 
    api_key=os.getenv('GROQ_API_KEY')
)

# Create agent
code_generator = Agent(
    model,
    result_type=GeneratedCode,
    system_prompt=(
        "You are a Python code generator. When given a request:\n"
        "1. Generate appropriate Python code\n"
        "2. Provide a description of what the code does\n"
        "3. Specify expected inputs and outputs\n"
        "4. List the technologies used\n"
        "5. Specify code locations as a list of dictionaries, where each dictionary has 'start' and 'end' line numbers\n"
        "   Format example: [{\"start\": 1, \"end\": 3}, {\"start\": 5, \"end\": 8}]\n"
        "Return all information in a structured format matching the GeneratedCode model."
    ),
)

def generate_files(prompt: str, code_filename: str = "generated_code.py"):
    """
    Generate Python code and documentation based on the prompt.
    
    Args:
        prompt: The code generation prompt
        code_filename: Name of the Python file to create
    """
    # Get code from AI
    result = code_generator.run_sync(prompt)
    
    # Create the Python file
    with open(code_filename, "w") as f:
        f.write(result.data.code)
    
    # Create the JSON documentation file instead of MD
    doc_filename = f"{code_filename.rsplit('.', 1)[0]}.json"
    documentation = {
        "description": result.data.description,
        "technical_details": {
            "file": code_filename,
            "code_locations": result.data.code_locations
        },
        "usage": {
            "input": result.data.expected_input,
            "output": result.data.expected_output
        },
        "technology_stack": result.data.tech_stack
    }
    
    with open(doc_filename, "w") as f:
        json.dump(documentation, f, indent=4)

    return result.data

def main():
    # Example usage
    prompt = "Create a fastapi app that has a route /hello that returns 'Hello, World!'"
    result = generate_files(prompt)
    print(f"Generated files with the following details:")
    print(f"Description: {result.description}")
    print(f"Code locations: {result.code_locations}")

if __name__ == "__main__":
    main()