""" Main code:
Runs the simulation with selected parameters
(maybe later decides on the parameters?)
starts file Simulation.py
"""

import Simulation
import PlotClasses
import BackendClasses


ui = False
print_excel = True
# TODO create a function to analyze the proportions between self - org and accumulated success.
# TODO stack it so we can run the simulation multiple times and then show the self-org/accumulated success for each
#  seperatly and togther
for i in range(1):
    simulation_collector = Simulation.main_run(ui, print_excel)

    BackendClasses.calc_success_vs_self_org(simulation_collector["self_organization_measure"],
                                            simulation_collector["successful_operations_total"])

PlotClasses.paintfinal(simulation_collector, dt=5)

# f.show()
