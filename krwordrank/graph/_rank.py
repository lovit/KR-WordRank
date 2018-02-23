def hits(graph, beta, max_iter=50, bias=None, verbose=True, 
    sum_weight=100, number_of_nodes=None, converge=0.001):

    if not bias:
        bias = {}
    if not number_of_nodes:
        number_of_nodes = max(len(graph), len(bias))

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