import networkx as nx
import matplotlib.pyplot as plt
import random
from queue import PriorityQueue

class Robot:
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.path = []
        self.order = None  # Add an order attribute

class FOODIE:
    def __init__(self, terrain, num_robots):
        self.terrain = terrain
        self.robots = [Robot(f"ROBOT {i}", "FW") for i in range(num_robots)]
        self.orders = PriorityQueue()
        self.pos = nx.spring_layout(self.terrain)  # Calculate positions only once
        self.obstacles = []
        self.order_locations = {}  # New dictionary to keep track of orders


    def add_order(self, location):
        # Random priority for demo
        priority = random.random()
        self.orders.put((priority, location))
        self.order_locations[location] = "WAITING"

        # FIX NO ORDERS SHOULD HAPPEN ON FW


    def plan_route(self, robot):
        # If no orders or robot is currently delivering, do nothing
        if self.orders.empty() or robot.path:
            return
        order = self.orders.get()[1]
        try:
            path_to_order = nx.astar_path(self.terrain, robot.location, order)
            path_to_FW = nx.astar_path(self.terrain, order, "FW")
            robot.path = path_to_order + path_to_FW[1:]  # Combine the paths
            robot.order = order  # Set the order to be the final destination
        except nx.NetworkXNoPath:
            print(f"No path found for {robot.name} to {order}.")
            self.add_order(order)  # Re-add the order to the queue

    def move_robot(self, robot):
        if robot.path:
            next_node = robot.path.pop(0)
            print(f"{robot.name} moving from {robot.location} to {next_node}.")
            robot.location = next_node
        if robot.location == robot.order:
            self.order_locations[robot.order] = f"Delivered by {robot.name}"
            robot.order = "FW"  # Update the order to indicate the robot is returning to FW


    def simulate(self):
        while not self.orders.empty():
            for robot in self.robots:
                self.plan_route(robot)
                self.move_robot(robot)
            self.draw_terrain()
            print("Order Status:")
            for location, status in self.order_locations.items():
                print(f"Order at {location}: {status}")
            plt.pause(.25)

    def draw_terrain(self):
        plt.clf()
        nx.draw(self.terrain, self.pos, with_labels=True, node_color='#83AF9B', node_size=1000, font_size=14, font_weight='bold', font_color='white')
        for i, robot in enumerate(self.robots):
            if robot.location in self.pos:
                offset = i * 0.03  # adjust the value as needed
                label = robot.name
                if robot.path:  # check if robot has a path
                    # Check if the robot is returning to FW or going to an order
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
            plt.plot([x1, x2], [y1, y2], 'r--')  # 'r--' means red dashed line
        plt.show(block=False)




def create_random_obstacles(G, p):
    obstacles = []
    for (u, v) in list(G.edges):
        if random.random() < p:
            G.remove_edge(u, v)
            if not nx.is_connected(G):
                # If the graph is not connected, re-add the edge
                G.add_edge(u, v)
            else:
                obstacles.append((u, v))
    return obstacles

def main():
    G = nx.grid_2d_graph(10, 10)
    G = nx.convert_node_labels_to_integers(G, first_label=1, ordering="sorted")
    G = nx.relabel_nodes(G, {node: str(node) for node in G.nodes()})  # Convert node labels to strings
    G.add_node("FW")  # Add FW node
    random_node = random.choice([node for node in G.nodes() if node != "FW"])
    G.add_edge("FW", random_node)

    foodie = FOODIE(G, 3)  # 3 robots for demo
    foodie.obstacles = create_random_obstacles(G, 0.1)  # 20% chance to remove an edge
    for _ in range(10):  # 10 orders for demo
        foodie.add_order(random.choice(list(G.nodes)))
        foodie.simulate()

if __name__ == "__main__":
    main()
