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
    G = nx.DiGraph()
    G.graph['graph']={'rankdir':'LR'}
    
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
            timePer = (G.node[n]["QuantityOut"]/G.node[n]["Time"])*TIMECONSTANT
            G.node[n]["QuantityPer"]=timePer
            G.node[n]["FactoriesNeeded"] = 1./((1./G.node[n]["QuantityNeeded"])*(timePer))
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
        from networkx.drawing.nx_pydot import write_dot
        from subprocess import call
        write_dot(G,outdir+name+".dot")
        call(["dot", "-Tpng", outdir+name+".dot", "-o", outdir+name+".dot.png"])
        call(["dot", "-Tpdf", outdir+name+".dot", "-o", outdir+name+".dot.pdf"])
    
    return G

if __name__=="__main__":
    main(TIMECONSTANT=60)