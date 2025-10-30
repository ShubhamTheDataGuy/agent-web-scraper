from langgraph.graph import StateGraph, START, END
from agent.utils.states import GraphState, InputState, OutputState
from agent.utils.constants import INITIALIZE, CRAWL, SCRAP, FORMAT, SAVE, ERROR_HANDLER
from agent.utils.nodes import initialize, crawl, scrap, format, save, error_handler

def build_graph():
    graph_builder = StateGraph(GraphState, input=InputState, output=OutputState)

    # Define Nodes
    graph_builder.add_node(INITIALIZE, initialize)
    graph_builder.add_node(CRAWL, crawl)
    graph_builder.add_node(SCRAP, scrap)
    graph_builder.add_node(FORMAT, format)
    graph_builder.add_node(SAVE, save)
    graph_builder.add_node(ERROR_HANDLER, error_handler)

    # Define Edges
    graph_builder.add_edge(START, INITIALIZE)
    graph_builder.add_edge(INITIALIZE, CRAWL)

    # Conditional Edges
    graph_builder.add_conditional_edges(
        source=CRAWL,
        path=lambda state: ERROR_HANDLER if state.get("error") else SCRAP,
        path_map={ERROR_HANDLER: ERROR_HANDLER, SCRAP: SCRAP}
    )
    graph_builder.add_conditional_edges(
        source=SCRAP,
        path=lambda state: ERROR_HANDLER if state.get("error") else FORMAT,
        path_map={ERROR_HANDLER: ERROR_HANDLER, FORMAT: FORMAT}
    )
    graph_builder.add_conditional_edges(
        source=FORMAT,
        path=lambda state: ERROR_HANDLER if state.get("error") else SAVE,
        path_map={ERROR_HANDLER: ERROR_HANDLER, SAVE: SAVE}
    )
    graph_builder.add_conditional_edges(
        source=ERROR_HANDLER,
        path= lambda state: state.get("failed_node") if state.get("retry_count") <= 3 else END,
        path_map={END:END, CRAWL:CRAWL, SCRAP:SCRAP, FORMAT:FORMAT} 
    )

    graph_builder.add_edge(SAVE, END)

    return graph_builder
