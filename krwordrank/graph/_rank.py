def hits(graph, beta, max_iter=50, bias=None, verbose=True, 
    sum_weight=100, number_of_nodes=None, converge=0.001):
    """
    It trains rank of node using HITS algorithm.

    Arguments
    ---------
    graph : dict of dict
        Adjacent subword graph. graph[int][int] = float
    beta : float
        PageRank damping factor
    max_iter : int
        Maximum number of iterations
    bias : None or dict
        Bias vector
    verbose : Boolean
        If True, it shows training progress.
    sum_weight : float
        Sum of weights of all nodes in graph
    number_of_nodes : None or int
        Number of nodes in graph
    converge : float
        Minimum rank difference between previous step and current step.
        If the difference is smaller than converge, it do early-stop.

    Returns
    -------
    rank : dict
        Rank dictionary formed as {int:float}.
    """

    if not bias:
        bias = {}
    if not number_of_nodes:
        number_of_nodes = max(len(graph), len(bias))

    if number_of_nodes <= 1:
        raise ValueError(
            'The graph should consist of at least two nodes\n',
            'The node size of inserted graph is %d' % number_of_nodes
        )

    dw = sum_weight / number_of_nodes
    rank = {node:dw for node in graph.keys()}

    for num_iter in range(1, max_iter + 1):
        rank_ = _update(rank, graph, bias, dw, beta)
        diff = sum((abs(w - rank.get(n, 0)) for n, w in rank_.items()))
        rank = rank_

        if diff < sum_weight * converge:
            if verbose:
                print('\riter = %d Early stopped.' % num_iter, end='', flush=True)
            break

        if verbose:
            print('\riter = %d' % num_iter, end='', flush=True)

    if verbose:
        print('\rdone')

    return rank

def _update(rank, graph, bias, dw, beta):
    rank_new = {}
    for to_node, from_dict in graph.items():
        rank_new[to_node] = sum([w * rank[from_node] for from_node, w in from_dict.items()])
        rank_new[to_node] = beta * rank_new[to_node] + (1 - beta) * bias.get(to_node, dw)
    return rank_new