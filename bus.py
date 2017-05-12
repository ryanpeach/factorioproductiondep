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

def announce(f):
    def wrapper(*args, **kwargs):
        out = f(*args, **kwargs)
        print("{}({},{}) -> {}".format(f.__name__, args, kwargs, out))
        return out
    return wrapper
    
def declare(**kwargs):
    for k, v in kwargs.items():
        print(str(k)+": "+str(v))

def printlst(*args):
    for v in args:
        print(v)
        
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

## Create the main test methods
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
    out = set(s for s in successors if direct_supplied_by(s,Bi) and s not in Bi)

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

""" 
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
"""
generate = creation_hypotheses # Gets rid of removal

# Graph
def generate_and_validate(GT, G0, Bi):
    GT.node[Bi]['done'] = True
    H = generate(Bi)
    for h in H:
        if h not in GT:
            v, t = valid(G0, h), test_b(G0, h)
            GT.add_node(h, done=False, valid=v, test=t)
            
        GT.add_edge(Bi, h, added=h.difference(Bi), removed=Bi.difference(h))
        if GT.node[h]["valid"]:
            score(h, GT)
        
def select_next(GT):
    H = find_heads(GT)
    scores = [GT.node[h]['score'] for h in H if not GT.node[h]['done']]
    if scores:
        best_score_idx = np.argmin(scores)
        return H[best_score_idx]

def test(GT):
    H = find_heads(GT)
    for i, h in enumerate(H):
        if GT.node[h]["test"]:
            GT.node[h]["done"] = True
            return h

def needed_in(item, bus, exceptions={}):
    for b_item in bus:
        if item in D.predecessors(b_item) or item in exceptions:
            return True
    return False
    
def trim_path(path, G0):
    outpath = []
    G0 = frozenset(G0)
    path = list(path)
    
    assert valid(G0, path[0]), "Goal {} can not be supplied by the starting bus {}.".format(G0, path[0])
    assert all(g in path[-1] for g in G0), "Not all goals in the final element of path: {}".format([g for g in G0 if g not in path[-1]])
    
    path[-1] = G0
    
    # An item is currunneeded if no future bus's needs include it
    for i, b0 in enumerate(path[:-1]):
        outbus = []
        for item in b0:
            for b1 in path[i+1:]:
                if needed_in(item,b1,):
                    #print("{} needed in {}".format(item, b1))
                    outbus.append(item)
                    break
                #print("{} not needed in {}".format(item, b1))
            #print("-----------------")
        outpath.append(frozenset(outbus))
    return outpath+[G0]
    
# Distances
def dist(GT, g, Bi):
    if g in Bi:
        return 0
    elif direct_supplied_by(g, Bi):
        return 1
    else:
        return 1+min(dist(GT, p, Bi) for p in D.predecessors_iter(g))

# Scoring
def score_by_distance(Bi, GT):
    assert Bi in GT, "{} not yet in GT".format(Bi)
    total = 0
    for g in G0:
        d = dist(GT, g, Bi)
        if d:
            total += d
    GT.node[Bi]["score"] = total
    GT.node[Bi]["distance"] = total
    
def score_with_min_length(Bi, GT, p=.5):
    assert Bi in GT, "{} not yet in GT".format(Bi)
    B0 = GT.graph["B0"]
    
    if Bi is not B0:
        all_paths = nx.all_simple_paths(GT, source=B0, target=Bi)
        max_lengths = [max([len(b) for b in path]) for path in all_paths]
        minimax = min(max_lengths)
    else:
        minimax = len(B0)
    
    # Save Score
    GT.node[Bi]["minimax length"] = minimax
    score_by_distance(Bi, GT)
    GT.node[Bi]["score"] *= (1.-p)
    GT.node[Bi]["score"] += minimax*p

## Default name for scoring
score = score_by_distance

# Main Process
def main(G0, B0, max_n = 500, verbose=True):
    # Throw an error if not possible from original bus
    assert valid(G0, B0), "Goal {} can not be supplied by the starting bus {}.".format(G0, B0)
    
    # Generate generate and test graph
    GT = nx.DiGraph()
    GT.graph["B0"] = B0
    GT.graph["G0"] = G0
    GT.add_node(B0, done=False, test=test_b(G0, B0), valid=True)
    score(B0, GT)
    
    # Main loop
    def find_next():
        done = test(GT)
        try:
            while True:
                best_h = select_next(GT)
                if best_h:
                    generate_and_validate(GT, G0, best_h)
                    done = test(GT)
                    if done:
                        # Find all paths
                        for best_path in nx.all_shortest_paths(GT, source=B0, target=done):
                        
                            # Print output
                            if verbose == 2:
                                print("Found:")
                                printlst(best_path)
                        
                            yield done, best_path
                        
                        if verbose:
                            print("Next")
                        
                else:
                    if verbose == 2:
                        print("None Found.")
                    raise StopIteration
                    
        except KeyboardInterrupt:
            raise StopIteration
            
    # Look for the minimum of the maximum bus lengths
    best_path, best_score, best_mean_lengths, n = None, None, None, 0
    def announce_save(new=True):
        if verbose:
            if new:
                print("\n========== New Best Score: {} Length: {} Mean: {} ==============".format(best_score, len(best_path), best_mean_lengths))
            else:
                print("\n========== Best Score: {} Length: {} Mean: {} ==============".format(best_score, len(best_path), best_mean_lengths))
            
            printlst(*best_path)
                
            for p0, p1 in zip(best_path, best_path[1:]):
                added, removed = p1.difference(p0), p0.difference(p1)
                if added:
                    declare(added=added)
                if removed:
                    declare(removed=removed)
                    
    for h, path in find_next():
        trim_p = trim_path(path, G0)
        lengths = [len(p) for p in trim_p]
        mean_lengths = np.mean(lengths)
        max_score = max(lengths)
        
        # If this is the first iteration
        if best_score is None:
            best_path, best_score, best_mean_lengths = trim_p, max_score, mean_lengths
            announce_save()
            
        # If the max score is better than best score
        elif max_score < best_score:
            best_path, best_score, best_mean_lengths = trim_p, max_score, mean_lengths
            announce_save()
            
        # If not a shorter max width, a shorter length
        elif len(trim_p) < len(best_path):
            best_path, best_score, best_mean_lengths = trim_p, max_score, mean_lengths
            announce_save()
        
        # If not a shorter length, a shorter average width
        elif mean_lengths < best_mean_lengths:
            best_path, best_score, best_mean_lengths = trim_p, max_score, mean_lengths
            announce_save()
            
        # Print no better if verbose
        elif verbose:
            print("\nNo better: Score: {} Length: {} Mean: {}".format(best_score, len(best_path), best_mean_lengths))
        
        # Breakout
        if n > max_n:
            break
        n += 1
    
    announce_save(new=False)
    return best_path, best_score
    
if __name__=="__main__":
    # Starting Bus
    B0 = frozenset(["Stone Brick", "Iron Plate", "Copper Plate", "Coal", "Steel Plate", "Lubricant", "Plastic Bar", "Coal", "Sulfur"])
    B0 = frozenset(find_roots(D))
    
    # Goal
    G0 = frozenset(["Science Pack 1", "Science Pack 2", "Science Pack 3", "Production Science Pack", "Military Science Pack", "High Tech Science Pack"])

    main(G0, B0)