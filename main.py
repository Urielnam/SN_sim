""" Main code:
Runs the simulation with selected parameters
(maybe later decides on the parameters?)
starts file Simulation.py
"""

import Simulation
import PlotClasses

ui = False
print_excel = True
# TODO create a function to analyze the proportions between self - org and accumulated success.
# TODO stack it so we can run the simulation multiple times and then show the self-org/accumulated success for each
#  seperatly and togther
simulation_collector = Simulation.main_run(ui, print_excel)


PlotClasses.paintfinal(simulation_collector, dt=5)

# f.show()
