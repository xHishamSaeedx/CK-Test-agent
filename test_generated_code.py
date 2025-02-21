import os
import sys
import subprocess
import logging
from typing import Union
from pathlib import Path
import shutil
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class TestResult(BaseModel):
    is_successful: bool
    explanation: str
    improvements: str = ""  # Added field for suggested improvements

def read_markdown_file(file_path: str) -> dict:
    """Parse the markdown file to extract information."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract relevant sections
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        if line.startswith('##'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
            current_section = line.replace('#', '').strip()
        else:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def create_test_file(original_file: str, test_cases: list) -> str:
    """Create a copy of the original file with test cases."""
    # Read the original function
    with open(original_file, 'r') as f:
        original_code = f.read()
    
    # Create test file content with ASCII symbols instead of Unicode
    test_file_content = f"""{original_code}

# Test cases
def run_tests():
    test_cases = {test_cases}
    results = []
    
    for i, (input_str, expected) in enumerate(test_cases, 1):
        result = length_of_longest_substring(input_str)
        success = result == expected
        results.append(success)
        print(f'Test {{i}}: Input="{{input_str}}", Expected={{expected}}, Got={{result}}, {{"++" if success else "--"}}')
    
    return all(results), results

if __name__ == '__main__':
    success, results = run_tests()
    print(f"\\nOverall: {{'All tests passed!' if success else 'Some tests failed.'}}")
    sys.exit(0 if success else 1)
"""
    
    # Create test file with UTF-8 encoding
    test_file_path = 'test_generated_code_copy.py'
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_file_content)
    
    return test_file_path

def run_tests(test_file: str) -> tuple[bool, str]:
    """Run the test file and capture output."""
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def evaluate_results(md_content: str, test_output: str) -> TestResult:
    """Use PydanticAI to evaluate the test results."""
    model = GroqModel('llama-3.3-70b-versatile', api_key='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')
    
    agent = Agent(
        model,
        result_type=TestResult,
        system_prompt=(
            "You are a code quality evaluator. Based on the markdown documentation "
            "and test results provided, determine if the code successfully meets its objectives. "
            "If the code is not successful, provide specific details about what's wrong "
            "and suggest improvements. Return a boolean result, explanation, and improvements needed."
        )
    )
    
    prompt = f"""
    Documentation:
    {md_content}
    
    Test Results:
    {test_output}
    
    Analyze the implementation considering:
    1. Does it meet the documented objectives?
    2. Do all test cases pass?
    3. Are there any edge cases that fail?
    4. What specific improvements are needed if it's not successful?
    """
    
    result = agent.run_sync(prompt)
    return result.data

def main():
    # Test cases for the longest substring without repeating characters
    test_cases = [
        ("abcabcbb", 3),  # Basic case from documentation
        ("bbbbb", 1),     # Same character repeated
        ("pwwkew", 3),    # Multiple substrings of same length
        ("", 0),          # Empty string
        (" ", 1),         # Single space
        ("au", 2),        # Two different characters
        ("aab", 2),       # Repeated character at end
        ("dvdf", 3),      # Complex case
    ]
    
    try:
        # Read the markdown file
        md_content = read_markdown_file('generated_code.md')
        logging.info("Successfully parsed markdown file")
        
        # Create and run test file
        test_file = create_test_file('generated_code.py', test_cases)
        logging.info(f"Created test file: {test_file}")
        
        # Run tests
        success, test_output = run_tests(test_file)
        logging.info("Test execution completed")
        logging.info(f"Test output:\n{test_output}")
        
        # Evaluate results using PydanticAI
        evaluation = evaluate_results(str(md_content), test_output)
        logging.info(f"AI Evaluation: Success={evaluation.is_successful}")
        logging.info(f"Explanation: {evaluation.explanation}")
        
        if not evaluation.is_successful:
            logging.warning("Code needs improvements:")
            logging.warning(evaluation.improvements)
            
            # Create a feedback file for the coding LLM
            with open('improvement_feedback.txt', 'w') as f:
                f.write("Original Documentation:\n")
                f.write(str(md_content))
                f.write("\n\nTest Results:\n")
                f.write(test_output)
                f.write("\n\nEvaluation Results:\n")
                f.write(f"Success: {evaluation.is_successful}\n")
                f.write(f"Explanation: {evaluation.explanation}\n")
                f.write(f"Required Improvements: {evaluation.improvements}\n")
            
            logging.info("Feedback has been saved to 'improvement_feedback.txt'")
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            
    except Exception as e:
        logging.error(f"Error during test execution: {str(e)}")
        raise

if __name__ == "__main__":
    main() 