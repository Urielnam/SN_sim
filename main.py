""" Main code:
Runs the simulation with selected parameters
(maybe later decides on the parameters?)
starts file Simulation.py
"""

import Simulation
import PlotClasses
import BackendClasses
import UIClasses
import Data_collector as DC
from multiprocessing import Pool

ui = False
print_excel = False
end_time = 100
number_of_iterations = 3


# we can run the simulation multiple times and then show the self-org/accumulated success for each
# separately and together

if __name__ == '__main__':
    for i in range(number_of_iterations):
        DC.run_simulation(i, ui, print_excel, end_time)

        DC.build_run_dict(i)

    BackendClasses.calc_average_stdev(DC.success_vs_self_org_dict["total"])
    # function to analyze the proportions between self - org and accumulated success.

    # currently a function showing only one run. I want a function to stack different runs.

    UIClasses.plot_self_org_success_with_error(DC.success_vs_self_org_dict["total"])

    PlotClasses.paint_final(DC.simulation_collector["run #" + str(0)], dt=5)

# f.show()
