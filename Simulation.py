import simpy
from datetime import datetime
import statistics

from agents import IIoTNode, NetworkBus, EdgeProcessor, SCADAActuator
from BackendClasses import clockanddatacalc_func, export_to_excel, snapshot_system_state
from sim_context import SimulationContext
import UIClasses
import strategies

# -------------------------
# SIMULATION
# -------------------------

def main_run(config, overrides=None):
    """
    Main simulation entry point.
    Args:
        config: SimulationConfig object.
        overrides: Dictionary of parameters to override (for sensitivity analysis).
    """

    # Apply overrides if provided (useful for sensitivity sweeps)
    if overrides:
        for k, v in overrides.items():
            if hasattr(config, k):
                setattr(config, k, v)

    now = datetime.now().ctime().replace(":", "_")

    def metric_monitor(ctx, bus, edge, scada, visualizer=None):
        while True:
            yield ctx.env.timeout(ctx.config.sampling_interval)

            # Calculate Stats
            clockanddatacalc_func(ctx, bus, edge, scada)

            # Update UI if active
            if visualizer:
                visualizer.tick()

            # Capture integer state every 1.0 time unit (or config.dt)
            if int(ctx.env.now * 10) % 10 == 0:
                snapshot_system_state(ctx, bus, edge, scada)


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

    # 6. Initialize Optimization Strategy
    if config.optimization_method == "biological":
        strategy = strategies.BiologicalStrategy(ctx, bus, edge, scada)
    elif config.optimization_method == "qos":
        strategy = strategies.QoSStrategy(ctx, bus, edge, scada)
    elif config.optimization_method == "rl":
        strategy = strategies.RLStrategy(ctx, bus, edge, scada)
    elif config.optimization_method == "ga":
        strategy = strategies.GAStrategy(ctx, bus, edge, scada)
    elif config.optimization_method == "static":
        strategy = strategies.StaticStrategy(ctx, bus, edge, scada)
    else:
        # Default fallback
        strategy = strategies.BiologicalStrategy(ctx, bus, edge, scada)

    # Execute Strategy Setup
    strategy.setup()

    # 7. Start Core Metrics
    env.process(metric_monitor(ctx, bus, edge, scada, vis))

    # 7. Run Simulation
    print(f"--- Starting Run (Mode={config.optimization_method}, UI={config.ui}) ---")

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

    final_success = len(ctx.successful_operations)
    # Calculate Resource Usage over the entire run
    if ctx.total_resource:
        # Sum of all samples * duration of each sample = Total Resource-Time Units
        final_resource = sum(ctx.total_resource.values()) * config.sampling_interval
    else:
        final_resource = 0


    local_simulation_collector = {
        # Time Series Data
        "data_age": ctx.data_age,
        "data_age_by_type": ctx.data_age_by_type,
        "successful_operations_total": ctx.successful_operations_total,
        "number_of_iiots": ctx.number_of_iiots,
        "agent_flow_rates_by_type": ctx.agent_flow_rates_by_type,
        "total_resource": ctx.total_resource,
        "self_organization_measure": ctx.self_organization_measure,

        # Raw Data (For validation)
        "successful_operations": ctx.successful_operations,
        "last dt timesteps": ctx.timestep_list,

        # We must export the raw snapshots so the batch generator can save them
        "state_snapshots": getattr(ctx, "state_snapshots", []),

        # Summary Metrics (For T-Test/ANOVA)
        "final_success_count": final_success,
        "final_resource_cost": final_resource
    }

    if config.print_excel:
        # Use BackendClasses to export
        export_to_excel(local_simulation_collector, now)

    return local_simulation_collector







