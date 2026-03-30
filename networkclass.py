
import math
import networkx as nx
from bokeh.io import output_notebook, show, save
from bokeh.models import Range1d, Circle, ColumnDataSource, MultiLine, EdgesAndLinkedNodes, NodesAndLinkedEdges, LabelSet
from bokeh.plotting import figure
from bokeh.plotting import from_networkx
import numpy as np
import os


class Networks_Game:
    
    def __init__(self, students, Network = "Graph.txt", Round = 0, aliases = None):
        self.round = Round
        self.students = students
        self.aliases = {student: student for student in students}
        if aliases is not None:
            for student in students:
                alias = aliases.get(student, student)
                if isinstance(alias, str) and alias.strip():
                    self.aliases[student] = alias.strip()
        self.pending_changes = {}
        self.game_size = len(students)
        for student in students:
            self.pending_changes[student] = True
        self.changes_made = 0
        #if Network == None:
        #    self.graph = nx.Graph()
        #    
        #else:
        self.graph = nx.DiGraph()  # Se fuerza explícitamente como grafo dirigido
        if os.path.getsize(Network) > 0:
            graph_from_file = nx.read_edgelist(Network, create_using=nx.DiGraph())
            self.graph.add_edges_from(graph_from_file.edges())  # Añadir explícitamente las aristas del archivo

        self.graph.add_nodes_from(self.students)  # Esto asegura la existencia de nodos siempre
        nx.set_node_attributes(self.graph, name='alias', values=self.aliases)
            
        
        
    def new_change(self, student, add1, add2, rem = None):
        decided = student.decided
        if add1 != None or add2 != None:
            if add1 != add2 and (not decided):
                student.add_changes(add1, add2, rem)
                self.pending_changes[student.id] = False
                self.changes_made+=1
                return True,"Changes added."
            elif add1 == add2:
                return False,"New connections must be different."
            else:
                return False, "You already made changes."
        else:
            if (not decided):
                student.add_changes(add1, add2, rem)
                self.pending_changes[student.id] = False
                self.changes_made+=1
                return True,"Changes added."
            else:
                return False, "You already made changes."   
            
    def apply_changes(self, students):
        
        if self.round > 0:
            to_add = []
            to_remove = []
            for student in students:
                if student.add1 is not None:
                    to_add.append((student.id, student.add1))
                if student.add2 is not None:
                    to_add.append((student.id, student.add2))
                if student.rem is not None:
                    to_remove.append((student.id, student.rem))

                self.pending_changes[student.id] = False

            missing_students = [x for x in self.students if self.pending_changes[x]]

            for ID in missing_students:
                unconnected = self.unconnectedOF(ID)
                connected = self.connectionsOF(ID)

                np.random.shuffle(unconnected)
                np.random.shuffle(connected)

                if len(unconnected) >= 2:
                    to_add.append((ID, unconnected.pop()))
                    to_add.append((ID, unconnected.pop()))
                elif len(unconnected) == 1:
                    to_add.append((ID, unconnected.pop()))

                if len(connected) >= 1:
                    to_remove.append((ID, connected.pop()))

            # Asegurar eliminación de duplicados
            to_add = list(set(to_add))
            to_remove = list(set(to_remove))

            self.graph.remove_edges_from(to_remove)
            self.graph.add_edges_from(to_add)
            self.changes_made = 0
            self.round += 1
            return True

            
        elif self.round == 0:
            to_add = []

            for student in students:
                if student.add1 is not None:
                    to_add.append((student.id, student.add1))
                if student.add2 is not None:
                    to_add.append((student.id, student.add2))

                self.pending_changes[student.id] = False

            missing_students = [x for x in self.students if self.pending_changes[x]]

            for ID in missing_students:
                unconnected = self.unconnectedOF(ID)
                
                np.random.shuffle(unconnected)  # mezcla para aleatoriedad segura

                if len(unconnected) >= 2:
                    to_add.append((ID, unconnected.pop()))
                    to_add.append((ID, unconnected.pop()))
                elif len(unconnected) == 1:
                    to_add.append((ID, unconnected.pop()))

            # antes de añadir, verificar duplicados
            to_add = list(set(to_add))
            
            self.graph.add_edges_from(to_add)
            self.changes_made = 0
            self.round += 1
            return True

        
        else:
            
            return False
    
    def connectionsOF(self, studentID):
        return list(self.graph.neighbors(studentID))
    
    def unconnectedOF(self, studentID):
        connected = self.connectionsOF(studentID)
        connected.append(studentID)
        return [x for x in self.students if (x not in connected)]
    
    def save_network(self, path):
        
        with open(path, "wb") as f:
            nx.readwrite.edgelist.write_edgelist(self.graph, f)
            f.close()
        return True
    
    def compute_ranking(self):
        indegree = dict(self.graph.in_degree())
        outdegree = dict(self.graph.out_degree())
        clustering = nx.algorithms.cluster.clustering(self.graph.to_undirected())
        between = nx.algorithms.centrality.betweenness_centrality(self.graph, normalized=True)
        
        nx.set_node_attributes(self.graph, name='indegree', values=indegree)
        nx.set_node_attributes(self.graph, name='outdegree', values=outdegree)
        nx.set_node_attributes(self.graph, name='clustering', values=clustering)
        nx.set_node_attributes(self.graph, name='BTC', values=between)
        
        return True
    
    def visualize(self):
        in_degree = dict(self.graph.in_degree())
        uniform_node_size = {node: 18 for node in self.graph.nodes()}
        nx.set_node_attributes(self.graph, name='adjusted_node_size', values=uniform_node_size)

        node_highlight_color = 'blue'
        size_by_this_attribute = 'adjusted_node_size'
        title = 'Game of Networks Round ' + str(self.round)

        HOVER_TOOLTIPS = [
            ("User ID", "@index"),
            ("Alias", "@alias"),
            ("Indegree", "@indegree"),
            ("Outdegree", "@outdegree"),
            ("Clustering coefficient", "@clustering"),
            ("Betwenness Centrality", "@BTC"),
        ]


        plot = figure(tooltips=HOVER_TOOLTIPS,
                    tools="pan,wheel_zoom,save,reset",
                    active_scroll='wheel_zoom',
                    title=title)

        components = [sorted(comp) for comp in nx.weakly_connected_components(self.graph)]
        components.sort(key=len, reverse=True)

        graph_layout = {}
        if components:
            spacing_x = 6.5
            spacing_y = 5.5
            cols = max(1, math.ceil(math.sqrt(len(components))))
            for idx, comp in enumerate(components):
                subgraph = self.graph.subgraph(comp)
                local_layout = nx.spring_layout(
                    subgraph,
                    k=max(0.6, 2.0 / math.sqrt(max(1, len(comp)))),
                    seed=42,
                    iterations=80,
                )
                row = idx // cols
                col = idx % cols
                offset_x = col * spacing_x
                offset_y = -row * spacing_y
                for node, (x, y) in local_layout.items():
                    graph_layout[node] = (x + offset_x, y + offset_y)

        network_graph = from_networkx(self.graph, graph_layout, scale=1, center=(0, 0))

        network_graph.node_renderer.glyph = Circle(size=size_by_this_attribute, fill_color="#3288bd", fill_alpha=0.95)
        network_graph.node_renderer.hover_glyph = Circle(size=size_by_this_attribute, fill_color=node_highlight_color, line_width=2)
        network_graph.node_renderer.selection_glyph = Circle(size=size_by_this_attribute, fill_color=node_highlight_color, line_width=2)

        network_graph.edge_renderer.glyph = MultiLine(line_alpha=0.25, line_width=1.2, line_color="#4d4d4d")

        network_graph.selection_policy = NodesAndLinkedEdges()
        network_graph.inspection_policy = NodesAndLinkedEdges()

        plot.renderers.append(network_graph)

        if graph_layout:
            x_vals = [x for x, _ in graph_layout.values()]
            y_vals = [y for _, y in graph_layout.values()]
            x_pad = 1.2
            y_pad = 1.2
            plot.x_range = Range1d(min(x_vals) - x_pad, max(x_vals) + x_pad)
            plot.y_range = Range1d(min(y_vals) - y_pad, max(y_vals) + y_pad)

        plot.xaxis.visible = False
        plot.yaxis.visible = False
        plot.xgrid.visible = False
        plot.ygrid.visible = False
        plot.outline_line_alpha = 0.35

        node_labels = list(self.graph.nodes())
        rank_by_indegree = sorted(node_labels, key=lambda node: (-in_degree.get(node, 0), node))
        highlighted_nodes = set(rank_by_indegree[:max(8, len(node_labels) // 3)])
        label_nodes = [node for node in node_labels if node in highlighted_nodes]

        x = [network_graph.layout_provider.graph_layout[node][0] for node in label_nodes]
        y = [network_graph.layout_provider.graph_layout[node][1] for node in label_nodes]
        source = ColumnDataSource(
            {
                'x': x,
                'y': y,
                'name': [self.aliases.get(node, node) for node in label_nodes],
            }
        )
        labels = LabelSet(x='x', y='y', text='name', source=source, background_fill_color='white',
                        text_font_size='10px', background_fill_alpha=0.9, render_mode='canvas', y_offset=6)
        plot.renderers.append(labels)

        # Flechas pequeñas y discretas
        from bokeh.models import Arrow, NormalHead

        for start_node, end_node in self.graph.edges():
            plot.add_layout(Arrow(end=NormalHead(size=6, fill_color="#555555"),
                                line_alpha=0.45, line_width=1,
                                x_start=network_graph.layout_provider.graph_layout[start_node][0],
                                y_start=network_graph.layout_provider.graph_layout[start_node][1],
                                x_end=network_graph.layout_provider.graph_layout[end_node][0],
                                y_end=network_graph.layout_provider.graph_layout[end_node][1]))

        return plot

        
class Student:
    
    def __init__(self, id):
        self.id = id
        self.add1 = None
        self.add2 = None
        self.rem = None
        self.decided = False
        
    def add_changes(self, add1, add2, rem= None):
        if not self.decided:
            self.add1 = add1
            self.add2 = add2
            self.rem = rem
            self.decided = True
            return True
        return False
    
    def reset_changes(self):
        self.add1 = None
        self.add2 = None
        self.rem = None
        self.decided = False
        
        
        
        
