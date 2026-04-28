import networkx as nx


def find_unreachable(G: nx.DiGraph) -> list:
    """
    BFS/DFS from START node (node 0).
    Any node not visited is unreachable.
    """
    if len(G.nodes) == 0:
        return []

    # BFS from node 0 (START)
    start = 0
    visited = set()
    queue = [start]

    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        for succ in G.successors(node):
            if succ not in visited:
                queue.append(succ)

    # Unreachable = all nodes - visited
    all_nodes = set(G.nodes)
    unreachable = all_nodes - visited
    return list(unreachable)


def remove_unreachable(G: nx.DiGraph) -> tuple:
    """
    Remove all unreachable nodes from CFG.
    Returns (modified_G, list of removed nodes).
    """
    unreachable = find_unreachable(G)
    changes = []

    for node in unreachable:
        label = G.nodes[node].get("label", "")
        first = label.split("\n")[0]
        changes.append(
            f"Block {node} ('{first}'): "
            f"unreachable — removed"
        )
        G.remove_node(node)

    return G, changes


def print_unreachable_code(changes: list):
    print("\n" + "=" * 50)
    print("  UNREACHABLE CODE REMOVAL")
    print("=" * 50)

    if changes:
        print(f"\n✅ {len(changes)} unreachable "
              f"block(s) removed:\n")
        for c in changes:
            print(f"  ✗ {c}")
    else:
        print("\n  No unreachable code found.")