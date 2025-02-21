from typing import Union

from pydantic_ai import Agent

from pydantic_ai.models.groq import GroqModel

model = GroqModel('llama-3.3-70b-versatile', api_key='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')
agent: Agent[None, Union[list[str], list[int]]] = Agent(
    model,
    result_type=Union[list[str], list[int]],  # type: ignore
    system_prompt='Extract either colors or sizes from the shapes provided.',
)

result = agent.run_sync('red square, blue circle, green triangle')
print(result.data)
#> ['red', 'blue', 'green']

result = agent.run_sync('square size 10, circle size 20, triangle size 30')
print(result.data)
#> [10, 20, 30]