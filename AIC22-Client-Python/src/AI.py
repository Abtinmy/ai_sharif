import random
import math
from src.client import GameClient
from src.model import GameView
from src import hide_and_seek_pb2


INF = float('inf')
PR_STAY = 10
distances = None

def write(txt):
    f = open("log_opponent1.log", "a")
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

    #write(str(adj))
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
     #method 1
    # return random.randint(2, len(view.config.graph.nodes))

    # method 2
    count_thieves = 0
    team = view.viewer.team
    for agent in view.visible_agents:
      if agent.agent_type == hide_and_seek_pb2.AgentType.THIEF and agent.team == team:
        count_thieves += 1
    
    i = int(len(view.config.graph.nodes)/count_thieves)
    st_node = random.randint(i*view.viewer.id, i*view.viewer.id+i)
    write(str(view.viewer.id) + " -> " + str(st_node))
    return st_node

    # method 3
    # count_node = len(view.config.graph.nodes)
    # start_node = 1
    # while start_node == 1 or start_node > count_node:
    #   rand = np.random.uniform(low=0,high=1)
    #   start_node =  int(rand * count_node) + 1
    # return start_node
    
    # method 4 sampling from beta distribution
    # np.random.beta(a=5,b=2) -> replace with above sampling method
    
    
    # method 5 select ith furthest node from police station for ith thief
    # if distances == None:
    #   count_node = len(view.config.graph.nodes)
    #   distances = floyd_warshall(view.config.graph.paths, count_node)
  
    # police_distances = distances[1]
    # argsorted_distances = np.argsort(police_distances)

    # return argsorted_distances[-view.viewer.id]




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

    def police_count(self, node_id, team, view: GameView) -> int:
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

    def thieves_count(self, node_id, team, view: GameView) -> int:
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
        for adj_id in range(1, nodes_count+1):
            if self.cost[node_id][adj_id] != INF:
                p_count = None
                if team_type == "same":
                    p_count = self.police_count(adj_id, view.viewer.team, view)
                else:
                    if view.viewer.team == hide_and_seek_pb2.Team.FIRST:
                        p_count = self.police_count(
                            adj_id, hide_and_seek_pb2.Team.SECOND, view)
                    else:
                        p_count = self.police_count(
                            adj_id, hide_and_seek_pb2.Team.FIRST, view)

                pr += p_count / self.degrees[adj_id]
        return pr

    def pr_theives(self, node_id, team_type: str, view: GameView) -> float:
        pr = 1
        if view.turn.turn_number not in view.config.visible_turns:
            return pr

        nodes_count = len(view.config.graph.nodes)
        for adj_id in range(1, nodes_count+1):
            if self.cost[node_id][adj_id] != INF:
                t_count = None
                if team_type == "same":
                    t_count = self.thieves_count(
                        adj_id, view.viewer.team, view)
                else:
                    if view.viewer.team == hide_and_seek_pb2.Team.FIRST:
                        t_count = self.thieves_count(
                            adj_id, hide_and_seek_pb2.Team.SECOND, view)
                    else:
                        t_count = self.thieves_count(
                            adj_id, hide_and_seek_pb2.Team.FIRST, view)

                pr += t_count / self.degrees[adj_id]
        return pr

    def thief_move_ai(self, view: GameView) -> int:
        nodes_count = len(view.config.graph.nodes)
        if self.cost is None:
            self.cost = convert_paths_to_adj(
                view.config.graph.paths, nodes_count)
        if self.degrees is None:
            self.degrees = self.get_degrees(view)
       
        h = {}      # h(next) = cost * (prob. Of polices)
        current_node = view.viewer.node_id
        h[current_node] = self.pr_police(current_node, "opp", view)
        for adj_id in range(1, nodes_count+1):
            h[adj_id] = INF
            if self.cost[current_node][adj_id] != INF and adj_id != current_node:
                h[adj_id] = self.pr_police(adj_id, "opp", view)
            
        min_h = min(h.values())
        move_to = current_node
        if min_h != INF:
            min_nodes = [k for k, v in h.items() if v == min_h]
            move_to = random.choice(min_nodes)

        write("Thief: "+str(h))
        write("Thief with id " + str(view.viewer.id) + " in node " +
                str(current_node) + " move to " + str(move_to))
        return move_to

    def police_move_ai(self, view: GameView) -> int:
        nodes_count = len(view.config.graph.nodes)
        if self.cost is None:
            self.cost = convert_paths_to_adj(
                view.config.graph.paths, len(view.config.graph.nodes))
        if self.degrees is None:
            self.degrees = self.get_degrees(view)

        h = {}  # h(x) = (cost * pr_police) / (pr_thieves * degree)
        current_node = view.viewer.node_id
        h[current_node] = self.pr_theives(current_node, "opp", view)
        for adj_id in range(1, nodes_count+1):
            h[adj_id] = INF
            if self.cost[current_node][adj_id] != INF and adj_id != current_node:
                h[adj_id] = self.pr_theives(adj_id, "opp", view)
                
        min_h = min(h.values())
        move_to = current_node
        if min_h != INF:
            min_nodes = [k for k, v in h.items() if v == min_h]
            move_to = random.choice(min_nodes)

        write("Police: " + str(h))
        write("Police with id " + str(view.viewer.id) + " in node " +
            str(current_node) + " move to " + str(move_to))
        return move_to
