from src.client import GameClient
from src.model import GameView
from src import hide_and_seek_pb2
import random
import pdb


INF = float('inf')


def convert_paths_to_adj(paths, n):

    inf = float('inf')
    adj = [[inf for j in range(n+1)] for i in range(n+1)]

    for path in paths:
        adj[path.first_node_id][path.second_node_id] = path.price
        adj[path.second_node_id][path.first_node_id] = path.price

    for i in range(n+1):
        adj[i][i] = 0

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
    # randome gheire tekrari
    return random.randint(1, len(view.config.graph.nodes))
    # write your code here
    # return 2


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

    # def get_degree(self, node_id, view: GameView) -> int:
    #     d = 0
    #     for adj in view.config.graph.paths:
    #         if adj.first_node_id == node_id:
    #             d += 1
    #     return d

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

        pr = 0.001
        # for pth in view.config.graph.paths:
        #     if pth.second_node_id == node_id:  # destination is current node
        nodes_count = len(view.config.graph.nodes)
        for adj_id in range(1, nodes_count+1):
            if self.cost[node_id][adj_id]:
                pr += self.police_count(adj_id, view) / \
                    self.degrees[adj_id]
        return pr

    def pr_theives(self, node_id, view: GameView) -> float:
        pr = 1
        # vt = [t for t in view.config.visible_turns]
        if view.turn.turn_number not in view.config.visible_turns:
            return pr

        # for pth in view.config.graph.paths:
        #     if pth.second_node_id == node_id:
        #   # destination is current node
        nodes_count = len(view.config.graph.nodes)
        for adj_id in range(1, nodes_count+1):
            if self.cost[node_id][adj_id]:
                pr += self.thieves_count(adj_id, view) / \
                    self.degrees[adj_id]
        return pr

    def thief_move_ai(self, view: GameView) -> int:
        nodes_count = len(view.config.graph.nodes)
        if self.cost is None:
            self.cost = convert_paths_to_adj(
                view.config.graph.paths, nodes_count)
        if self.degrees is None:
            self.degrees = self.get_degrees(view)
        # write your code here
        # message = ''
        # for m in range(len(view.visible_agents)):
        #     message = message  + '0'
        # self.phone.send_message(message)
        h = {}      # h(next) = cost * (prob. Of polices)
        current_node = view.viewer.node_id
        # for pth in view.config.graph.paths:
        #     if pth.first_node_id == current_node:

        for adj_id in range(1, nodes_count+1):
            if self.cost[current_node][adj_id] != INF:
                # adj_id = pth.first_node_id
                h[adj_id] = INF
                if self.degrees[adj_id] != 1 and view.balance > self.cost[current_node][adj_id]:
                    h[adj_id] = self.cost[current_node][adj_id] * \
                        self.pr_police(adj_id, view)

        min_h = INF
        move_to = -1
        for adj_id in h.keys():
            if h[adj_id] < min_h:
                min_h = h[adj_id]
                move_to = adj_id
        pdb.set_trace()

        if min_h != INF:
            return move_to
        else:
            return current_node  # Stay?

    def police_move_ai(self, view: GameView) -> int:
        nodes_count = len(view.config.graph.nodes)
        if self.cost is None:
            self.cost = convert_paths_to_adj(
                view.config.graph.paths, len(view.config.graph.nodes))
        if self.degrees is None:
            self.degrees = self.get_degrees(view)

        h = {}

        current_node = view.viewer.node_id
        # for pth in view.config.graph.paths:
        #     if pth.first_node_id == current_node:
        for adj_id in range(1, nodes_count+1):
            if self.cost[current_node][adj_id] != INF:
                # adj_id = pth.first_node_id
                h[adj_id] = INF
                if self.degrees[adj_id] != 1 and view.balance > self.cost[current_node][adj_id]:
                    h[adj_id] = self.cost[current_node][adj_id] * self.pr_police(adj_id, view) \
                        * (1-self.pr_theives(adj_id, view)) / self.degrees[adj_id]

        min_h = INF
        move_to = -1
        for adj_id in h.keys():
            if h[adj_id] < min_h:
                min_h = h[adj_id]
                move_to = adj_id

        if min_h != INF:
            return move_to
        else:
            return current_node  # Stay
