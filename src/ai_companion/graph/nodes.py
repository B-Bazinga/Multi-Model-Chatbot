# Define all the nodes used for the Graph
import os
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig

from ai_companion.graph.state import AICompanionState
from ai_companion.graph.utils.chains import (
    get_character_response_chain,
    get_router_chain,
)
from ai_companion.graph.utils.helpers import (
    get_chat_model,
    get_text_to_image_module,
    get_text_to_speech_module,
)
from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager
from ai_companion.modules.schedules.context_generation import ScheduleContextGenerator
from ai_companion.settings import settings

# Router Node --- Uses a chain to determine the workflow 
async def router_node(state: AICompanionState):
    chain = get_router_chain()
    # Analyzes all the recent messages to get a understanding of the workflow
    response = await chain.ainvoke({"messages": state["messages"][-settings.ROUTER_MESSAGES_TO_ANALYZE :]})
    return {"workflow": response.response_type}

# Context Injection Node
def context_injection_node(state: AICompanionState):
    # Check the what is the current Activity AI Agent is meant to do as defined in the prompts
    schedule_context = ScheduleContextGenerator.get_current_activity()
    # It uses that to determine if the current activity which they are doing matches what they are supposed to be doing 
    if schedule_context != state.get("current_activity", ""):
        apply_activity = True
    else:
        apply_activity = False
    return {"apply_activity": apply_activity, "current_activity": schedule_context}

# Conversation Node -- Handles the convo 
async def conversation_node(state: AICompanionState, config: RunnableConfig):
    # Gets the Current Activity and the Memory
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    # Then uses a response chain to make the response based on how the states and memory are
    chain = get_character_response_chain(state.get("summary", ""))

    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    # Returns the Message that our agent will saying 
    return {"messages": AIMessage(content=response)}

# Image Node
async def image_node(state: AICompanionState, config: RunnableConfig):
    # Gets the Current Activity and the Memory and use it to generate an image using a TextToImage Model
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_image_module = get_text_to_image_module()

    scenario = await text_to_image_module.create_scenario(state["messages"][-5:])
    os.makedirs("generated_images", exist_ok=True)
    img_path = f"generated_images/image_{str(uuid4())}.png"
    await text_to_image_module.generate_image(scenario.image_prompt, img_path)

    # Inject the image prompt information as an AI message
    scenario_message = HumanMessage(content=f"<image attached by Mikasa generated from prompt: {scenario.image_prompt}>")
    updated_messages = state["messages"] + [scenario_message]

    response = await chain.ainvoke(
        {
            "messages": updated_messages,
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )

    return {"messages": AIMessage(content=response), "image_path": img_path}

# Audio Node -- Similar as the Image Node but here audio is generated using TextToSpeech Model
async def audio_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_speech_module = get_text_to_speech_module()

    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    output_audio = await text_to_speech_module.synthesize(response)

    return {"messages": response, "audio_buffer": output_audio}

# Summarize Node
async def summarize_conversation_node(state: AICompanionState):
    model = get_chat_model()
    summary = state.get("summary", "")

    if summary:
        summary_message = (
            f"This is summary of the conversation to date between Mikasa and the user: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = (
            "Create a summary of the conversation above between Mikasa and the user. "
            "The summary must be a short description of the conversation so far, "
            "but that captures all the relevant information shared between Mikasa and the user:"
        )

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = await model.ainvoke(messages)

    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][: -settings.TOTAL_MESSAGES_AFTER_SUMMARY]]
    return {"summary": response.content, "messages": delete_messages}

# Memory Extraction Node
async def memory_extraction_node(state: AICompanionState):
    """Extract and store important information from the last message."""
    if not state["messages"]:
        return {}

    memory_manager = get_memory_manager()
    await memory_manager.extract_and_store_memories(state["messages"][-1])
    return {}

# Memory Injection Node
def memory_injection_node(state: AICompanionState):
    """Retrieve and inject relevant memories into the character card."""
    memory_manager = get_memory_manager()

    # Get relevant memories based on recent conversation
    recent_context = " ".join([m.content for m in state["messages"][-3:]])
    memories = memory_manager.get_relevant_memories(recent_context)

    # Format memories for the character card
    memory_context = memory_manager.format_memories_for_prompt(memories)

    return {"memory_context": memory_context}
