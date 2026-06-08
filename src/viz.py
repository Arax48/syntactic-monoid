# src/viz.py
import graphviz

def render_dfa(dfa, filename="dfa_graph", view=True):
    """Renders the DFA as a graph using Graphviz."""
    dot = graphviz.Digraph(name="DFA", format="png")
    dot.attr(rankdir="LR")

    for state in dfa.states:
        if state in dfa.accepting:
            dot.node(state, shape="doublecircle")
        else:
            dot.node(state, shape="circle")

    # Invisible start arrow
    dot.node("", shape="none")
    dot.edge("", dfa.start)

    for state, transitions in dfa.transitions.items():
        # Group symbols that go to the same target
        grouped = {}
        for symbol, target in transitions.items():
            grouped.setdefault(target, []).append(symbol)
        for target, symbols in grouped.items():
            dot.edge(state, target, label=", ".join(sorted(symbols)))

    dot.render(filename, view=view, cleanup=True)
    print(f"DFA graph saved to {filename}.png")
