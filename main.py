""" Main code:
Runs the simulation with selected parameters
(maybe later decides on the parameters?)
starts file Simulation.py
"""

import PlotClasses
import BackendClasses
import multiprocessing
import Data_collector as DC
import psutil
import os

ui = False
print_excel = False

end_time = 100
number_of_iterations = 1
max_resource = 50
dt = 5


# we can run the simulation multiple times and then show the self-org/accumulated success for each
# separately and together


def memory_check():
    process = psutil.Process(os.getpid())
    print(process.memory_info().rss / (1024 * 1024), "MB")


def work(sim_coll, success_vs_self_org_dict, ind, dt):
    DC.run_simulation(sim_coll, success_vs_self_org_dict, ind, ui, print_excel, end_time, max_resource, dt)


if __name__ == '__main__':
    processes = []
    manager = multiprocessing.Manager()
    simulation_collector = manager.dict()
    success_vs_self_org_dict = manager.dict()
    success_vs_self_org_dict = {'total': {}}

    for i in range(number_of_iterations):
        simulation_collector["run #" + str(i)] = {}
        p = multiprocessing.Process(
            target=work,
            args=(simulation_collector, success_vs_self_org_dict, i, dt)
        )
        memory_check()
        processes.append(p)
        p.start()

    for pro in processes:
        pro.join()

    print(success_vs_self_org_dict)
    BackendClasses.calc_average_stdev(success_vs_self_org_dict["total"])

    # function to analyze the proportions between self - org and accumulated success.

    PlotClasses.multiple_plot_graphs(simulation_collector, success_vs_self_org_dict, number_of_iterations, dt)

    # currently a function showing only one run. I want a function to stack different runs.

    # UIClasses.plot_self_org_success_with_error(DC.success_vs_self_org_dict["total"])

    # PlotClasses.paint_final(DC.simulation_collector["run #" + str(0)], dt=5)

# f.show()
