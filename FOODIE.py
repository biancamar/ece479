import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import random
import numpy as np
from queue import PriorityQueue

# Define the parameters of a robot
class Robot:
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.path = []
        self.order = None
        self.charge = 100
        # variables for the recharging process
        self.charging_ticks = 0
        self.loading_ticks = 0

# Define the parameters of an item
class Item:
    def __init__(self, name, size, is_frozen):
        self.name = name
        self.size = size
        self.is_frozen = is_frozen

# Defining the properties of the FOODIE sim itself
class FOODIE:
    def __init__(self, terrain, num_robots):
        self.terrain = terrain # node terrain
        self.robots = [Robot(f"ROBOT {i}", "FW") for i in range(num_robots)]
        self.orders = PriorityQueue() # using a priority queue to sort orders
        self.pos = nx.spring_layout(self.terrain) # saving the positions once to avoid jumpiness
        self.obstacles = []
        self.order_locations = {}
        self.low_battery_level = 30

        # List of items that could appear on a FOODIE order
        self.possible_items = [
            Item("Watermelon", 'large', False),
            Item("Icecream", 'small', True),
            Item("Beer", 'small', False),
            Item("Burger", 'small', False),
            Item("Gallon Water", 'large', False),
            Item("Fries", 'small', False),
            Item("Grilled Cheese", 'small', False),
            Item("Popsicle", 'small', True),
            Item("Banana Bunch", 'medium', False),
            Item("Bread", 'medium', False),
            Item("Cheese", 'small', False),
            Item("Trailmix", 'small', False)
        ]

    # This function defines the bagging expert module system
    def bagger(self, robot):
        # Create a random assortment of items
        order_items = random.sample(self.possible_items, random.randint(1, len(self.possible_items)))

        # Sort the items based on their size and is_frozen attribute
        size_order = {'large': 0, 'medium': 1, 'small': 2}
        sorted_items = sorted(order_items, key=lambda x: (x.is_frozen, size_order[x.size]))

        # Define a rule base for backwards chaining
        rule_base = {
            "start": lambda: "process_item",
            "small_item": lambda: "regular_bag" if sorted_items[-1].size else "small",
            "medium_item": lambda: "regular_bag" if sorted_items[-1].size else "medium",
            "large_item": lambda: "regular_bag" if sorted_items[-1].size else "large",
            "freezer_bag": lambda: "add_item",
            "regular_bag": lambda: "add_item",
            "add_item": lambda: "check_capacity",
            "check_capacity": lambda: "new_bag" if len(bags[bag_type][-1]) >= max_items_per_bag else "continue_bagging",
            "new_bag": lambda: "process_item",
            "continue_bagging": lambda: "process_item"
        }

        regular_bags = [[]]
        freezer_bags = [[]]
        max_items_per_bag = 3  # set the limit for the number of items in each bag

        print(f"{robot.name} is bagging the order:")

        # Pack the items into bags
        for item in sorted_items:
            # Determine which bag to use
            if item.is_frozen:
                target_bags = freezer_bags
                bag_name = "Freezer Bag"
            else:
                target_bags = regular_bags
                bag_name = "Regular Bag"

            current_bag = target_bags[-1] # Get the current bag

            # Add the item to the bag or start a new bag if the current one is full
            if len(current_bag) < max_items_per_bag:
                current_bag.append(item)
                print(f"  - {item.name} ({item.size}) added to {bag_name}")
            else:
                new_bag = [item]
                target_bags.append(new_bag)
                print(f"  - {bag_name} is full, starting a new {bag_name}")
                print(f"  - {item.name} ({item.size}) added to new {bag_name}")

    # function for adding an order to the queue and set its status to waiting
    def add_order(self, location):
        priority = random.random()
        self.orders.put((priority, location))
        self.order_locations[location] = "WAITING"

    # function the uses A* to plan the route of the delivery robot
    def plan_route(self, robot):
        # No plannign if no orders
        if self.orders.empty() or robot.path:
            return
        if robot.charge <= self.low_battery_level:  # Check if the robot needs to charge
            return
        order = self.orders.get()[1]
        try:
            # Using A* to plan the route
            path_to_order = nx.astar_path(self.terrain, robot.location, order)
            path_to_FW = nx.astar_path(self.terrain, order, "FW")
            robot.path = path_to_order + path_to_FW[1:]
            robot.order = order
            self.bagger(robot) # Bag and store the order
        except nx.NetworkXNoPath: # In case of failure
            print(f"No path found for {robot.name} to {order}.")
            self.add_order(order)

    # Function for moving the robots along at each sim tick
    def move_robot(self, robot):
        # Check how many ticks the robot has been charging for and charge acccordingly
        if robot.charging_ticks > 0:
            robot.charging_ticks -= 1
            if robot.charging_ticks == 0:
                robot.charge = 100  # Fully charged
            print(f"{robot.name} charging at FW.")
            return

        # Robot spends a tick to load and bag order
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
                robot.charge -= 1  # Decrease the battery by 1 at each tick

                if robot.location == robot.order:
                    self.order_locations[robot.order] = f"Delivered by {robot.name}"
                    robot.order = "FW"
        # Time for a charge
        if robot.location == "FW" and robot.charge <= 30:
            robot.charging_ticks = 5  # Set the charging_ticks to 5

    # Function for running the simultion, plannign and moving together
    def simulate(self):
        while not self.orders.empty():
            for robot in self.robots:
                self.plan_route(robot)
                self.move_robot(robot)
            self.draw_terrain()
            plt.pause(.5) # Set the tick rate

    # Function for drawing terrain and creating graphics on the nodes
    def draw_terrain(self):
        plt.clf()
        #Customize the terrain
        nx.draw(self.terrain, self.pos, with_labels=True, node_color='#83AF9B', node_size=1000, font_size=14, font_weight='bold', font_color='white')

        robot_img = mpimg.imread('robot.png')  # Read the robot image

        for i, robot in enumerate(self.robots):
            if robot.location in self.pos:
                img_pos = self.pos[robot.location]
                imagebox = OffsetImage(robot_img, zoom=0.3)  # Adjust the zoom value to scale the robot image
                imagebox.image.axes = plt.gca()

                ab = AnnotationBbox(imagebox, (img_pos[0], img_pos[1]), frameon=False)
                plt.gca().add_artist(ab)

                # Adding and managing the status labels
                label = f"{robot.name} ({robot.charge}%)"
                if robot.path:
                    label += " -> " + ("RETURNING" if robot.order == "FW" and robot.path[-1] == "FW" else str(robot.order))
                plt.text(img_pos[0]-0.08, img_pos[1]+0.07, label, fontsize=12, color='red')

        # Customizing order nodes
        for location, status in self.order_locations.items():
            if status == "WAITING":
                nx.draw_networkx_nodes(self.terrain, self.pos, nodelist=[location], node_color='#F3E0BE', node_size=1500, node_shape='o')
                nx.draw_networkx_labels(self.terrain, self.pos, {location: "ORDER"}, font_size=12, font_weight='bold', font_color='black')
            else:
                nx.draw_networkx_nodes(self.terrain, self.pos, nodelist=[location], node_color='#83AF9B', node_size=1500, node_shape='o')

        # Custom red dashed design for obstacle connections
        for u, v in self.obstacles:
            x1, y1 = self.pos[u]
            x2, y2 = self.pos[v]
            plt.plot([x1, x2], [y1, y2], 'r--')

        # Generate the order list for each of the order statuses
        plt.gca().set_title("FOODIE OVERVIEW:")
        order_list_text = ""
        for location, status in self.order_locations.items():
            assigned_robot = None
            for robot in self.robots:
                if robot.order == location:
                    assigned_robot = robot.name
                    break
            order_list_text += f"Order at {location} - Status: {status} - Assigned to: {assigned_robot if assigned_robot else 'Not assigned'}\n"
        plt.gca().text(0.02, 0.02, order_list_text, fontsize=10, color='black', transform=plt.gca().transAxes)

        # Reveal the plot
        plt.show(block=False)

# Function that turns a set percentage of the edges into obstacles randomly
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
    G = nx.grid_2d_graph(10, 10) # 10x10 grid of nodes
    G = nx.convert_node_labels_to_integers(G, first_label=1, ordering="sorted")
    G = nx.relabel_nodes(G, {node: str(node) for node in G.nodes()})  # Convert node labels to strings
    G.add_node("FW")  # Add the warehouse node
    random_node = random.choice([node for node in G.nodes() if node != "FW"])
    G.add_edge("FW", random_node)

    foodie = FOODIE(G, 3)  # 3 robots for demo
    foodie.pos = nx.kamada_kawai_layout(G)  # Use kamada_kawai_layout to minimize edge crossings and node overlaps
    foodie.obstacles = create_random_obstacles(G, 0.3)  # 30% chance of an obstacle

    for _ in range(10):  # 10 orders for demo
        foodie.add_order(random.choice(list(G.nodes)))
        foodie.simulate()

if __name__ == "__main__":
    main()
