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

    def pr_police(self, node_id, view: GameView) -> float:
        pr = 0.001
        for pth in view.config.graph.paths:
            if pth.second_node_id == node_id:  # destination is node_id
                pr += self.police_count(pth.first_node_id, view) * \
                    self.get_degree(pth.first_node_id, view)
        return pr

    def thief_move_ai(self, view: GameView) -> int:
        # write your code here
        # message = ''
        # for m in range(len(view.visible_agents)):
        #     message = message  + '0'
        # self.phone.send_message(message)
        current_node = view.viewer.node_id
        h = {}
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
                move_to = adj_id

        if h[adj_id] != INF:
            return adj_id

        else:
            # means all degree 1 --> I think it's impossible OR price > current balance
            return -1  #Means stay there. how is it handled?!

    def police_move_ai(self, view: GameView) -> int:
        # write your code here
        
        # self.phone.send_message('00101001')
        return 1
