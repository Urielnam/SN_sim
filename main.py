""" Main code:
Runs the simulation with selected parameters
(maybe later decides on the parameters?)
starts file Simulation.py
"""

import PlotClasses
import BackendClasses
import multiprocessing
import Data_collector as DC

ui = False
print_excel = False
end_time = 100
number_of_iterations = 3
max_resource = 50
max_resource = 50


# we can run the simulation multiple times and then show the self-org/accumulated success for each
# separately and together

def work(simulation_collector, success_vs_self_org_dict, i):
    DC.run_simulation(simulation_collector, success_vs_self_org_dict, i, ui, print_excel, end_time, max_resource)


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
            args=(simulation_collector, success_vs_self_org_dict, i)
        )
        processes.append(p)
        p.start()

    for pro in processes:
        pro.join()

    BackendClasses.calc_average_stdev(success_vs_self_org_dict["total"])

    # function to analyze the proportions between self - org and accumulated success.
    # function to analyze the proportions between self - org and accumulated success.
    PlotClasses.multiple_plot_graphs(simulation_collector, success_vs_self_org_dict, number_of_iterations)

# f.show()
