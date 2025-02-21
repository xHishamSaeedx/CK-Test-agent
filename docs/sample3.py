from typing import Union

from pydantic import BaseModel

from pydantic_ai import Agent

from pydantic_ai.models.groq import GroqModel

class Box(BaseModel):
    width: int
    height: int
    depth: int
    units: str

model = GroqModel('llama-3.3-70b-versatile', api_key='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')

agent: Agent[None, Union[Box, str]] = Agent(
    model,
    result_type=Union[Box, str],  # type: ignore
    system_prompt=(
        "Extract me the dimensions of a box, "
        "if you can't extract all data, ask the user to try again."
    ),
)

result = agent.run_sync('The box is 10x20x30')
print(result.data)
#> Please provide the units for the dimensions (e.g., cm, in, m).

result = agent.run_sync('The box is 10x20x30 cm')
print(result.data)
#> width=10 height=20 depth=30 units='cm'