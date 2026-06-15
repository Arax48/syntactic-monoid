"""
backend.visualization
=====================

Renderizado grafico para uso interactivo y pedagogico.

Por ahora expone una unica funcion publica:

    regex_to_html(pattern, alphabet=None, output_path=None, open_browser=True)

que produce una pagina HTML AUTOCONTENIDA con: la regex de entrada,
una hoja de sintaxis en castellano, y los digrafos del AFN de Thompson,
del AFD por construccion de subconjuntos y del AFD minimo. Los grafos
van inline como SVG (Graphviz). Sin servidor, sin dependencias en
tiempo de ejecucion mas alla de Graphviz.
"""

from backend.visualization.regex_view import regex_to_html

__all__ = ["regex_to_html"]
