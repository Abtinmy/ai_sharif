from src.client import GameClient
from src.model import GameView
from src import hide_and_seek_pb2

INF = 10**9


def get_thief_starting_node(view: GameView) -> int:
    # write your code here
    return 2


class Phone:
    def __init__(self, client: GameClient):
        self.client = client

    def send_message(self, message):
        self.client.send_message(message)


class AI:
    def __init__(self, phone: Phone):
        self.phone = phone

    def get_degree(self, node_id, view: GameView) -> int:
        d = 0
        for adj in view.config.graph.paths:
            if adj.first_node_id == node_id:
                d += 1
        return d

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
        pr = 0.001
        for pth in view.config.graph.paths:
            if pth.second_node_id == node_id:  # destination is current node
                pr += self.police_count(pth.first_node_id, view) * \
                    self.get_degree(pth.first_node_id, view)
        return pr

    def pr_theives(self, node_id, view: GameView) -> float:
        pr = 1
        if GameView.turn.turnNumber in view.turnSettings.visibleTurns:
            return pr

        for pth in view.config.graph.paths:
            if pth.second_node_id == node_id:  # destination is current node
                pr += self.thieves_count(pth.first_node_id, view) * \
                    self.get_degree(pth.first_node_id, view)
        return pr

    def thief_move_ai(self, view: GameView) -> int:
        # write your code here
        # message = ''
        # for m in range(len(view.visible_agents)):
        #     message = message  + '0'
        # self.phone.send_message(message)
        h = {}      # h(next) = cost * (prob. Of polices)
        current_node = view.viewer.node_id
        for pth in view.config.graph.paths:
            if pth.first_node_id == current_node:
                adj_id = pth.first_node_id
                h[adj_id] = INF
                if self.get_degree(adj_id, view) != 1 and view.balance > pth.price:
                    h[adj_id] = pth.price * self.pr_police(adj_id, view)

        min_h = INF
        move_to = -1
        for adj_id in h.keys():
            if h[adj_id] < min_h:
                min_h = h[adj_id]
                move_to = adj_id

        if min_h != INF:
            return move_to
        else:
            return current_node  # Stay?

    def police_move_ai(self, view: GameView) -> int:
        # write your code here current_node = view.viewer.node_id
        # h(next) = cost * (pr. Of polices)*(1-pr. Of thieves)/d(next)
        h = {}
        current_node = view.viewer.node_id
        for pth in view.config.graph.paths:
            if pth.first_node_id == current_node:
                adj_id = pth.first_node_id
                h[adj_id] = INF
                if self.get_degree(adj_id, view) != 1 and view.balance > pth.price:
                    h[adj_id] = pth.price * self.pr_police(adj_id, view) \
                        * (1-self.pr_theives(adj_id, view)) / self.get_degree(adj_id, view)

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
