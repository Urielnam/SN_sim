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
print_excel = False

simulation_collector = {}
success_vs_self_org_dict = {}
success_vs_self_org_dict["total"] = {}
# TODO stack it so we can run the simulation multiple times and then show the self-org/accumulated success for each
#  separately and together
for i in range(3):
    simulation_collector["run #" + str(i)] = Simulation.main_run(ui, print_excel)

    success_vs_self_org_dict["run #" + str(i)] = BackendClasses.calc_success_vs_self_org(
        simulation_collector["run #" + str(i)]["self_organization_measure"],
        simulation_collector["run #" + str(i)]["successful_operations_total"])
    BackendClasses.calc_average_stdev(success_vs_self_org_dict["run #" + str(i)])

    for x in success_vs_self_org_dict["run #" + str(i)]:
        if x not in success_vs_self_org_dict["total"]:
            success_vs_self_org_dict["total"][x] = {"values": success_vs_self_org_dict["run #" + str(i)][x]["values"]}
        else:
            success_vs_self_org_dict["total"][x]["values"] = success_vs_self_org_dict["total"][x]["values"] \
                                                   + success_vs_self_org_dict["run #" + str(i)][x]["values"]


BackendClasses.calc_average_stdev(success_vs_self_org_dict["total"])
# function to analyze the proportions between self - org and accumulated success.

# currently a function showing only one run. I want a function to stack different runs.

UIClasses.plot_self_org_success_with_error(success_vs_self_org_dict["total"])

PlotClasses.paint_final(simulation_collector["run #" + str(0)], dt=5)




# f.show()
