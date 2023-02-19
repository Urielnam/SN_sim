import Simulation
import BackendClasses
import multiprocessing


def run_simulation(simulation_collector, success_vs_self_org_dict, i, ui, print_excel, end_time, max_resource):
    temp_run = Simulation.main_run(ui, print_excel, end_time, max_resource)
    simulation_collector["run #" + str(i)] = temp_run
    build_run_dict(simulation_collector, success_vs_self_org_dict, i)


def build_run_dict(simulation_collector, success_vs_self_org_dict, i):
    temp_dict = BackendClasses.calc_success_vs_self_org(
        simulation_collector["run #" + str(i)]["self_organization_measure"],
        simulation_collector["run #" + str(i)]["successful_operations_total"])

    success_vs_self_org_dict["run #" + str(i)] = temp_dict
    BackendClasses.calc_average_stdev(success_vs_self_org_dict["run #" + str(i)])

    for x in success_vs_self_org_dict["run #" + str(i)]:
        if x not in success_vs_self_org_dict["total"]:
            success_vs_self_org_dict["total"][x] = {"values": success_vs_self_org_dict["run #" + str(i)][x]["values"]}
        else:
            success_vs_self_org_dict["total"][x]["values"] = success_vs_self_org_dict["total"][x]["values"] \
                                                             + success_vs_self_org_dict["run #" + str(i)][x]["values"]
