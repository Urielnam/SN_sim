""" Main code:
Runs the simulation with selected parameters
(maybe later decides on the parameters?)
starts file Simulation.py
"""

import Simulation
import PlotClasses
import BackendClasses
import UIClasses


ui = False
print_excel = True
simulation_collector = {}

# TODO stack it so we can run the simulation multiple times and then show the self-org/accumulated success for each
#  separately and together
for i in range(1):
    simulation_collector["run #" + str(i)] = Simulation.main_run(ui, print_excel)

    success_vs_self_org_dict = BackendClasses.calc_success_vs_self_org(
        simulation_collector["run #" + str(i)]["self_organization_measure"],
        simulation_collector["run #" + str(i)]["successful_operations_total"])

# function to analyze the proportions between self - org and accumulated success.
BackendClasses.calc_average_stdev(success_vs_self_org_dict)
# currently a function showing only one run. I want a function to stack different runs.
PlotClasses.paintfinal(simulation_collector, dt=5)
UIClasses.plot_self_org_success_with_error(success_vs_self_org_dict)


# f.show()
