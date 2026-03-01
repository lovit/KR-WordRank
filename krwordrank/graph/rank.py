def hits(
    graph: dict[int, dict[int, float]],
    beta: float,
    max_iter: int = 50,
    bias: dict[int, float] | None = None,
    verbose: bool = True,
    sum_weight: float = 100,
    number_of_nodes: int | None = None,
    converge: float = 0.001,
) -> dict[int, float]:
    """Train node ranks using the HITS algorithm.

    Args:
        graph: Adjacent subword graph where ``graph[from_node][to_node]`` is the
            edge weight.
        beta: PageRank damping factor (0 < beta < 1).
        max_iter: Maximum number of iterations.
        bias: Bias vector as ``{node_index: bias_value}``. Uses uniform bias if
            None.
        verbose: If True, prints iteration progress.
        sum_weight: Total weight sum across all nodes.
        number_of_nodes: Number of nodes in the graph. Inferred from *graph* and
            *bias* if None.
        converge: Early-stop threshold; training halts when the total rank change
            between consecutive iterations falls below
            ``sum_weight * converge``.

    Returns:
        Rank dictionary as ``{node_index: rank_value}``.

    Raises:
        ValueError: If the graph has fewer than two nodes.
    """
    if not bias:
        bias = {}
    if not number_of_nodes:
        number_of_nodes = max(len(graph), len(bias))

    if number_of_nodes <= 1:
        raise ValueError(
            "The graph should consist of at least two nodes\n",
            "The node size of inserted graph is %d" % number_of_nodes,
        )

    dw = sum_weight / number_of_nodes
    rank = {node: dw for node in graph.keys()}

    for num_iter in range(1, max_iter + 1):
        rank_ = _update(rank, graph, bias, dw, beta)
        diff = sum((abs(w - rank.get(n, 0)) for n, w in rank_.items()))
        rank = rank_

        if diff < sum_weight * converge:
            if verbose:
                print("\riter = %d Early stopped." % num_iter, end="", flush=True)
            break

        if verbose:
            print("\riter = %d" % num_iter, end="", flush=True)

    if verbose:
        print("\rdone")

    return rank


def _update(
    rank: dict[int, float],
    graph: dict[int, dict[int, float]],
    bias: dict[int, float],
    dw: float,
    beta: float,
) -> dict[int, float]:
    rank_new = {}
    for to_node, from_dict in graph.items():
        rank_new[to_node] = sum([w * rank[from_node] for from_node, w in from_dict.items()])
        rank_new[to_node] = beta * rank_new[to_node] + (1 - beta) * bias.get(to_node, dw)
    return rank_new
