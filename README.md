# FOODIE Project

We are implementing the optimization of routes that the robots take based on the order received and an expert system module that will handle bagging food items into a robot’s compartment. This project utilizes the A* algorithm in order to simulate the FOODIE process. In doing so, the algorithm must include the backward chaining algorithm, which starts with the goal and works backward to find the facts that will trigger the rules that will help achieve the goal. This can be done using a depth-first search or a breadth-first search.

Assumptions:
The locale is a known bounded terrain.
There is a finite number of movable robots, each equipped with HW/SW. Additionally, robots have compartments and a robotic arm that allows them to pick and bag items.
Robots will depart from and return to a food warehouse (FW) in which they: 
Park and recharge.
If the charge is below 20% the robot travels back to the charging station. 
Receive orders for food items.
Bag the items. 
The items will be bagged in order of size and will either be frozen or fresh.  
May deliver more than one order to more than one location and then return to the FW. 
Load up items into their compartment. 
Once a robot has configured and loaded the order, it departs to the destination specified in the order. 
