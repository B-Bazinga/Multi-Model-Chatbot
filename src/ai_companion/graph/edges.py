# These consists of transitions that are been defined for the langgraph

from langgraph.graph import END
from typing_extensions import Literal


from ai_companion.graph.state import AICompanionState
from ai_companion.settings import settings

# Should be used to summarize the conversation
def should_summarize_conversation(
    state: AICompanionState,
) -> Literal["summarize_conversation_node", "__end__"]:
    messages = state["messages"]

    if len(messages) > settings.TOTAL_MESSAGES_SUMMARY_TRIGGER:
        return "summarize_conversation_node"

    return END

# Selects the workflow based on the current state so if it images or audio it will decide based on the workflow
def select_workflow(
    state: AICompanionState,
) -> Literal["conversation_node", "image_node", "audio_node"]:
    workflow = state["workflow"]

    if workflow == "image":
        return "image_node"

    elif workflow == "audio":
        return "audio_node"

    else:
        return "conversation_node"
