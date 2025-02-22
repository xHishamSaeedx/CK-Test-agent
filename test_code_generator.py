from typing import Union, Any, List, Dict
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
import json
import os

class CodeLocation(BaseModel):
    start: int
    end: int

class TechnicalDetails(BaseModel):
    file: str
    code_locations: List[CodeLocation]

class GeneratedCodeInfo(BaseModel):
    description: str
    technical_details: TechnicalDetails
    usage: Dict
    technology_stack: List[str]

class CodeResult(BaseModel):
    output: Any
    error: Union[str, None] = None
    fixed_code: Union[str, None] = None

def load_code_info(json_file: str) -> GeneratedCodeInfo:
    """Load code information from JSON file"""
    with open(json_file, 'r') as f:
        data = json.load(f)
        return GeneratedCodeInfo(**data)

def extract_code_snippets(source_file: str, locations: List[CodeLocation]) -> List[str]:
    """Extract code snippets from the specified locations in the source file"""
    snippets = []
    try:
        with open(source_file, 'r') as f:
            lines = f.readlines()
            for location in locations:
                snippet = ''.join(lines[location.start - 1:location.end])
                snippets.append(snippet)
    except FileNotFoundError:
        print(f"Source file {source_file} not found")
    except Exception as e:
        print(f"Error reading file: {str(e)}")
    return snippets

# Initialize the Groq model
model = GroqModel('llama-3.3-70b-versatile', api_key='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')

# Create an agent that can handle code execution
code_agent = Agent(
    model,
    result_type=CodeResult,
    system_prompt="""
    You are a Python code execution assistant. Given a code snippet:
    1. Check for syntax errors and fix them if possible
    2. If the code needs additional imports or context, add them
    3. Return the fixed code and expected output
    4. If there's an error that can't be fixed, provide a clear error message
    5. Add print statements or logging to show execution progress and results
    6. Include a main block to make the code runnable from command line

    Return the results in the CodeResult format with:
    - output: Expected output or None if error
    - error: Error message if any
    - fixed_code: The corrected code if fixable, including:
        * Clear print statements showing execution steps
        * __main__ block for command line execution
        * Status messages indicating success/failure
    """
)

def run_snippet(snippet: str, tech_stack: List[str]) -> CodeResult:
    """Run a single code snippet using Pydantic AI"""
    try:
        context = f"Technology stack: {', '.join(tech_stack)}\nCode snippet:\n{snippet}"
        result = code_agent.run_sync(context)
        return result.data
    except Exception as e:
        return CodeResult(
            output=None,
            error=f"Processing error: {str(e)}",
            fixed_code=None
        )

def save_code_to_file(snippet_num: int, code: str) -> str:
    """Save the code to a new Python file"""
    output_dir = "validated_snippets"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{output_dir}/snippet_{snippet_num}.py"
    with open(filename, 'w') as f:
        f.write(code)
    return filename

def main():
    # Load code information from JSON file
    code_info = load_code_info('generated_code.json')
    
    # Extract code snippets from the source file
    snippets = extract_code_snippets(
        code_info.technical_details.file,
        code_info.technical_details.code_locations
    )
    
    # Process each snippet
    for i, snippet in enumerate(snippets, 1):
        print(f"\nProcessing snippet {i}:")
        print("-" * 40)
        print(f"From file: {code_info.technical_details.file}")
        print(f"Description: {code_info.description}")
        print(f"Original Code:\n{snippet}")
        
        result = run_snippet(snippet, code_info.technology_stack)
        
        print("\nResult:")
        if result.error:
            print(f"Error: {result.error}")
            if result.fixed_code:
                filename = save_code_to_file(i, result.fixed_code)
                print(f"\nSuggested fixed code saved to: {filename}")
                print(f"Code:\n{result.fixed_code}")
        else:
            print(f"Output: {result.output}")
            if result.fixed_code:
                filename = save_code_to_file(i, result.fixed_code)
                print(f"\nValidated code saved to: {filename}")
                print(f"Code:\n{result.fixed_code}")
        print("-" * 40)

if __name__ == "__main__":
    main() 