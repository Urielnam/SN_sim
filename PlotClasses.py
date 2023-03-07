from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# TODO consider changing this function so it only makes the X and Y axis data and does not create the figure object.
#  at the parent file the figure object is created and is shown.

import matplotlib.pyplot as plt
import numpy as np
from Simulation import data_type_keys
import random


# draw the graph for a single run.
def paint_final(simulation_collector, dt, run_num):

    f = plt.figure(figsize=(2, 2))
    f.suptitle('This is simulation run #' + str(run_num))
    a3 = f.add_subplot(121)
    a3.plot()
    a1 = f.add_subplot(222)
    a1.plot()
    a2 = f.add_subplot(224)
    a2.plot()

    # Draw the inital state of the clock and data on the canvas

    # re-draw the clock and data fields on the canvas. Also update the matplotlib charts

    # Delete previous data.

    a1.set_xlabel("Time")
    a1.set_ylabel("Average Data Age")

    a1.plot([t for (t, age) in simulation_collector['data_age'].items()],
            [np.mean(age) for (t, age) in simulation_collector['data_age'].items()], label="all")

    for key in data_type_keys:
        a1.plot([t for (t, age) in simulation_collector['data_age_by_type'][key].items()],
                [np.mean(age) for (t, age) in simulation_collector['data_age_by_type'][key].items()], label=key)
    a1.legend(loc="upper left")

    a2.cla()
    a2.set_xlabel("Time")
    a2.set_ylabel("Accumulated Success")

    # code to calculate step function.
    a2.plot([t for (t, success) in simulation_collector['successful_operations_total'].items()],
            [success for (t, success) in simulation_collector['successful_operations_total'].items()],
            label="Average success over last " + str(dt) + " timesteps")

    a3.cla()
    a3.set_xlabel("Time")
    a3.set_ylabel("System Cost")

    a3.plot([t for (t, a) in simulation_collector['number_of_sensors'].items()],
            [a for (t, a) in simulation_collector['number_of_sensors'].items()],
            label="Sensors")

    for key in simulation_collector['agent_flow_rates_by_type'].keys():
        a3.plot([t for (t, a) in simulation_collector['agent_flow_rates_by_type'][key].items()],
                [a for (t, a) in simulation_collector['agent_flow_rates_by_type'][key].items()],
                label=key)
    a3.plot([t for (t, a) in simulation_collector['total_resource'].items()],
            [a for (t, a) in simulation_collector['total_resource'].items()],
            label="Total")

    a3.legend(loc="upper left")

    # to calculate self-org, check how much the system has been
    # "in motion" for the last X timesteps.
    # sum of number of times the resources were re-allocated.

    a2.plot([t for (t, a) in simulation_collector['self_organization_measure'].items()],
            [a for (t, a) in simulation_collector['self_organization_measure'].items()],
            label="Self-organization effort over last " + str(dt) + " timesteps")

    a2.legend(loc="upper left")


# a function that draws graphs for multiple runs
# it gains the data from the simulation collector and then constructs the frame
# top frame has the success from two runs, rest of the graph has all simulations split in a 2x2, 2x3, 3x3, etc config
def multiple_plot_graphs(simulation_collector, success_vs_self_org_dict, number_of_iterations, dt):
    max_number_of_iterations = 2
    if number_of_iterations < max_number_of_iterations:
        for i in range(number_of_iterations):
            paint_final(simulation_collector["run #" + str(i)], 5, i)
    else:
        for i in random.sample(range(number_of_iterations), k=max_number_of_iterations):
            paint_final(simulation_collector["run #" + str(i)], 5, i)

    plot_self_org_success_with_error(success_vs_self_org_dict["total"])

    plot_all_success(simulation_collector)

    plot_self_org_with_flow_data(0, simulation_collector)

    plt.show()


def plot_self_org_success_with_error(success_vs_self_org_dict):
    plt.figure()
    plt.title("Self-Org vs Success")
    x = []
    y = []
    e = []

    for self_org in success_vs_self_org_dict:
        x.append(self_org)
        y.append(success_vs_self_org_dict[self_org]["average"])
        e.append(success_vs_self_org_dict[self_org]["stdev"])

    plt.errorbar(x, y, e, linestyle='None', marker='^')

    # plt.show()


def plot_all_success(simulation_collector):
    plt.figure()
    plt.title("Cummulative Success")

    for run_num in simulation_collector:
        x = simulation_collector[run_num]["successful_operations"]
        y = [i+1 for i in range(len(x))]

        plt.plot(x, y, label=run_num)

    plt.legend()


def plot_self_org_with_flow_data(run_num, simulation_collector):
    """
    show the contribution of different agent types to the overall self_org_measure
    first segment shows for the first three agent types and the last one shows for sensors.
"""
    x = list(simulation_collector["run #" + str(run_num)]['self_organization_measure'].keys())
    number_of_figs = 2
    fig, axis = plt.subplots(number_of_figs)
    fig.subplots_adjust(hspace=0.4)
    axis[0].plot([a for (t, a) in simulation_collector["run #" + str(run_num)]['self_organization_measure'].items()])

    bottom = [0]*len(x)
    temp = simulation_collector.copy()
    for key in simulation_collector["run #" + str(run_num)]['agent_flow_rates_by_type'].keys():
        """
        for every agent type:
        check if value at time step j is different in j-1 for all j in that specific key.
        """
        original_array = np.array(list(simulation_collector["run #" + str(run_num)]['agent_flow_rates_by_type'][key].values())[1:])
        shifted_array = np.array(list(simulation_collector["run #" + str(run_num)]['agent_flow_rates_by_type'][key].values())[:-1])
        measure = original_array != shifted_array

        # measure = [simulation_collector["run #" + str(run_num)]['agent_flow_rates_by_type'][key][x[j]] !=
        #            simulation_collector["run #" + str(run_num)]['agent_flow_rates_by_type'][key][x[j-1]] for
        #            j in range(1, len(simulation_collector["run #" + str(run_num)]['agent_flow_rates_by_type'][key]))]
        measure = np.insert(measure, 0, False)
        axis[1].bar(x, measure, bottom=bottom, width=0.1)
        axis[1].legend(key, loc="upper right")
        bottom = [bottom[i] + measure[i] for i in range(len(bottom))]

    original_array = np.array(list(simulation_collector["run #" + str(run_num)]['number_of_sensors'].values())[1:])
    shifted_array = np.array(list(simulation_collector["run #" + str(run_num)]['number_of_sensors'].values())[:-1])
    measure = original_array != shifted_array
    # measure = [simulation_collector["run #" + str(run_num)]['number_of_sensors'][x[j]] !=
    #            simulation_collector["run #" + str(run_num)]['number_of_sensors'][x[j-1]] for
    #            j in range(1, len(simulation_collector["run #" + str(run_num)]['number_of_sensors']))]
    measure = np.insert(measure, 0, False)
    axis[1].bar(x, measure, bottom=bottom, width=0.1)
    axis[1].legend("Sensors", loc="upper right")






