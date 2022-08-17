import random
import math
import numpy as np
from src.client import GameClient
from src.model import GameView
from src import hide_and_seek_pb2


INF = float('inf')
PR_STAY = 10


def write(txt):
    f = open("logs/log_opponent1.log", "a")
    f.write(txt)
    f.write('\n')
    f.close()


def convert_paths_to_adj(paths, n, normalize=False):

    inf = float('inf')
    adj = [[inf for j in range(n+1)] for i in range(n+1)]

    min_price = inf
    for path in paths:
        adj[path.first_node_id][path.second_node_id] = path.price + 1
        adj[path.second_node_id][path.first_node_id] = path.price + 1
        if path.price < min_price:
            min_price = path.price + 1

    for i in range(n+1):
        adj[i][i] = 0

    # Price normalization: All/Min
    if normalize:
        if min_price != 0:
            for i in range(n+1):
                for j in range(n+1):
                    adj[i][j] /= min_price

    # write(str(adj))
    return adj


def floyd_warshall(paths, n, mode="price") -> list:
    """mode: price, distance"""
    # TODO: mix floyd warshall distance and price

    D = convert_paths_to_adj(paths, n, True)

    if mode == "distance":
        for i in range(len(D)):
            for j in range(len(D[0])):
                if D[i][j] and D[i][j] != INF:
                    D[i][j] = 1

    inf = float('inf')
    for k in range(n+1):
        for i in range(n+1):
            for j in range(n+1):
                if D[i][k] < inf and D[k][j] < inf:
                    D[i][j] = min(D[i][j], D[i][k] + D[k][j])

    return D


def minDistance(dist, queue):
    minimum = float("Inf")
    min_index = -1

    for i in range(1, len(dist)):
        if dist[i] < minimum and i in queue:
            minimum = dist[i]
            min_index = i
    return min_index


def dijkstra(graph, source_node_id, target_node_id) -> [int]:
    row = len(graph)
    col = len(graph[0])

    dist = [float("Inf")] * row
    parent = [-1] * row
    dist[source_node_id] = 0

    queue = []
    for i in range(1, row):
        queue.append(i)

    while queue:
        u = minDistance(dist, queue)
        queue.remove(u)

        for i in range(1, col):
            is_one = 1 if graph[u][i] >= 0 and graph[u][i] != INF else 0
            if is_one and i in queue:
                if dist[u] + is_one < dist[i]:
                    dist[i] = dist[u] + is_one
                    parent[i] = u

    path = []
    node = target_node_id
    while parent[node] != -1:
        path.append(node)
        node = parent[node]
    path.append(node)
    return path


def get_thief_starting_node(view: GameView) -> int:
    # method 1
    # return random.randint(2, len(view.config.graph.nodes))

    # method 2
    # count_thieves = 0
    # team = view.viewer.team
    # for agent in view.visible_agents:
    #     if agent.agent_type == hide_and_seek_pb2.AgentType.THIEF and agent.team == team:
    #         count_thieves += 1

    # i = int(len(view.config.graph.nodes)/count_thieves)
    # st_node = random.randint(i*view.viewer.id, i*view.viewer.id+i)
    # # write(str(view.viewer.id) + " -> " + str(st_node))
    # return st_node

    # method 3
    # count_node = len(view.config.graph.nodes)
    # start_node = 1
    # while start_node == 1 or start_node > count_node:
    #     rand = np.random.uniform(low=0, high=1)
    #     start_node = int(rand * count_node) + 1
    # return start_node

    # method 4 sampling from beta distribution
    # np.random.beta(a=5,b=2) -> replace with above sampling method

    # method 5 select ith furthest node from police station for ith thief
    count_node = len(view.config.graph.nodes)
    distances = floyd_warshall(
        view.config.graph.paths, count_node, mode="distance")

    police_distances = distances[1]
    police_distances[0] = -1

    argsorted_distances = np.argsort(police_distances)
    # write("Distances: "+str(distances))
    # write("Argsort: "+str(argsorted_distances))
    # write(str(view.viewer.id) + " -> " +
    #       str(argsorted_distances[-view.viewer.id]))
    # write("distance: " +
    #       str(police_distances[argsorted_distances[-view.viewer.id]]))
    return argsorted_distances[-view.viewer.id]


class Phone:
    def __init__(self, client: GameClient):
        self.client = client

    def send_message(self, message):
        self.client.send_message(message)


class AI:
    def __init__(self, view: GameView, phone: Phone):
        self.phone = phone
        self.cost = None
        self.floyd_warshall_matrix = None
        self.degrees = None
        self.police_target = None

    def get_degrees(self, view: GameView) -> list:
        nodes_count = len(view.config.graph.nodes)
        degrees = [0]*(nodes_count+1)
        for n in range(1, nodes_count+1):
            for adj in range(1, nodes_count+1):
                if self.cost[n][adj] != INF and adj != n:
                    degrees[n] += 1
        return degrees

    def get_adjacents(self, node_id, view: GameView) -> list:
        nodes_count = len(view.config.graph.nodes)
        neighbours = []
        for adj_id in range(1, nodes_count+1):
            if self.cost[node_id][adj_id] != INF and adj_id != node_id:
                neighbours.append(adj_id)
        return neighbours

    def police_count_all(self, view: GameView) -> int:
        pc = 0
        for vu in view.visible_agents:
            if(vu.agent_type == hide_and_seek_pb2.AgentType.POLICE and vu.team != view.viewer.team):
                pc += 1
        pc += 1
        return pc

    def get_opponent_polices_nodes(self, view: GameView) -> list:
        polices_nodes = []
        for vu in view.visible_agents:
            if(vu.agent_type == hide_and_seek_pb2.AgentType.POLICE and vu.team != view.viewer.team):
                polices_nodes.append(vu.node_id)
        return polices_nodes

    def police_count_node(self, node_id, team, view: GameView) -> int:
        pc = 0
        for vu in view.visible_agents:
            if (
                not vu.is_dead and
                vu.node_id == node_id and
                vu.agent_type == hide_and_seek_pb2.AgentType.POLICE and
                vu.team == team
            ):
                pc += 1
        return pc

    def thieves_count_node(self, node_id, team, view: GameView) -> int:
        tc = 0
        for vu in view.visible_agents:
            if (
                not vu.is_dead and
                vu.node_id == node_id and
                vu.agent_type == hide_and_seek_pb2.AgentType.THIEF and
                vu.team == team
            ):
                tc += 1
        return tc

    def pr_police(self, node_id, team_type: str, view: GameView) -> float:
        pr = 1
        nodes_count = len(view.config.graph.nodes)
        adjacents = self.get_adjacents(node_id, view)
        adjacents.append(node_id)
        for adj_id in adjacents:
            #write(f"node_id = {node_id}, adj_id = {adj_id}, len = {len(self.cost)}, {len(self.cost[0])}")
            # if self.cost[node_id][adj_id] != INF:  # ERROR sometimes!
            p_count = None
            if team_type == "same":
                p_count = self.police_count_node(
                    adj_id, view.viewer.team, view)
            else:
                if view.viewer.team == hide_and_seek_pb2.Team.FIRST:
                    p_count = self.police_count_node(
                        adj_id, hide_and_seek_pb2.Team.SECOND, view)
                else:
                    p_count = self.police_count_node(
                        adj_id, hide_and_seek_pb2.Team.FIRST, view)

            pr += p_count / self.degrees[adj_id]
        return pr

    def pr_theives(self, node_id, team_type: str, view: GameView) -> float:
        pr = 1
        if view.turn.turn_number not in view.config.visible_turns:
            return pr

        nodes_count = len(view.config.graph.nodes)
        adjacents = self.get_adjacents(current_node, view)
        adjacents.append(current_node)
        for adj_id in adjacents:
            t_count = None
            if team_type == "same":
                t_count = self.thieves_count_node(
                    adj_id, view.viewer.team, view)
            else:
                if view.viewer.team == hide_and_seek_pb2.Team.FIRST:
                    t_count = self.thieves_count_node(
                        adj_id, hide_and_seek_pb2.Team.SECOND, view)
                else:
                    t_count = self.thieves_count_node(
                        adj_id, hide_and_seek_pb2.Team.FIRST, view)

            pr += t_count / self.degrees[adj_id]
        return pr

    def thief_move_ai(self, view: GameView) -> int:
        current_node = view.viewer.node_id
        nodes_count = len(view.config.graph.nodes)
        if self.cost is None:
            self.cost = convert_paths_to_adj(
                view.config.graph.paths, nodes_count)
        if self.degrees is None:
            self.degrees = self.get_degrees(view)
        if self.floyd_warshall_matrix is None:
            self.floyd_warshall_matrix = floyd_warshall(
                view.config.graph.paths, nodes_count)

        # TODO: dozd az police door she

        police_distances = {}
        for police_node in self.get_opponent_polices_nodes(view):
            police_distances[police_node] = self.floyd_warshall_matrix[current_node][police_node]

        shortest_dist = min(police_distances.values())
        nearest_police = random.choice(
            [k for k, v in police_distances.items() if v == shortest_dist])

        nearest_police_to_adjacents = {}
        adjacents = self.get_adjacents(current_node, view)
        adjacents.append(current_node)
        for adj_id in adjacents:
            nearest_police_to_adjacents[adj_id] = self.floyd_warshall_matrix[adj_id][nearest_police]
        write(f"{nearest_police_to_adjacents=}")
        furthest_dist_to_police = max(nearest_police_to_adjacents.values())
        furthest_adjacents = [
            k for k, v in nearest_police_to_adjacents.items() if v == furthest_dist_to_police]
        if furthest_adjacents:
            move_to = random.choice(furthest_adjacents)
            write(f"{move_to=}")
            return move_to
        else:
            # TODO: idk
            h = {}      # h(next) = (prob. Of polices)
            current_node = view.viewer.node_id
            adjacents = self.get_adjacents(current_node, view)
            adjacents.append(current_node)
            for adj_id in adjacents:
                h[adj_id] = self.pr_police(adj_id, "opp", view)

            min_h = min(h.values())
            move_to = current_node
            if min_h != INF:
                min_nodes = [k for k, v in h.items() if v == min_h]
                move_to = random.choice(min_nodes)

            # write("Thief: "+str(h))
            # write("Thief with id " + str(view.viewer.id) + " in node " +
            #       str(current_node) + " move to " + str(move_to))
            return move_to

    def find_target_police(self, view: GameView):
        nodes_count = len(view.config.graph.nodes)
        current_node = view.viewer.node_id

        thieves_nodes = [thief.node_id for thief in view.visible_agents
                         if (thief.agent_type == hide_and_seek_pb2.AgentType.THIEF and
                             thief.team != view.viewer.team)]

        if view.turn.turn_number in view.config.visible_turns:
            fwarshal_mat = self.floyd_warshall_matrix
            min_dist = INF
            move_to = []
            for node_id in thieves_nodes:
                if fwarshal_mat[current_node][node_id] < min_dist and node_id != current_node:
                    move_to.clear()
                    min_dist = fwarshal_mat[current_node][node_id]
                    move_to.append(node_id)
                elif fwarshal_mat[current_node][node_id] == min_dist and node_id != current_node:
                    move_to.append(node_id)
            write(
                f"moveto test : {move_to}, distance = {fwarshal_mat[current_node][move_to[0]]}")

            return random.choice(move_to)
        else:
            if self.police_target is None:
                nexts = []
                for adj_id in self.get_adjacents(current_node, view):
                    nexts.append(adj_id)

                return random.choice(nexts)
            else:
                return self.police_target

    def police_move_ai(self, view: GameView) -> int:
        nodes_count = len(view.config.graph.nodes)
        current_node = view.viewer.node_id

        if self.cost is None:
            self.cost = convert_paths_to_adj(
                view.config.graph.paths, len(view.config.graph.nodes))
        if self.degrees is None:
            self.degrees = self.get_degrees(view)

        if self.police_target == current_node:
            self.police_target = None
        if self.floyd_warshall_matrix is None:
            self.floyd_warshall_matrix = floyd_warshall(
                view.config.graph.paths, nodes_count)

        self.police_target = self.find_target_police(view)

        path = dijkstra(self.cost, current_node, self.police_target)
        if len(path) > 1:
            # write(
            #     f"agent id={view.viewer.id}, {current_node=}, {self.police_target=}, {path= }, go to {path[-2]}")
            return path[-2]
        else:
            # TODO: police ha az hamdige door beshan avvale bazi
            # TODO: --> less important random nare age dozd gereft. be samte dozde badi bere.
            adjacents = self.get_adjacents(current_node, view)
            adjacents.append(current_node)
            return random.choice(adjacents)

        # h = {}  # h(x) = (cost * pr_police) / (pr_thieves * degree)
        # h[current_node] = self.pr_theives(current_node, "opp", view)
        # for adj_id in range(1, nodes_count+1):
        #     h[adj_id] = INF
        #     if self.cost[current_node][adj_id] != INF and adj_id != current_node:
        #         h[adj_id] = self.pr_theives(adj_id, "opp", view)

        # min_h = min(h.values())
        # move_to = current_node
        # if min_h != INF:
        #     min_nodes = [k for k, v in h.items() if v == min_h]
        #     move_to = random.choice(min_nodes)

        # write("Police: " + str(h))
        # write("Police with id " + str(view.viewer.id) + " in node " +
        #     str(current_node) + " move to " + str(move_to))
        # return move_to
