import numpy as np
from statistics import mean, stdev
import os
import pandas as pd
from typing import List


# old not-optimized function, when end_time = 1000, iterations = 5, resource = 100 and dt = 5 it took 444s out of a
# total of 626s


def add_to_dict_arr(dic, key, val):
    """
    Appends value to a list at dic[key].
    Use this for metrics where multiple values can exist for one timestamp
    (e.g., list of ages of all packets arriving at t=10).
    """
    if key in dic:
        dic[key].append(val)
    else:
        dic[key] = [val]

def log_scalar(dic, key, val):
    """
    Sets dic[key] = val directly.
    Use this for 1-to-1 metrics (e.g., total resource count at t=10).
    Overwrites if key exists (assumes one measurement per tick).
    """
    dic[key] = val

# -------------------------
# METRIC CALCULATIONS
# -------------------------

def calc_self_org(ctx):
    """
    Calculates the 'Self-Organization Measure' (Volatility).
    Args:
        ctx: simulation context

    Returns:
        The total self-organization measure.
    """
    changes_by_key: List[int] = []

    # 1. Flow Rate Changes
    for key_n in ctx.agent_flow_rates_by_type.keys():
        change_count = 0
        # Check history
        # Note: We assume scalar values here now
        times = sorted(list(ctx.agent_flow_rates_by_type[key_n].keys()))

        # We need at least 2 points
        if len(times) < 2:
            changes_by_key.append(0)
            continue

        for i in range(len(times) - 1):
            val_now = ctx.agent_flow_rates_by_type[key_n][times[i]]
            val_next = ctx.agent_flow_rates_by_type[key_n][times[i + 1]]
            if val_now != val_next:
                change_count += 1
        changes_by_key.append(change_count)

    # 2. Topology Changes (Sensor Count)
    change_count = 0
    times_iiot = sorted(list(ctx.number_of_iiots.keys()))
    if len(times_iiot) >= 2:
        for x in range(len(times_iiot) - 1):
            if ctx.number_of_iiots[times_iiot[x]] != ctx.number_of_iiots[times_iiot[x + 1]]:
                change_count += 1
    changes_by_key.append(change_count)

    return np.sum(changes_by_key)

def calc_self_org_over_time(ctx):
    """
    Wraps the calculation and logs it.
    """
    result_self_org = calc_self_org(ctx)
    # Self-org measure is a scalar for this timestamp
    log_scalar(ctx.self_organization_measure, float(ctx.env.now), result_self_org)

def calc_ages(ctx):
    """
    Calculates age of data packets.
    Note: 'ages' is a list of floats (one per packet).
    We KEEP add_to_dict_arr here because we might want the distribution.
    """
    all_packets = ctx.get_all_packets()
    ages = [ctx.env.now - data_object.time for data_object in all_packets]

    # Store the list of ages for this timestamp
    add_to_dict_arr(ctx.data_age, float(ctx.env.now), ages)

    for key in ctx.config.data_type_keys:
        type_ages = [ctx.env.now - data_object.time for data_object in all_packets if data_object.type == key]
        add_to_dict_arr(ctx.data_age_by_type[key], float(ctx.env.now), type_ages)


def calc_success_over_time(ctx):
    """
    Calculates cumulative success.
    Refactored to store SCALAR values.
    """
    # Count how many successes happened up to now
    # successful_operations is a list of timestamps [10, 15, 20...]
    # We want the count.

    # Logic: Since successful_operations grows, len() is the cumulative count.
    # The original logic using bisect seems to want "successes within the last dt window"
    # OR "total success up to now". The variable name 'successful_operations_total' implies cumulative.

    total_count = len(ctx.successful_operations)
    log_scalar(ctx.successful_operations_total, float(ctx.env.now), total_count)


def calculate_number_of_objects(ctx, bus, edge, scada):
    """
    Logs resource usage. Refactored to store SCALARS.
    """
    current_time = float(ctx.env.now)

    # Log Scalars
    log_scalar(ctx.number_of_iiots, current_time, len(ctx.iiot_list))
    log_scalar(ctx.agent_flow_rates_by_type["Network Bus"], current_time, bus.flow_rate)
    log_scalar(ctx.agent_flow_rates_by_type["Edge Processor"], current_time, edge.flow_rate)
    log_scalar(ctx.agent_flow_rates_by_type["SCADA Actuator"], current_time, scada.flow_rate)

    total_res = len(ctx.iiot_list) + bus.flow_rate + edge.flow_rate + scada.flow_rate
    log_scalar(ctx.total_resource, current_time, total_res)


def prepare_timestep_list(ctx):
    if len(ctx.timestep_list) >= ctx.config.dt * 10:
        ctx.timestep_list.pop(0)
    ctx.timestep_list.append(float(ctx.env.now))

def calc_self_org_vectorized(ctx):
    """
        Calculates self-organization using vectorized numpy operations.

        Args:
            ctx: Simulation Context

        Returns:
            The total self-organization measure.
    """

    # need to find a way to limit the comparison (it runs too long...)

    changes_by_key = []
    timestep_limit = len(ctx.timestep_list)


    for key_n in ctx.agent_flow_rates_by_type.keys():
        flow_rates = np.array(list(ctx.agent_flow_rates_by_type[key_n].values()))
        # next step limits the flow rates to the timestep limit
        flow_rates = flow_rates[-timestep_limit:]
        # handle the cases where timestep_limit is less than 2
        if len(flow_rates) < 2:
            changes_by_key.append(0)
        else:
            # Shift the array to compare adjacent values
            shifted_flow_rates = np.roll(flow_rates, 1)
            shifted_flow_rates[0]  = flow_rates[0] # Handle the first element
            changes = np.sum(flow_rates != shifted_flow_rates)
            changes_by_key.append(changes)
            # print(changes)


    iiot_counts = np.array(list(ctx.number_of_iiots.values()))
    # limit the iiot count to the timestep limit
    iiot_counts = iiot_counts[:timestep_limit]
    if len(iiot_counts) < 2:
        changes_by_key.append(0)
    else:
        shifted_iiot_counts = np.roll(iiot_counts, 1)
        shifted_iiot_counts[0] = iiot_counts[0]
        iiot_changes = np.sum(iiot_counts != shifted_iiot_counts)
        changes_by_key.append(iiot_changes)

    return np.sum(changes_by_key)


# accumulated function for all secondary calculation for the simulation.
def clockanddatacalc_func(ctx, bus, edge, scada):

    prepare_timestep_list(ctx)
    calc_ages(ctx)
    calculate_number_of_objects(ctx, bus, edge, scada)
    calc_self_org_over_time(ctx)
    calc_success_over_time(ctx)


# -------------------------
# UTILITIES
# -------------------------
def create_folder(name, now):
    """
    Creates a time-stamped directory structure: sim_data/timestamp/name
    """
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    top_folder = os.path.join(ROOT_DIR, "sim_data")
    if not os.path.exists(top_folder): os.mkdir(top_folder)

    date_folder = os.path.join(top_folder, now)
    if not os.path.exists(date_folder): os.mkdir(date_folder)

    DATA_DIR = os.path.join(date_folder, name)
    if not os.path.exists(DATA_DIR): os.mkdir(DATA_DIR)

    return DATA_DIR


def create_folder_path(path):
    if not os.path.exists(path):
        os.mkdir(path)


def export_to_excel(simulation_data, timestamp_str):
    """
    Exports data to Excel.
    """
    try:
        save_path = create_folder("excels", timestamp_str)

        for key, data_map in simulation_data.items():
            if not isinstance(data_map, dict):
                continue

            # Convert dictionary {time: val} to DataFrame
            try:
                # Check if values are lists or scalars
                sample_val = next(iter(data_map.values())) if data_map else None

                if isinstance(sample_val, list):
                    # For data_age: Flatten or keep as string representation?
                    # For analysis, we usually want mean/max per row
                    rows = []
                    for t, v_list in data_map.items():
                        row = {"time": t, "raw_values": str(v_list), "mean": mean(v_list) if v_list else 0}
                        rows.append(row)
                    df = pd.DataFrame(rows)
                else:
                    # Scalar values (Simple Series)
                    df = pd.DataFrame(list(data_map.items()), columns=['Time', 'Value'])

                excel_name = os.path.join(save_path, f"{key}.xlsx")
                df.to_excel(excel_name, index=False)
            except Exception as e:
                print(f"Skipping export for {key}: {e}")

        print(f"Data exported to: {save_path}")

    except Exception as e:
        print(f"Export failed: {e}")


# -------------------------
# AGGREGATION FOR PLOTTING (Legacy Support)
# -------------------------

def calc_average_stdev(success_vs_self_org_dict):
    # This logic assumes the structure built in Data_collector.py
    # We leave it largely alone but ensure it handles empty lists safely.
    for self_org_key in success_vs_self_org_dict:
        vals = success_vs_self_org_dict[self_org_key]["values"]
        success_vs_self_org_dict[self_org_key]["average"] = mean(vals) if vals else 0
        if len(vals) > 1:
            success_vs_self_org_dict[self_org_key]["stdev"] = stdev(vals)
        else:
            success_vs_self_org_dict[self_org_key]["stdev"] = 0


def calc_success_vs_self_org(self_organization_measure_dict, successful_operations_total_dict):
    success_vs_self_org_dict = {}

    # Keys are timestamps
    for t in self_organization_measure_dict:
        if t in successful_operations_total_dict:
            self_org_val = self_organization_measure_dict[t]
            success_val = successful_operations_total_dict[t]

            # Group by self_org value (bucket)
            if self_org_val not in success_vs_self_org_dict:
                success_vs_self_org_dict[self_org_val] = {"values": []}

            success_vs_self_org_dict[self_org_val]["values"].append(success_val)

    return success_vs_self_org_dict