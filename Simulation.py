import simpy
import random
import pandas as pd
from datetime import datetime


from agents.iiot_node import IIoT_Node
from agents.network_bus import Network_Bus, check_queue
from agents.edge_processor import Edge_Processor
from agents.scada_actuator import SCADA_Actuator

from BackendClasses import clockanddatacalc_func

from sim_context import SimulationContext

# -------------------------
# SIMULATION
# -------------------------

# export data at the end of runtime.
# data to include
# all plotted data - need to check how it's done maybe?

def main_run(config):

    if config.ui:
        import UIClasses

    now = datetime.now().ctime()
    now = now.replace(":", "_")

    def create_clock(ctx, bus, edge, scada, clock, UI_obj):
        # This generator is meant to be used as a SimPy event to update the clock and the data in the UI

        while True:
            yield ctx.env.timeout(0.1)
            clockanddatacalc_func(ctx, bus, edge, scada)

            if config.ui:
                clock.tick(ctx.env.now)
                UI_obj.tick()

    def check_max_resource(ctx, bus, edge, scada):
        return (len(ctx.iiot_list) + bus.flow_rate +
                edge.flow_rate +
                scada.flow_rate) < ctx.config.max_resource

    def create_new_iiot(iiot_number, ctx):
        # set a random number for the chances of giving good info.
        # iiot accuracy = iiot_acc.
        iiot_chance = config.iiot_acc*random.random()
        # add new iiot
        ctx.iiot_list.append(IIoT_Node(ctx, iiot_chance, iiot_number))
        # increase iiot count
        return iiot_number + 1

    def kill_iiot(ctx, iiot):
        iiot.is_alive = False
        ctx.iiot_list.remove(iiot)

    # we need to select how much we change the number of iiots, and then execute it.


    def iiot_maker(ctx, bus, edge, scada):
        iiot_number = 2

        while True:
            #   LOGIC FOR IMPLEMENTATION - suggestion
            # ---------------------------------------------
            # do not kill a iiot if it is the last one.
            # if we are at max resource, kill iiot.
            # if new feedback is gained:
            #   if good - create new iiot
            #   if bad - kill iiot
            # if none of the above - check self_org.
            #   if lower then threshold - calculate what would increase the self-org and act accordingly.
            #   currently, any change in number of iiots increases self-org.
            #   randomly decide if increasing or decreasing (considering you won't get over max resource or kill
            #   the last iiot

            # CURRENT LOGIC
            # -------------------------------------------
            # while there are any feedback data packet:
            while len(ctx.bus_iiot_queue) > 0:

                # if scada feedback is good, create new iiot and kill the data packet.
                # if actuation is right:
                if ctx.bus_iiot_queue[0].status:

                    # if there are enough resources - grow the number of iiots. else - do nothing.
                    if check_max_resource(ctx, bus, edge, scada):
                        iiot_number = create_new_iiot(iiot_number, ctx)
                    # kill the data, even if you did not create an iiot.
                    ctx.bus_iiot_queue.pop(0)
                # else, if scada actuation is wrong and failed.
                else:
                    b = ctx.bus_iiot_queue[0]
                    for iiot in ctx.iiot_list.copy():
                        # find the rouge iiot and kill it.
                        if iiot.name == b.creator:
                            kill_iiot(ctx, iiot)
                    # if the iiot list is empty, create a new iiot.
                    if len(ctx.iiot_list) == 0:
                        iiot_number = create_new_iiot(iiot_number, ctx.env)
                    ctx.bus_iiot_queue.pop(0)

            # if we are at max resource, reduce the number of iiots
            if not check_max_resource(ctx, bus, edge, scada) and len(ctx.iiot_list) > 1:
                selected_iiot = random.choice(ctx.iiot_list)
                kill_iiot(ctx, selected_iiot)

            if config.self_org_active:
                """
                main goal - if self-org is less than 10, have every agent type "vibrate".
                check if condition is applied.
                check if self_org is less than 10 (ampiric)
                check if equal to last step.
                try to increase (enough resources?)
                if not enough resources
                try to decrease (enough spare to decrease?)
                if failed - do nothing.
                """
                if len(ctx.self_organization_measure) > 600:
                    if list(ctx.self_organization_measure.values())[-1][0] < ctx.config.self_org_threshold:
                        if len(ctx.iiot_list) == list(ctx.number_of_iiots.values())[-1][0]:
                            if check_max_resource(ctx, bus, edge, scada):
                                iiot_number = create_new_iiot(iiot_number, ctx.env)
                            else:
                                if len(ctx.iiot_list) > 1:
                                    removed_iiot = random.choice(ctx.iiot_list.copy())
                                    kill_iiot(ctx, removed_iiot)

            yield ctx.env.timeout(0.1)

    # same as previous logic, only with general object
    # object could be bus network, edge processor station or scada upgrade
    def increase_self_org(ctx, object, object_name):

        if config.self_org_active:
            if len(ctx.self_organization_measure) > 600:
                if list(ctx.self_organization_measure.values())[-1][0] < ctx.config.self_org_threshold:
                    if object.flow_rate == list(ctx.agent_flow_rates_by_type[object_name].values())[-1]:
                        if check_max_resource(ctx, bus, edge, scada):
                            object.flow_rate = object.flow_rate + 1
                        else:
                            if object.flow_rate > 1:
                                object.flow_rate = object.flow_rate - 1

    def bus_upgrade(ctx, bus, edge, scada):
        while True:
            if check_queue(ctx) < (bus.flow_rate - 1) * 5 and bus.flow_rate > 1:
                bus.flow_rate = bus.flow_rate - 1
            if check_max_resource(ctx, bus, edge, scada):
                while check_queue(ctx) > bus.flow_rate * 5:
                    bus.flow_rate = bus.flow_rate + 1
            increase_self_org(ctx, bus, "Network Bus")
            yield ctx.env.timeout(0.1)

    def edge_upgrade(ctx, edge, bus, scada):
        while True:
            if len(ctx.bus_edge_queue) < (edge.flow_rate - 1) * 5 and edge.flow_rate > 1:
                edge.flow_rate = edge.flow_rate - 1
            if check_max_resource(ctx, bus, edge, scada):
                while len(ctx.bus_edge_queue) > edge.flow_rate * 5:
                    edge.flow_rate = edge.flow_rate + 1
            increase_self_org(ctx, edge, "Edge Processor")
            yield ctx.env.timeout(0.1)

    def scada_upgrade(ctx, scada, bus, edge):
        while True:
            if len(ctx.bus_scada_queue) < (scada.flow_rate - 1) * 5 and scada.flow_rate > 1:
                scada.flow_rate = scada.flow_rate - 1
            if check_max_resource(ctx, bus, edge, scada):
                while len(ctx.bus_scada_queue) > scada.flow_rate * 5:
                    scada.flow_rate = scada.flow_rate + 1
            increase_self_org(ctx, scada, "SCADA Actuator")
            yield ctx.env.timeout(1.1)

    # original function
    clock = {}
    UI_obj = {}

    if config.ui:
        env = simpy.rt.RealtimeEnvironment(factor=0.1, strict=False)
        ctx = SimulationContext(env, config)

        UI_obj = UIClasses.PaintGrapic(
            ctx.iiot_bus_queue,
            ctx.bus_iiot_queue,
            ctx.bus_edge_queue,
            ctx.edge_sublist,
            ctx.edge_bus_queue,
            ctx.bus_scada_queue,
            ctx.scada_bus_queue)

        clock = UIClasses.ClockAndDataDraw(ctx,1100, 260, 1290, 340, 0)

    else:
        # do not remove, it's a faster env function:
        env = simpy.Environment()
        ctx = SimulationContext(env, config)



    bus = Network_Bus(ctx)
    scada = SCADA_Actuator(ctx)
    edge = Edge_Processor(ctx)
    env.process(create_clock(ctx, bus, edge, scada, clock, UI_obj))

    ctx.iiot_list.append(IIoT_Node(ctx,0.5, 1))
    env.process(iiot_maker(ctx, bus, edge, scada))
    env.process(bus_upgrade(ctx, bus, edge, scada))
    env.process(edge_upgrade(ctx, edge, bus, scada))
    env.process(scada_upgrade(ctx, scada, bus, edge))

    if config.ui:
        env.process(UIClasses.save_graph(ctx, now))

    env.run(until=config.end_time)

    if config.ui:
        UIClasses.main.mainloop()

    local_simulation_collector = {
        "data_age": ctx.data_age,
        "data_age_by_type": ctx.data_age_by_type,
        "successful_operations_total": ctx.successful_operations_total,
        "number_of_iiots": ctx.number_of_iiots,
        "agent_flow_rates_by_type": ctx.agent_flow_rates_by_type,
        "total_resource": ctx.total_resource,
        "self_organization_measure": ctx.self_organization_measure,
        "successful_operations": ctx.successful_operations,
        "last dt timesteps": ctx.timestep_list
    }

    def print_to_file(local_simulation_collector):
        # convert into dataframe
        path = UIClasses.create_folder("excels", now)
        for val in local_simulation_collector:
            df = pd.DataFrame(data=local_simulation_collector[val])
            # df = df.T
            # convert into excel
            excel_name = path + "\\" + val + ".xlsx"
            df.to_excel(excel_name, index=False)


    if config.print_excel:
        print_to_file(local_simulation_collector)
    return local_simulation_collector







