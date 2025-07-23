from agents.guardrail import input_guardrail, GuardrailFunctionOutput,output_guardrail
from agents.run import Runner
from agents import RunContextWrapper, Agent
from pydantic import BaseModel
from agents import TResponseInputItem
from config import config,model

# Define output type
class HealthInputOutput(BaseModel):
    is_health_related_question: bool
    input: str
    reasoning: str
    answer: str

# Define agent used for input validation
health_guardrail_agent = Agent(
    name="Health Input Guardrail Agent",
    instructions="""
        You are a friendly and helpful Health & Wellness assistant.
        Your purpose is to support users in areas like: health, fitness, wellness, diet, workout, nutrition, exercise, injuries, goal analysis, meal planning, escalation needs, progress tracking, and regular check-ins.
        You should handle full, detailed conversations like those with doctors or nutritionists. This includes personal stories, explanations, and life context shared by the user.

        Valid inputs also include:
        Polite greetings like "hi", "hello", or "hey".
        Users sharing their current condition, lifestyle, mood, feelings, or personal details (e.g., "My name is Ali", "I'm feeling tired", "I eat out every day").
        Your job is to determine whether the user's message is related to any supported health and wellness topic.

        Supported topics include: 
        Health, fitness, diet, workout, exercise
        Progress tracking, check-in schedules, goal setting and analysis
        Meal planning, nutrition, injuries, escalation needs, and overall wellness
        Any personal detail, lifestyle description, or emotional sharing related to health context

        If the input is clearly unrelated (e.g., about politics, math, or programming), then mark it as not health-related.
        """,
    output_type=HealthInputOutput,
    model=model
)

# actual guardrail function
@input_guardrail
async def health_input_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input:str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
        
        result = await Runner.run(health_guardrail_agent, input, context=ctx.context, run_config=config)
        return GuardrailFunctionOutput(
            output_info=result.final_output,
            tripwire_triggered=not result.final_output.is_health_related_question
        )
   



class HealthOutputValidation(BaseModel):
    is_safe: bool
    original_output: str
    feedback: str

# Output checking agent
output_checker_agent = Agent(
    name="Health Output Guardrail Agent",
    instructions="""You are reviewing the assistant's response to ensure it is safe, relevant, and helpful.
        The response should be related to health, fitness, nutrition, wellness, workout planning, goal analysis,
        tracking progress, injury support, escalation handling, scheduling, or meal planning.
        Polite and friendly responses to greetings (like 'Hi! How can I help you today?') are also acceptable.
        Ensure the assistant avoids giving unrelated, offensive, or harmful advice.
        If the response is off-topic or unsafe, flag it as not acceptable. Otherwise, mark it as valid output.""",
    output_type=HealthOutputValidation,
    model=model
)

# Actual guardrail function
@output_guardrail
async def health_output_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    output: str
) -> GuardrailFunctionOutput:
        
        result = await Runner.run(output_checker_agent, output, context=ctx.context, run_config=config)
        return GuardrailFunctionOutput(
            output_info=result.final_output,
            tripwire_triggered=not result.final_output.is_safe
        )
    
