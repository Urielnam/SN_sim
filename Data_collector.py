import Simulation
import BackendClasses

simulation_collector = {}
success_vs_self_org_dict = {}
success_vs_self_org_dict["total"] = {}


def run_simulation(i, ui, print_excel, end_time):
    simulation_collector["run #" + str(i)] = Simulation.main_run(ui, print_excel, end_time)


def build_run_dict(i):
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
