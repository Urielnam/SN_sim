""" Main code:
Runs the simulation with selected parameters
(maybe later decides on the parameters?)
starts file Simulation.py
"""

import Simulation
import PlotClasses
import BackendClasses


# TODO create a function to analyze the proportions between self - org and accumulated success.
# TODO stack it so we can run the simulation multiple times and then show the self-org/accumulated success for each
#  seperatly and togther
for i in range(1):
    simulation_collector = Simulation.main_run(False)

    BackendClasses.calc_success_vs_self_org(simulation_collector[6], simulation_collector[2])

    PlotClasses.paintfinal(simulation_collector[0],
                           simulation_collector[1],
                           simulation_collector[2],
                           simulation_collector[3],
                           simulation_collector[4],
                           simulation_collector[5],
                           simulation_collector[6], dt=5)



# f.show()
