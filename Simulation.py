import simpy
import random
import pandas as pd
from datetime import datetime

from agents import IIoTNode, NetworkBus, EdgeProcessor, SCADAActuator
from BackendClasses import clockanddatacalc_func, export_to_excel
from sim_context import SimulationContext
import UIClasses

# -------------------------
# SIMULATION
# -------------------------

# export data at the end of runtime.
# data to include
# all plotted data - need to check how it's done maybe?

def main_run(config):

    now = datetime.now().ctime().replace(":", "_")

    def metric_monitor(ctx, bus, edge, scada, visualizer=None):
        while True:
            yield ctx.env.timeout(0.1)

            # Calculate Stats
            clockanddatacalc_func(ctx, bus, edge, scada)

            # Update UI if active
            if visualizer:
                visualizer.tick()

    def check_max_resource(ctx, bus, edge, scada):
        return (len(ctx.iiot_list) + bus.flow_rate +
                edge.flow_rate +
                scada.flow_rate) < ctx.config.max_resource

    def create_new_iiot(iiot_number, ctx):
        # set a random number for the chances of giving good info.
        # iiot accuracy = iiot_acc.
        iiot_chance = config.iiot_acc*random.random()
        # add new iiot
        ctx.iiot_list.append(IIoTNode(ctx, iiot_chance, iiot_number))
        # increase iiot count
        return iiot_number + 1

    def kill_iiot(ctx, iiot_name):
        if not ctx.iiot_list:
            return

        target_node = None
        if iiot_name:
            # Find specific node to kill
            for node in ctx.iiot_list:
                if node.name == iiot_name:
                    target_node = node
                    break
        else:
            # Random kill
            target_node = random.choice(ctx.iiot_registry)

        if target_node:
            target_node.is_alive = False
            if target_node in ctx.iiot_list:
                ctx.iiot_list.remove(target_node)



    # we need to select how much we change the number of iiots, and then execute it.


    def iiot_maker(ctx, bus, edge, scada):
        """
        Monitors feedback queue and adds/removes IIoT Nodes based on performance.
        """

        iiot_number = 2

        while True:
            # Wait for Feedback
            feedback = yield ctx.bus_iiot_queue.get()

            # Logic: Positive Feedback -> Grow
            if feedback.status:
                if check_max_resource(ctx, bus, edge, scada):
                    iiot_number = create_new_iiot(iiot_number, ctx)

            # Logic: Negative Feedback -> Prune Rogue Node
            else:
                kill_iiot(ctx, feedback.creator)
                # If we killed the last one, restart population
                if len(ctx.iiot_list) == 0:
                    node_counter = create_new_iiot(iiot_number, ctx)

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

            yield ctx.env.timeout(0.01)

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
            yield ctx.env.timeout(0.1)
            # Check length of PriorityStore items
            q_len = len(ctx.bus_input_queue.items)

            if q_len > bus.flow_rate * 5:
                if check_max_resource(ctx, bus, edge, scada):
                    bus.flow_rate += 1
                elif q_len == 0 and bus.flow_rate > 1:
                    bus.flow_rate -= 1

            increase_self_org(ctx, bus, "Network Bus")


    def edge_upgrade(ctx, edge, bus, scada):
        while True:
            yield ctx.env.timeout(0.1)
            q_len = len(ctx.bus_edge_queue.items)

            if q_len > edge.flow_rate * 5:
                if check_max_resource(ctx, bus, edge, scada):
                    edge.flow_rate += 1
            elif q_len == 0 and edge.flow_rate > 1:
                edge.flow_rate -= 1

            increase_self_org(ctx, edge, "Edge Processor")
            yield ctx.env.timeout(0.1)

    def scada_upgrade(ctx, scada, bus, edge):
        while True:
            yield ctx.env.timeout(0.1)

            q_len = len(ctx.bus_scada_queue.items)

            if q_len > scada.flow_rate * 5:
                if check_max_resource(ctx, bus, edge, scada):
                    scada.flow_rate += 1
            elif q_len == 0 and scada.flow_rate > 1:
                scada.flow_rate -= 1


            increase_self_org(ctx, scada, "SCADA Actuator")

    # 3. Setup Environment
    if config.ui:
        # Realtime for visualization
        env = simpy.rt.RealtimeEnvironment(factor=0.1, strict=False)
    else:
        env = simpy.Environment()

    ctx = SimulationContext(env, config)

    # 4. Instantiate Visualizer (If UI is True)
    vis = None
    if config.ui:
        vis = UIClasses.Visualizer(ctx)

    # 5.Instantiate Agents
    bus = NetworkBus(ctx)
    scada = SCADAActuator(ctx)
    edge = EdgeProcessor(ctx)

    # Initial IIoT
    ctx.iiot_list.append(IIoTNode(ctx, 0.5, 1))

   # 6. Start Processes
    env.process(metric_monitor(ctx, bus, edge, scada, vis))
    env.process(iiot_maker(ctx, bus, edge, scada))
    env.process(bus_upgrade(ctx, bus, edge, scada))
    env.process(edge_upgrade(ctx, edge, bus, scada))
    env.process(scada_upgrade(ctx, scada, bus, edge))

    # 7. Run Simulation
    print(f"--- Starting Run (UI={config.ui}) ---")

    if config.ui:
        # If UI is on, we cannot use env.run(until=X) directly because
        # Tkinter needs the main thread.

        # We define a closer to stop the loop
        def close_sim():
            if env.now < config.end_time:
                try:
                    env.step()
                    vis.root.after(1, close_sim)  # Loop 1ms
                except simpy.core.EmptySchedule:
                    vis.root.quit()
            else:
                vis.save_snapshot(now)  # <--- Auto-save at end
                vis.root.quit()

        vis.root.after(0, close_sim)
        vis.start()  # Blocking call for Tkinter
    else:
        # Headless mode
        env.run(until=config.end_time)

    # 8. Export Data
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

    if config.print_excel:
        # Use BackendClasses to export
        export_to_excel(local_simulation_collector, now)

    return local_simulation_collector







