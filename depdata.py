import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pandas as pd
import networkx as nx
import math

# Import Data
data = pd.read_csv("./assets/Factorio Science - Dependencies.csv")

def main(TIMECONSTANT=1, save=True, name="out", outdir="./output/"):

    # Create Graph
    G = nx.DiGraph(TIMECONSTANT=1)
    G.graph['graph']={'rankdir':'LR','label':"Time Constant: {}s".format(TIMECONSTANT)}
    
    # Add nodes to Graph with data
    node_data = data[["Parent","Time","Output"]]
    for i, d in node_data.iterrows():
        G.add_node(d["Parent"],Time=d["Time"],QuantityOut=d["Output"])
        
    # Format Data into a relational format
    ## Select each child individually
    D = [data[["Parent","Child {}".format(i+1),"Amount {}".format(i+1)]].copy() for i in range(3)]
    
    ## Drop all NaN's
    for d in D:
        d.dropna(inplace=True)
    
    ## Rename to a common naming Scheme
    for i, d in enumerate(D):
        d.rename(index=str, columns={"Child {}".format(i+1): "Child", "Amount {}".format(i+1): "Amount"}, inplace=True)
    
    # Concatenate them
    dependencies = pd.concat(D, ignore_index=True)            
    
    # Find independent nodes
    independent = set()
    for i, d in dependencies.iterrows():
        if d["Parent"] not in G.nodes():
            independent.add(d["Parent"])
        if d["Child"] not in G.nodes():
            independent.add(d["Child"])
            
    print("Independent: {}".format(independent))
    # Add Edges to Graph
    for i, d in dependencies.iterrows():
        G.add_edge(d["Child"],d["Parent"],QuantityPer=d["Amount"])
    
    # Update weights to fit with demand
    def how_many_do_i_need(node):
        if "QuantityNeeded" in G.node[node]:
            return G.node[node]["QuantityNeeded"]
        total = 0
        customers = [n for n in G.nodes() if n in G.edge[node]]
        for n in customers:
            quantity_per = G.edge[node][n]["QuantityPer"]
            total += quantity_per * how_many_do_i_need(n)
        return total
    
    # TODO: Instead, get the nodes which have no parents algorithmically
    roots = ["Science Pack 1","Science Pack 2","Science Pack 3","Military Science Pack","Production Science Pack","High Tech Science Pack"]
    for n in roots:
        G.node[n]["QuantityNeeded"] = 1
    
    for n in G.nodes():
        G.node[n]["QuantityNeeded"] = how_many_do_i_need(n)
        if "QuantityOut" in G.node[n]:
            quantPer = (G.node[n]["QuantityOut"]/G.node[n]["Time"])*TIMECONSTANT
            G.node[n]["QuantityPer"]=quantPer
            G.node[n]["FactoriesNeeded"] = 1./((1./G.node[n]["QuantityNeeded"])*(quantPer))
        #if "Time" in G.node[n]:
        #    del G.node[n]["Time"]
        
    # Plotting
    ## Make labels
    for n in G.nodes():
        #print(G.node[n])
        out = str(n)+"\n"
        for k, v in G.node[n].items():
            if isinstance(v,float):
                out += str(k)+": "+'{0:.2f}'.format(v)+"\n"
            else:
                out += str(k)+": "+str(v)+"\n"
        print(out)
        G.node[n]["label"]=out
        
    for n1,n2 in G.edges():
        out = ""
        for k, v in G.edge[n1][n2].items():
            if isinstance(v,float):
                out += str(k)+": "+'{0:.2f}'.format(v)+"\n"
            else:
                out += str(k)+": "+str(v)+"\n"
        G.edge[n1][n2]["label"]=out
        
    ## Output
    if save:
        save_graph(G, name=name, outdir=outdir)
        
    return G
    
def save_graph(G, name="out", outdir="./output/"):
    """ Draws and saves a graph. """
    from networkx.drawing.nx_pydot import write_dot
    from subprocess import call
    import os
    if not os.path.exists(outdir+name+"/"):
        os.makedirs(outdir+name+"/")
    write_dot(G,outdir+name+"/"+name+".dot")
    call(["dot", "-Tpng", outdir+name+"/"+name+".dot", "-o", outdir+name+"/"+name+".png"])
    call(["dot", "-Tpdf", outdir+name+"/"+name+".dot", "-o", outdir+name+"/"+name+".pdf"])

def min_one_factory_optimize(save=True, name="out", outdir="./output/"):
    """ Chooses a time constant which would have the minimum number of factories precisely equal 1. """
    G = main(TIMECONSTANT=1,save=False)
    num_factories = [G.node[n]["FactoriesNeeded"] for n in G.nodes() if "FactoriesNeeded" in G.node[n]]
    out = G.graph["TIMECONSTANT"]*float(min(num_factories))
    return main(out, save=save, name=name, outdir=outdir)
    
if __name__=="__main__":
    main()
    
    print("Calculate Based on a perfect supply flow.")
    min_one_factory_optimize(name="min_factories")
    