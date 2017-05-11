import pandas as pd
import networkx as nx
import numpy as np
from depdata import main as depdata
from depdata import save_graph

# Get our dependency graph
D = depdata(save=False)

# Graph Tools
def find_roots(ADG):
    return [n for n in ADG.nodes() if len(ADG.predecessors(n))==0]
    
def find_heads(ADG):
    return [n for n in ADG.nodes() if len(ADG.successors(n))==0]

def anounce(f):
    def wrapper(*args, **kwargs):
        out = f(*args, **kwargs)
        print("{}({},{}) -> {}".format(f.__name__, args, kwargs, out))
        return out
    return wrapper
    
all_not_empty = lambda X: False if len(X) == 0 else all(X)

# Can our starting bus reach our goal?
def direct_supplied_by(g, Bi):
    """ Can the given goal node {g} be supplied by the given bus {Bi}? """
    assert isinstance(Bi, frozenset), "Bi {} should be a frozenset. Check your code that you are using sets instead of lists.".format(Bi)
    return all_not_empty([p in Bi for p in D.predecessors_iter(g)])
    
def r_supplied_by(g, Bi):
    """ Can this node or all nodes which this goal node {g} is supplied by be supplied by the given bus {Bi}? """
    if direct_supplied_by(g, Bi):
        return True
    else:
        return all_not_empty([p in Bi or r_supplied_by(p, Bi) for p in D.predecessors_iter(g)])
        
def list_supplied_by(Gi, Bi):
    """ Checks if all items in a goal list {Gi} can be supplied by the given bus {Bi}. """
    return all(r_supplied_by(g,Bi) for g in Gi)

## Create the main test method
def valid(G0, Bi):
    """ The main validity method for a bus. Used to eliminate busses which can not reach to Goal."""
    return (not len(Bi)==0) and list_supplied_by(G0, Bi)
    
def test_b(G0, Bi):
    """ The main test method for a bus. Asks simply if all the goal items are in the bus. Done when true. """
    return all(g in Bi for g in G0)

# Generate
## Generate new hypotheses by adding a possible-to-create item to the bus
def possible_to_create(Bi):
    """ Create a list of items it's possible to create from the bus {Bi}. """
    # We start out knowing at-least that possible-to-create items will be successors of the bus
    successors = set()
    for b in Bi:
        s = set(D.successors(b))
        successors = successors.union(s)
    
    # However, not all successors will be fully supplied by the bus
    # Therefore, we must eliminate successors not supplied by the bus
    out = set(s for s in successors if direct_supplied_by(s,Bi))

    return out
  
def creation_hypotheses(Bi):
    """ Generate all hypotheses where one item is added. """
    H1 = set()
    for s in possible_to_create(Bi):
        Hs = set(Bi.copy())
        Hs.add(s)
        H1.add(frozenset(Hs))
    return H1
    
## Generate new hypotheses by removing each item
def removal_hypotheses(Bi):
    """ Generate all hypotheses where one item is removed. """
    H1 = set()
    for b in Bi:
        Hb = set(Bi.copy())
        Hb.remove(b)
        if len(Hb):
            H1.add(frozenset(Hb))
            
    return H1
    
## Generate all new hypotheses
def generate(Bi):
    # First create all possible things from the current bus
    Hc = creation_hypotheses(Bi)
    
    # Remove items to create new hypotheses
    H1 = set()
    for c in Hc:
        Hr = removal_hypotheses(Bi) # Get all the possible removal hypotheses
        H1.add(c)   # Include the original
        H1.union(Hr) # Add all the removals
        
    return H1

# Graph
def generate_and_validate(GT, G0, Bi):
    GT.node[Bi]['done'] = True
    H = generate(Bi)
    for h in H:
        if h not in GT:
            v, t = valid(G0, h), test_b(G0, h)
            if v:
                s = score_by_distance(h, GT)
            else:
                s = -1
            GT.add_node(h, score=score_by_distance(h, GT), done=False, valid=v, test=t)
            GT.add_edge(Bi, h, removed=Bi.difference(h), added=h.difference(Bi))

def select_next(GT):
    H = find_heads(GT)
    scores = [GT.node[h]['score'] for h in H if not GT.node[h]['done']]
    if scores:
        best_score_idx = np.argmin(scores)
        return H[best_score_idx]

def test(GT):
    H = find_heads(GT)
    idx = None
    for i, h in enumerate(H):
        if GT.node[h]["test"]:
            idx = i
    if idx is not None:
        return H[idx] # Get the H from the index of the true value and return it

def dist(GT, g, Bi):
    if g in Bi:
        return 0
    elif direct_supplied_by(g, Bi):
        return 1
    else:
        return 1+min(dist(GT, p, Bi) for p in D.predecessors_iter(g))
     
def score_by_distance(Bi, GT):
    total = 0
    for g in G0:
        d = dist(GT, g, Bi)
        if d:
            total += d
    return total
    
def main(G0, B0):
    # Throw an error if not possible from original bus
    assert valid(G0, B0), "Goal {} can not be supplied by the starting bus {}.".format(G0, B0)
    
    # Generate generate and test graph
    GT = nx.DiGraph()
    GT.add_node(B0, score=score_by_distance(B0, GT), done=False, test=test_b(G0, B0), valid=True)
    
    # Main loop
    done = test(GT)
    try:
        while not done:
            best_h = select_next(GT)
            if best_h:
                generate_and_validate(GT, G0, best_h)
                done = test(GT)
                if done:
                    best_h = done
            else:
                print("None Found.")
                save_graph(GT, name="GenerateAndTest")
                break
        best_path = nx.shortest_path(GT, source=B0, target=done)
        print("Found:")
        for b in best_path:
            print(list(b))
        GT = GT.subgraph(best_path)
        save_graph(GT, name="GenerateAndTest")
    except KeyboardInterrupt:
        save_graph(GT, name="GenerateAndTest")
        
if __name__=="__main__":
    # Starting Bus
    B0 = frozenset(["Stone Brick", "Iron Plate", "Copper Plate", "Coal", "Steel Plate", "Lubricant", "Plastic Bar", "Coal", "Sulfur"])
    B0 = frozenset(find_roots(D))
    
    # Goal
    G0 = frozenset(["Science Pack 1", "Science Pack 2", "Science Pack 3", "Production Science Pack", "Military Science Pack", "High Tech Science Pack"])

    main(G0, B0)