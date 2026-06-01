import networkx as nx


def find_unreachable(G: nx.DiGraph) -> list:
    """
    BFS from START node (node 0).
    Any node not visited = unreachable.
    """
    if len(G.nodes) == 0:
        return []

    start = None
    for n in G.nodes:
        if G.nodes[n].get("label", "") == "START":
            start = n
            break
    if start is None:
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

    unreachable = set(G.nodes) - visited
    return list(unreachable)


def remove_unreachable(G: nx.DiGraph) -> tuple:
    """Remove all unreachable nodes from CFG."""
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
        print(
            f"\n✅ {len(changes)} unreachable "
            f"block(s) removed:\n"
        )
        for c in changes:
            print(f"  ✗ {c}")
    else:
        print("\n  No unreachable code found.")