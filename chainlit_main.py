from agent import health_planner_agent 
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered, Runner,OpenAIChatCompletionsModel,AsyncOpenAI,set_tracing_disabled
from dotenv import load_dotenv
from agents.run import RunConfig
import os
import chainlit as cl
from openai.types.responses import ResponseTextDeltaEvent



load_dotenv()
set_tracing_disabled(disabled=True)
API_KEY = os.getenv("GEMINI_API_KEY")


external_client = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client
)

@cl.on_chat_start
async def start_chat():
    cl.user_session.set("History_save",[])
    await cl.Message(content="👋 Hello! How Can I Help You Today?").send()

@cl.on_message
async def message_handler(message:cl.Message):
    history = cl.user_session.get("History_save")
    history.append({"role":"user","content":message.content})

    msg = cl.Message(content=" ")
    await msg.send()

    result = Runner.run_streamed(
        health_planner_agent,
        history,
        run_config=config
)
    try:
        async for event in result.stream_events():
            if event.type =="raw_response_event" and isinstance(event.data,ResponseTextDeltaEvent):
                await msg.stream_token(event.data.delta)

            
    except InputGuardrailTripwireTriggered:
        print("❌ Sorry, your message isn't related to health & wellness. Please try asking something health-related.")
    except OutputGuardrailTripwireTriggered as e:
        print("Health Wellness Agent output tripped :", e)
    
    # await cl.Message(content=result.final_output).send()
    history.append({"role":"assistant","content":result.final_output})
    cl.user_session.set("History", history)


