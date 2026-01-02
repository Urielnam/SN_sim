""" Main code:
Runs the simulation with selected parameters
(maybe later decides on the parameters?)
starts file Simulation.py
required libraries:
    matplotlib
    simpy
    psutil
    pandas
"""

import PlotClasses
import BackendClasses
import multiprocessing
import Data_collector as DC
import psutil
import os

from sim_config import SimulationConfig

RUN_PARAMS = {
    "end_time": 1000,
    "max_resource": 100,
    "dt": 5,
    "iiot_acc": 0.6,
    "self_org_threshold": 35,
    "ui": False,
    "print_excel": False,
    "optimization_method": "ga"
}

# optimization methods include: "biological", "qos", "rl" and "ga"

number_of_iterations = 1

# we can run the simulation multiple times and then show the self-org/accumulated success for each
# separately and together


def memory_check():
    process = psutil.Process(os.getpid())
    print(process.memory_info().rss / (1024 * 1024), "MB")


def work(sim_coll, ind, config):
    DC.run_simulation(sim_coll, ind, config)
    memory_check()


if __name__ == '__main__':
    processes = []
    manager = multiprocessing.Manager()
    simulation_collector = manager.dict()
    success_vs_self_org_dict = {'total':{}}

    # Create the Configuration Object
    current_config = SimulationConfig(
        end_time=RUN_PARAMS["end_time"],
        dt=RUN_PARAMS["dt"],
        max_resource=RUN_PARAMS["max_resource"],
        iiot_acc=RUN_PARAMS["iiot_acc"],
        self_org_threshold=RUN_PARAMS["self_org_threshold"],
        ui=RUN_PARAMS["ui"],
        print_excel=RUN_PARAMS["print_excel"],
        optimization_method=RUN_PARAMS["optimization_method"]
    )

    for i in range(number_of_iterations):
        simulation_collector["run #" + str(i)] = {}

        p = multiprocessing.Process(
            target=work,
            args=(simulation_collector, i, current_config)
        )
        processes.append(p)
        p.start()

    for pro in processes:
        pro.join()

    DC.build_run_dict(simulation_collector, success_vs_self_org_dict)
    BackendClasses.calc_average_stdev(success_vs_self_org_dict["total"])

    # function to analyze the proportions between self - org and accumulated success.

    PlotClasses.multiple_plot_graphs(simulation_collector, success_vs_self_org_dict, number_of_iterations,current_config)

    # currently a function showing only one run. I want a function to stack different runs.

    # UIClasses.plot_self_org_success_with_error(DC.success_vs_self_org_dict["total"])

    # PlotClasses.paint_final(DC.simulation_collector["run #" + str(0)], dt=5)

# f.show()
