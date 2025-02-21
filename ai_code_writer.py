import os
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
    start_line: int
    end_line: int

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
        "5. Calculate the line numbers where the code should be inserted\n"
        "Return all information in a structured format."
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
    
    # Create the documentation file
    doc_filename = f"{code_filename.rsplit('.', 1)[0]}.md"
    with open(doc_filename, "w") as f:
        f.write(f"""# Code Documentation

## Description
{result.data.description}

## Technical Details
- File: {code_filename}
- Code Location: Lines {result.data.start_line}-{result.data.end_line}

## Usage
### Input
{result.data.expected_input}

### Output
{result.data.expected_output}

## Technology Stack
{chr(10).join([f"- {tech}" for tech in result.data.tech_stack])}
""")

    return result.data

def main():
    # Example usage
    prompt = "Create a python function such that given a string s, return the length of the longest substring without repeating characters."
    result = generate_files(prompt)
    print(f"Generated files with the following details:")
    print(f"Description: {result.description}")
    print(f"Line numbers: {result.start_line}-{result.end_line}")

if __name__ == "__main__":
    main()