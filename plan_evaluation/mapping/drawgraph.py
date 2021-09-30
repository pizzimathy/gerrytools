
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from gerrychain.graph import Graph
import networkx as nx
from typing import Union, Tuple, Optional, TypedDict, List


def drawgraph(
        G: Graph, ax: Optional[Axes]= None, x: Optional[str]="INTPTLON20",
        y: Optional[str]="INTPTLAT20", components: Optional[bool]=False,
        node_size: Optional[float]=1, **kwargs: Optional[TypedDict]
    ) -> Union[Tuple[Figure, Axes], Tuple[List[Figure], List[Axes]]]:
    """
    Draws a gerrychain Graph object.

    :param G: The dual graph to draw.
    :param ax: Optional; `matplotlib.axes.Axes` object. If not passed, one is
    created.
    :param x: Optional; vertex property used as the horizontal (E-W) coordinate.
    :param y: Optional; vertex property used as the vertical (N-S) coordinate.
    :param components: Optional; if `True`, the graph is assumed to have more
    than one connected component (e.g. Michigan) and is drawn component-wise and
    rather than return a single (`Figure`, `Axes`) pair, return a pair of *lists*
    of `Figure`s and `Axes`.
    :param node_size: Optional; specifies the default size of a vertex.
    :param kwargs: Optional; arguments to be passed to `nx.draw()`.
    """
    # Create a mapping from identifiers to positions.
    positions = {
        v: (properties[x], properties[y])
        for v, properties in G.nodes(data=True)
    }

    # If `components` is true, plot the graph component-wise. Otherwise plot
    # normally. First, set some properties common to both graphs.
    properties = {"pos": positions, "node_size": node_size }

    if components:
        figures, axes = plt.figure(), plt.axes()
        nx.draw(G, ax=axes, **properties, **kwargs)
    else:
        # Create lists for figures and axes.
        figures, axes = [], []

        connected_components = [c for c in nx.connected_components(G)]
        for component in connected_components:
            # Create new Figure and Axes objects.
            fig, ax = plt.figure(), plt.axes()

            # Plot the graph.
            subgraph = G.subgraph(component)
            nx.draw(subgraph, ax=ax, **properties, **kwargs)

            # Add them to their respective lists.
            figures.append(fig)
            axes.append(ax)

    return figures, axes
