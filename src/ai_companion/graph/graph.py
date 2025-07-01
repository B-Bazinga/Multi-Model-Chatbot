from functools import lru_cache

from langgraph.graph import END, START, StateGraph

# Fetch all the edges for the LangGraph
from ai_companion.graph.edges import (
    select_workflow,
    should_summarize_conversation,
)

# Fetch all the nodes for the LangGraph
from ai_companion.graph.nodes import (
    audio_node,
    context_injection_node,
    conversation_node,
    image_node,
    memory_extraction_node,
    memory_injection_node,
    router_node,
    summarize_conversation_node,
)
# Get all the states for the LangGraph
from ai_companion.graph.state import AICompanionState


@lru_cache(maxsize=1) # Graph is built once and can be used again and again 
def create_workflow_graph():
    # Use the statebuilder to make the LangGraph which is made up of all the states 
    graph_builder = StateGraph(AICompanionState)

    # Add all the nodes -- Memory Extraction, Router, Context Injection, Conversation node, Image, Audio and Summarize Node
    graph_builder.add_node("memory_extraction_node", memory_extraction_node)
    graph_builder.add_node("router_node", router_node)
    graph_builder.add_node("context_injection_node", context_injection_node)
    graph_builder.add_node("memory_injection_node", memory_injection_node)
    graph_builder.add_node("conversation_node", conversation_node)
    graph_builder.add_node("image_node", image_node)
    graph_builder.add_node("audio_node", audio_node)
    graph_builder.add_node("summarize_conversation_node", summarize_conversation_node)

    # Define the Flow -- ie the Transitions for each node 
    # Extract the memories from the message
    graph_builder.add_edge(START, "memory_extraction_node")

    # Then determine response type if it is an image, text or audio
    graph_builder.add_edge("memory_extraction_node", "router_node")

    # Then inject both context and memories
    graph_builder.add_edge("router_node", "context_injection_node")
    # Add all the relevant memory which is going to be used for making the next response
    graph_builder.add_edge("context_injection_node", "memory_injection_node")

    # Then proceed to appropriate response node ie if it text, image or audio response
    graph_builder.add_conditional_edges("memory_injection_node", select_workflow) # ---> Acting as a conditional Statement

    # Check for summarization after any response
    graph_builder.add_conditional_edges("conversation_node", should_summarize_conversation)

    # Different response Nodes
    graph_builder.add_conditional_edges("image_node", should_summarize_conversation)
    graph_builder.add_conditional_edges("audio_node", should_summarize_conversation)
    graph_builder.add_edge("summarize_conversation_node", END)

    return graph_builder

# Compiled without a checkpointer. Meaning no checkpoints are saved for the graph to start from the state where it was left. Since the workflow is short-lived on so we won't need checkpoints.
graph = create_workflow_graph().compile()