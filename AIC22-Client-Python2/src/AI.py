import random
import math
import numpy as np
from src.client import GameClient
from src.model import GameView
from src import hide_and_seek_pb2
from src.model import AgentType

INF = float('inf')
PR_STAY = 10


#FIRST -> BLUE

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


def floyd_warshall(paths, n, mode="distance") -> list:
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


def dijkstra(graph, source_node_id, target_node_id) -> list:
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
    thieves_ids = [view.viewer.id]
    team = view.viewer.team
    for agent in view.visible_agents:
        if agent.agent_type % 2== 0 and agent.team == team:
            thieves_ids.append(agent.id)

    count_node = len(view.config.graph.nodes)
    distances = floyd_warshall(
        view.config.graph.paths, count_node, mode="distance")

    police_distances = distances[1]
    police_distances[0] = -1
    
    argsorted_distances = np.argsort(police_distances)

    return argsorted_distances[-((((view.viewer.id - min(thieves_ids) + 1) * 2) - 1) % len(view.config.graph.nodes))]


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
        self.prev_nodes = []
        self.view = view
        self.visible_thieves = []
        # write(str(dir(view.viewer)))

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
            if(vu.agent_type % 2 == 1 and vu.team != view.viewer.team):
                pc += 1
        pc += 1
        return pc

    def get_units(self, view:GameView, agent_type:AgentType, team: str, return_type: str): #team == true : ours #
        results = []
        # write("test")
        # write("test " + str(view.viewer.agent_type) + str([v.agent_type for v in view.visible_agents]))
        for vu in view.visible_agents:
        # write(f'{vu.agent_type}')
            if team == "same" and vu.team == view.viewer.team and vu.agent_type % 2 == agent_type % 2 and not vu.is_dead:
                if return_type == "node":
                    results.append(vu.node_id)
                else:
                    results.append(vu.id)

            if team == "opp" and vu.team != view.viewer.team and vu.agent_type % 2== agent_type % 2 and not vu.is_dead:
                if return_type == "node":
                    results.append(vu.node_id)
                else:
                    results.append(vu.id)

        return results

    def police_count_node(self, node_id, team, view: GameView) -> int:
        pc = 0
        for vu in view.visible_agents:
            if (
                not vu.is_dead and
                vu.node_id == node_id and
                vu.agent_type % 2 == 1 and
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
                vu.agent_type % 2 == 0 and
                vu.team == team
            ):
                tc += 1
        return tc

    def isThiefin(self, node_id, view: GameView) -> bool:
        for t in view.visible_agents:
            if t.agent_type % 2 == 0 and self.view.viewer.team == t.team and t.node_id == node_id:
                return True
        return False

    def isPolicein(self, node_id, view: GameView, same_team: bool = False) -> bool:
        for t in view.visible_agents:
            if same_team:
                if t.agent_type % 2== 1 and self.view.viewer.team == t.team and t.node_id == node_id:
                    return True
            else:
                if t.agent_type % 2 == 1 and self.view.viewer.team != t.team and t.node_id == node_id:
                    return True
        return False
    
    def thief_move_ai(self, view: GameView) -> int:
        nodes_count = len(view.config.graph.nodes)
        if self.cost is None:
            self.cost = convert_paths_to_adj(
                view.config.graph.paths, nodes_count)

        current_node = view.viewer.node_id
        nexts = []
        for adj_id in range(1, nodes_count+1):
            if self.cost[current_node][adj_id] != INF:
                nexts.append(adj_id)

        move_to = nexts[random.randint(0, len(nexts)-1)]
        # write("Thief with id " + str(view.viewer.id) + " in node " +
        #       str(current_node) + " move to " + str(move_to))
        return move_to



    
    def police_move_ai(self, view: GameView) -> int:
        nodes_count = len(view.config.graph.nodes)
        if self.cost is None:
            self.cost = convert_paths_to_adj(
                view.config.graph.paths, len(view.config.graph.nodes))

        current_node = view.viewer.node_id
        nexts = []
        for adj_id in range(1, nodes_count+1):
            if self.cost[current_node][adj_id] != INF:
                nexts.append(adj_id)

        move_to = nexts[random.randint(0, len(nexts)-1)]
        # write("Police with id " + str(view.viewer.id) + " in node " +
        #       str(current_node) + " move to " + str(move_to))
        return move_to
