import re
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class CodeFix(BaseModel):
    fixed_code: str
    explanation: str

class ImprovementFeedback(BaseModel):
    test_results: str
    evaluation_success: bool
    evaluation_explanation: str
    required_improvements: str

class CodeFixerAgent:
    def __init__(self, api_key: str):
        self.model = GroqModel('llama-3.3-70b-versatile', api_key=api_key)
        self.agent = Agent(
            self.model,
            result_type=CodeFix,
            system_prompt=(
                "You are a Python code fixing expert. Analyze the code and its test results, "
                "then provide the fixed code and an explanation of the changes made. "
                "Return only valid Python code that fixes the issues while maintaining the original functionality."
            )
        )

    def extract_file_info(self, markdown_path: str) -> tuple[Optional[str], Optional[tuple[int, int]]]:
        """Extract file path and line numbers from markdown."""
        md_content = Path(markdown_path).read_text()
        
        # Extract file path
        file_match = re.search(r'File: (.+\.py)', md_content)
        if not file_match:
            return None, None
        
        # Extract line numbers
        lines_match = re.search(r'Lines: (\d+)-(\d+)', md_content)
        if not lines_match:
            return file_match.group(1), None
        
        return file_match.group(1), (int(lines_match.group(1)), int(lines_match.group(2)))

    def get_improvement_feedback(self, feedback_path: str) -> ImprovementFeedback:
        """Extract improvement feedback from the feedback file."""
        try:
            content = Path(feedback_path).read_text()
            
            # Extract test results
            test_match = re.search(r'Test Results:\n(.*?)\n\nOverall:', content, re.DOTALL)
            test_results = test_match.group(1).strip() if test_match else ""
            
            # Extract evaluation results
            success_match = re.search(r'Success: (True|False)', content)
            success = success_match.group(1) == "True" if success_match else False
            
            explanation_match = re.search(r'Explanation: (.*?)\n', content)
            explanation = explanation_match.group(1) if explanation_match else ""
            
            improvements_match = re.search(r'Required Improvements: (.*?)$', content)
            improvements = improvements_match.group(1) if improvements_match else ""
            
            return ImprovementFeedback(
                test_results=test_results,
                evaluation_success=success,
                evaluation_explanation=explanation,
                required_improvements=improvements
            )
        except Exception as e:
            print(f"Error parsing improvement feedback: {e}")
            return None

    def extract_code(self, file_path: str, line_range: Optional[tuple[int, int]] = None) -> str:
        """Extract code from the specified file and line range."""
        try:
            code = Path(file_path).read_text()
            if line_range:
                lines = code.splitlines()
                start, end = line_range
                return "\n".join(lines[start:end + 1])
            return code
        except FileNotFoundError:
            return ""

    def fix_code(self, code: str, feedback: ImprovementFeedback) -> CodeFix:
        """Use Groq Pydantic AI to fix the code."""
        prompt = f"""
        Here is the Python code that needs fixing:
        
        {code}
        
        Test Results:
        {feedback.test_results}
        
        The code needs improvement because:
        {feedback.evaluation_explanation}
        
        Required improvements:
        {feedback.required_improvements}
        
        Please provide the fixed code that implements these improvements and passes all tests.
        """
        
        result = self.agent.run_sync(prompt)
        return result.data

    def update_file(self, file_path: str, fixed_code: str, line_range: Optional[tuple[int, int]] = None):
        """Update the file with fixed code."""
        try:
            if line_range:
                # Read existing file
                lines = Path(file_path).read_text().splitlines()
                start, end = line_range
                
                # Replace specific lines
                new_lines = fixed_code.splitlines()
                lines[start:end + 1] = new_lines
                
                # Write back to file
                Path(file_path).write_text('\n'.join(lines))
            else:
                # Replace entire file
                Path(file_path).write_text(fixed_code)
                
            print(f"Successfully updated {file_path}")
        except Exception as e:
            print(f"Error updating file: {e}")

def main():
    # Get API key from environment variables
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("Error: GROQ_API_KEY not found in environment variables")
        return
        
    # Initialize the code fixer with the API key from .env
    fixer = CodeFixerAgent(api_key=api_key)
    
    # Paths to required files
    markdown_path = 'generated_code.md'
    feedback_path = 'improvement_feedback.txt'
    
    # Extract file information from markdown
    file_path, line_range = fixer.extract_file_info(markdown_path)
    if not file_path:
        print("Could not find Python file information in markdown")
        return
    
    # Get the original code
    code = fixer.extract_code(file_path, line_range)
    if not code:
        print(f"Could not extract code from {file_path}")
        return
    
    # Get improvement feedback
    feedback = fixer.get_improvement_feedback(feedback_path)
    if not feedback:
        print("Could not extract improvement feedback")
        return
    
    if feedback.evaluation_success:
        print("Code is already working correctly!")
        return
    
    # Fix the code using Groq Pydantic AI
    try:
        fixed_code = fixer.fix_code(code, feedback)
        print(f"Fix explanation: {fixed_code.explanation}")
        
        # Update the file with fixed code
        fixer.update_file(file_path, fixed_code.fixed_code, line_range)
    except Exception as e:
        print(f"Error during code fixing: {e}")

if __name__ == "__main__":
    main() 