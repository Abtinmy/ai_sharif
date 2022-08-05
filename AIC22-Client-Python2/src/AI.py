import random
import math
from src.client import GameClient
from src.model import GameView
from src import hide_and_seek_pb2


INF = float('inf')
PR_STAY = 10


def write(txt):
    f = open("log_opponent2.log", "a")
    f.write(txt)
    f.write('\n')
    f.close()


def convert_paths_to_adj(paths, n):

    inf = float('inf')
    adj = [[inf for j in range(n+1)] for i in range(n+1)]

    min_price = inf
    for path in paths:
        adj[path.first_node_id][path.second_node_id] = path.price
        adj[path.second_node_id][path.first_node_id] = path.price
        if path.price < min_price:
            min_price = path.price

    for i in range(n+1):
        adj[i][i] = 0

    # Price normalization: All/Min
    if min_price != 0:
        for i in range(n+1):
            for j in range(n+1):
                adj[i][j] /= min_price

    write(str(adj))
    return adj


def floyd_warshall(paths, n):

    D = convert_paths_to_adj(paths, n)

    inf = float('inf')
    for k in range(n+1):
        for i in range(n+1):
            for j in range(n+1):
                if D[i][k] < inf and D[k][j] < inf:
                    D[i][j] = min(D[i][j], D[i][k] + D[k][j])

    return D


def get_thief_starting_node(view: GameView) -> int:
    return random.randint(2, len(view.config.graph.nodes))


class Phone:
    def __init__(self, client: GameClient):
        self.client = client

    def send_message(self, message):
        self.client.send_message(message)


class AI:
    def __init__(self, phone: Phone):
        self.phone = phone
        self.cost = None
        self.degrees = None

    def get_degrees(self, view: GameView) -> list:
        nodes_count = len(view.config.graph.nodes)
        degrees = [0]*(nodes_count+1)
        for n in range(1, nodes_count+1):
            for adj in range(1, nodes_count+1):
                if self.cost[n][adj] != INF:
                    degrees[n] += 1
        return degrees

    def police_count(self, node_id, view: GameView) -> int:
        pc = 0
        for vu in view.visible_agents:
            if not vu.is_dead and vu.node_id == node_id and vu.agent_type == hide_and_seek_pb2.AgentType.POLICE:
                pc += 1
        return pc

    def thieves_count(self, node_id, view: GameView) -> int:
        tc = 0
        for vu in view.visible_agents:
            if not vu.is_dead and vu.node_id == node_id and vu.agent_type == hide_and_seek_pb2.AgentType.THIEF:
                tc += 1
        return tc

    def pr_police(self, node_id, view: GameView) -> float:
        if self.degrees is None:
            self.degrees = self.get_degrees(view)

        pr = 1

        nodes_count = len(view.config.graph.nodes)
        for adj_id in range(1, nodes_count+1):
            if self.cost[node_id][adj_id] != INF:
                pr += self.police_count(adj_id, view) / \
                    self.degrees[adj_id]
        return pr

    def pr_theives(self, node_id, view: GameView) -> float:
        pr = 1

        if view.turn.turn_number not in view.config.visible_turns:
            return pr

        nodes_count = len(view.config.graph.nodes)
        for adj_id in range(1, nodes_count+1):
            if self.cost[node_id][adj_id] != INF:
                pr += self.thieves_count(adj_id, view) / \
                    self.degrees[adj_id]
        return pr

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
        write("Thief with id " + str(view.viewer.id) + " in node " +
              str(current_node) + " move to " + str(move_to))
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
        write("Police with id " + str(view.viewer.id) + " in node " +
              str(current_node) + " move to " + str(move_to))
        return move_to
