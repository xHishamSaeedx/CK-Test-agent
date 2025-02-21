from pydantic import BaseModel

from pydantic_ai import Agent

from pydantic_ai.models.groq import GroqModel

class CityLocation(BaseModel):
    city: str
    country: str

model = GroqModel('llama-3.3-70b-versatile', api_key='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')
agent = Agent(model, result_type=CityLocation)
result = agent.run_sync('Where were the olympics held in 2012?')
print(result.data)
#> city='London' country='United Kingdom'
print(result.usage())
"""
Usage(requests=1, request_tokens=57, response_tokens=8, total_tokens=65, details=None)
"""