from src.modules.extractor import getPage
from difflib import get_close_matches
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go

class KG:
    def __init__(self):
        self.graph = nx.DiGraph()
    def build_kg(self,data):
        for d in data:
            for rel in d['relation']:
                subj,vrb,obj = rel
                self.graph.add_node(subj)
                self.graph.add_node(obj)
                self.graph.add_edge(subj,obj,relation=vrb)
       # return self.graph 
    def match_queries(self,entities,relation):
        match_nodes,match_edges = [],[]
        for e in entities:
            matches = get_close_matches(e,self.graph.nodes(),n=1,cutoff=0.6)
            if matches:
                match_nodes.append(matches[0])
        
        for r in relation:
            subj,rel,obj = r
            for u,v,data in self.graph.edges(data=True):
                edge_rel = data.get('relation','')
                if isinstance(edge_rel,str) and rel.lower() in edge_rel.lower():
                    match_edges.append((u,edge_rel,v))
        
        return match_nodes,match_edges
    
    def visualize_kg_3d(self):
        G = self.graph
        pos = nx.spring_layout(G, dim=3, seed=42)

        x_nodes = [pos[node][0] for node in G.nodes()]
        y_nodes = [pos[node][1] for node in G.nodes()]
        z_nodes = [pos[node][2] for node in G.nodes()]

        x_edges, y_edges, z_edges = [], [], []
        for edge in G.edges():
            x_edges += [pos[edge[0]][0], pos[edge[1]][0], None]
            y_edges += [pos[edge[0]][1], pos[edge[1]][1], None]
            z_edges += [pos[edge[0]][2], pos[edge[1]][2], None]

        edge_trace = go.Scatter3d(
            x=x_edges, y=y_edges, z=z_edges,
            mode='lines',
            line=dict(color='gray', width=2),
            hoverinfo='none'
        )

        node_trace = go.Scatter3d(
            x=x_nodes, y=y_nodes, z=z_nodes,
            mode='markers+text',
            text=list(G.nodes()),
            textposition="top center",
            marker=dict(size=8, color='skyblue'),
            hovertext=list(G.nodes()),
            hoverinfo='text'
        )

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title="3D Knowledge Graph",
            showlegend=False,
            margin=dict(l=0, r=0, b=0, t=50),
            scene=dict(
                xaxis=dict(showbackground=False),
                yaxis=dict(showbackground=False),
                zaxis=dict(showbackground=False)
            )
        )

        fig.show()

