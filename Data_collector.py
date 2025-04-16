import Simulation
import BackendClasses


def run_simulation(simulation_collector, i, ui, print_excel, end_time, max_resource, dt, self_org_feedback_activate,
                   threshold_self_org_value, sensor_acc):
    temp_run = Simulation.main_run(ui, print_excel, end_time, max_resource, dt, self_org_feedback_activate,
                                   threshold_self_org_value, sensor_acc)
    simulation_collector["run #" + str(i)] = temp_run


def build_run_dict(simulation_collector, success_vs_self_org_dict):
    for itername in simulation_collector:
        temp_dict = BackendClasses.calc_success_vs_self_org(
            simulation_collector[itername]["self_organization_measure"],
            simulation_collector[itername]["successful_operations_total"])

        success_vs_self_org_dict[itername] = temp_dict
        BackendClasses.calc_average_stdev(success_vs_self_org_dict[itername])

        # if "total" not in success_vs_self_org_dict:
        #     success_vs_self_org_dict["total"] = {}

        for x in success_vs_self_org_dict[itername]:
            if x not in success_vs_self_org_dict["total"]:
                success_vs_self_org_dict["total"][x] = {"values": success_vs_self_org_dict[itername][x]["values"]}
            else:
                success_vs_self_org_dict["total"][x]["values"] = success_vs_self_org_dict["total"][x]["values"] + \
                                                                 success_vs_self_org_dict[itername][x]["values"]
