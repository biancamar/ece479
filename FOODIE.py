import networkx as nx
import matplotlib.pyplot as plt
import random
import numpy as np
from queue import PriorityQueue

# Define the items list
self.items_list = [
    {"name": "1 gallon water bottle", "size": "large", "frozen": False},
    {"name": "watermelon", "size": "large", "frozen": False},
    {"name": "ice cream", "size": "medium", "frozen": True},
    # Add more items as needed
]

class Robot:
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.path = []
        self.order = None
        self.charge = 100  # Add the charge attribute
        self.charging_ticks = 0
        self.loading_ticks = 0

class FOODIE:
    def __init__(self, terrain, num_robots):
        self.terrain = terrain
        self.robots = [Robot(f"ROBOT {i}", "FW") for i in range(num_robots)]
        self.orders = PriorityQueue()
        self.pos = nx.spring_layout(self.terrain)
        self.obstacles = []
        self.order_locations = {}
        self.low_battery_level = 20  # Add a low battery level (20% as an example)

    def add_order(self, location):
        priority = random.random()
        self.orders.put((priority, location))
        self.order_locations[location] = "WAITING"

    def plan_route(self, robot):
        if self.orders.empty() or robot.path:
            return
        if robot.charge <= self.low_battery_level:  # Check if the robot needs to charge
            return
        order = self.orders.get()[1]
        try:
            path_to_order = nx.astar_path(self.terrain, robot.location, order)
            path_to_FW = nx.astar_path(self.terrain, order, "FW")
            robot.path = path_to_order + path_to_FW[1:]
            robot.order = order
        except nx.NetworkXNoPath:
            print(f"No path found for {robot.name} to {order}.")
            self.add_order(order)

    def move_robot(self, robot):
        if robot.charging_ticks > 0:
            robot.charging_ticks -= 1
            if robot.charging_ticks == 0:
                robot.charge = 100  # Fully charged
            print(f"{robot.name} charging at FW. Charge: {robot.charge}%")
            return

        if robot.loading_ticks > 0:
            robot.loading_ticks -= 1
            if robot.loading_ticks == 0:
                robot.path.pop(0)  # Remove "loading" state
            print(f"{robot.name} loading compartment at FW.")
            return

        if robot.path:
            next_node = robot.path[0]
            if next_node == "loading":
                robot.loading_ticks = 1
            else:
                robot.path.pop(0)
                robot.location = next_node
                robot.charge -= 1  # Decrease the charge by 10 for each step

                if robot.location == robot.order:
                    self.order_locations[robot.order] = f"Delivered by {robot.name}"
                    robot.order = "FW"

        if robot.location == "FW" and robot.charge <= 20:
            robot.charging_ticks = 5  # Set the charging_ticks to 5

    def simulate(self):
        while not self.orders.empty():
            for robot in self.robots:
                self.plan_route(robot)
                self.move_robot(robot)
            self.draw_terrain()
            print("Order Status:")
            for location, status in self.order_locations.items():
                print(f"Order at {location}: {status}")
            plt.pause(.1)

    def draw_terrain(self):
        plt.clf()
        nx.draw(self.terrain, self.pos, with_labels=True, node_color='#83AF9B', node_size=1000, font_size=14, font_weight='bold', font_color='white')

        for i, robot in enumerate(self.robots):
            if robot.location in self.pos:
                offset = i * 0.03
                label = f"{robot.name} ({robot.charge}%)"
                if robot.path:
                    label += " -> " + ("RETURNING" if robot.order == "FW" and robot.path[-1] == "FW" else str(robot.order))
                plt.text(self.pos[robot.location][0]+offset, self.pos[robot.location][1], label, fontsize=12, color='red')

        for location, status in self.order_locations.items():
            if status == "WAITING":
                nx.draw_networkx_nodes(self.terrain, self.pos, nodelist=[location], node_color='#F3E0BE', node_size=1500, node_shape='o')
                nx.draw_networkx_labels(self.terrain, self.pos, {location: "ORDER"}, font_size=12, font_weight='bold', font_color='black')
            else:
                nx.draw_networkx_nodes(self.terrain, self.pos, nodelist=[location], node_color='#83AF9B', node_size=1500, node_shape='o')

        for u, v in self.obstacles:
            x1, y1 = self.pos[u]
            x2, y2 = self.pos[v]
            plt.plot([x1, x2], [y1, y2], 'r--')

        plt.gca().set_title("Orders and Status:")
        order_list_text = ""
        for location, status in self.order_locations.items():
            assigned_robot = None
            for robot in self.robots:
                if robot.order == location:
                    assigned_robot = robot.name
                    break
            order_list_text += f"Order at {location} - Status: {status} - Assigned to: {assigned_robot if assigned_robot else 'Not assigned'}\n"
        plt.gca().text(0.02, 0.02, order_list_text, fontsize=10, color='black', transform=plt.gca().transAxes)

        plt.show(block=False)

def create_random_obstacles(G, p):
    obstacles = []
    for (u, v) in list(G.edges):
        if random.random() < p:
            G.remove_edge(u, v)
            if not nx.is_connected(G):
                G.add_edge(u, v)
            else:
                obstacles.append((u, v))
    return obstacles

def create_tree_graph_with_obstacles(b, h, p):
    G = create_tree_graph(b, h)
    obstacles = create_random_obstacles(G, p)
    return G, obstacles

def create_tree_graph(b, h):
    G = nx.Graph()
    total_nodes = (b ** (h + 1) - 1) // (b - 1)
    nodes = np.arange(1, total_nodes + 1, dtype=int)
    edges = []

    for i, node in enumerate(nodes[:-1]):
        for j in range(1, b + 1):
            idx = i * b + j
            if idx >= len(nodes):
                break
            child = nodes[idx]
            edges.append((node, child))

    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    return G


def main():
    b = 2  # branching factor
    h = 6  # height of the tree
    G, obstacles = create_tree_graph_with_obstacles(b, h, 0.1)  # 10% chance to remove an edge
    G = nx.relabel_nodes(G, {node: str(node) for node in G.nodes()})

    G.add_node("FW")
    random_node = random.choice([node for node in G.nodes() if node != "FW"])
    G.add_edge("FW", random_node)

    foodie = FOODIE(G, 3)
    foodie.obstacles = obstacles
    foodie.pos = nx.spring_layout(G)  # Calculate positions only once
    for _ in range(100):
        foodie.add_order(random.choice(list(G.nodes)))
        foodie.simulate()

if __name__ == "__main__":
    main()
