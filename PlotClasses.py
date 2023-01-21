from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# TODO consider changing this function so it only makes the X and Y axis data and does not create the figure object.
#  at the parent file the figure object is created and is shown.

import matplotlib.pyplot as plt
import numpy as np
from Simulation import data_type_keys

# f = plt.figure(figsize=(2, 2), dpi=72)
# a3 = f.add_subplot(121)
# a3.plot()
# a1 = f.add_subplot(222)
# a1.plot()
# a2 = f.add_subplot(224)
# a2.plot()


# draw the graph for a single run.
def paintfinal(simulation_collector, dt):

    f = plt.figure(figsize=(2, 2), dpi=72)
    a3 = f.add_subplot(121)
    a3.plot()
    a1 = f.add_subplot(222)
    a1.plot()
    a2 = f.add_subplot(224)
    a2.plot()

    # data_plot = FigureCanvasTkAgg(f, master=main)
    # data_plot.get_tk_widget().config(height=400)
    # data_plot.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


    # Draw the inital state of the clock and data on the canvas

    # re-draw the clock and data fields on the canvas. Also update the matplotlib charts

    # canvas.delete(self.time)

    # Delete previous data.

    # dt = 5

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
    # successful_operations_total[float(env.now)].append(len([x for x in successful_operations if x > env.now - dt]))
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

    # data_plot.draw()
    plt.show()
