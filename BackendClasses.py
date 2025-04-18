import numpy as np
from statistics import mean, stdev
import bisect

# old not-optimized function, when end_time = 1000, iterations = 5, resource = 100 and dt = 5 it took 444s out of a
# total of 626s


def add_to_dict_arr(dic, key, val):
    if key in dic:
        dic[key].append(val)
    else:
        dic[key] = [val]

def calc_self_org_vectorized(dt, agent_flow_rates_by_type, number_of_sensors, env, timestep_list):
    """
        Calculates self-organization using vectorized numpy operations.

        Args:
            dt: Time step.
            agent_flow_rates_by_type: Dictionary of agent flow rates.
            number_of_sensors: Dictionary of sensor counts.
            env: Simulation environment.
            timestep_list: List of time steps.

        Returns:
            The total self-organization measure.
    """


    # need to find a way to limit the comparison (it runs too long...)

    changes_by_key = []
    timestep_limit = len(timestep_list)


    for key_n in agent_flow_rates_by_type.keys():
        flow_rates = np.array(list(agent_flow_rates_by_type[key_n].values()))
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


    sensor_counts = np.array(list(number_of_sensors.values()))
    # limit the sensor count to the timestep limit
    sensor_counts = sensor_counts[:timestep_limit]
    if len(sensor_counts) < 2:
        changes_by_key.append(0)
    else:
        shifted_sensor_counts = np.roll(sensor_counts, 1)
        shifted_sensor_counts[0] = sensor_counts[0]
        sensor_changes = np.sum(sensor_counts != shifted_sensor_counts)
        changes_by_key.append(sensor_changes)

    return np.sum(changes_by_key)


def calc_self_org(dt, agent_flow_rates_by_type, number_of_sensors, env, timestep_list):
    changes_by_key = []

    # def wrapped_func():
        # for every agent type
    for key_n in agent_flow_rates_by_type.keys():
        # create new parameter
        change_count = 0

        # iterate over the total number of timesteps
        for i in range(len(timestep_list) - 1):
            # if there was a change in previous timestep - add 1
            if agent_flow_rates_by_type[key_n][timestep_list[i]] != \
                    agent_flow_rates_by_type[key_n][timestep_list[i + 1]]:
                change_count += 1
        changes_by_key.append(change_count)

    change_count = 0

    for x in range(len(timestep_list) - 1):
        if number_of_sensors[timestep_list[x]] != \
                number_of_sensors[timestep_list[x + 1]]:
            change_count += 1
    changes_by_key.append(change_count)

    # lp = LineProfiler()
    # lp_wrapper = lp(wrapped_func)
    # lp_wrapper()
    # lp.print_stats()

    return np.sum(changes_by_key)


# calculate system self organization over time (for a2).
def calc_self_org_over_time(self_organization_measure, env, dt, agent_flow_rates_by_type, number_of_sensors,
                            timestep_list):
    # old function without numpy
    result_self_org = calc_self_org(dt, agent_flow_rates_by_type, number_of_sensors, env, timestep_list)
    # new function with numpy
    #result_self_org = calc_self_org_vectorized(dt, agent_flow_rates_by_type, number_of_sensors, env, timestep_list)
    add_to_dict_arr(self_organization_measure, float(env.now), result_self_org)


# calculate data type age over time (for a1).
def calc_ages(data_type_keys, data_age_by_type, env, sensor_array_queue, array_analysis_queue, analysis_array_queue,
              array_action_queue, action_array_queue, array_sensor_queue, data_age):
    # calculate average time for all objects.

    ages = [env.now - data_object.time for data_object in (sensor_array_queue + array_analysis_queue +
                                                           analysis_array_queue + array_action_queue +
                                                           action_array_queue + array_sensor_queue)]

    # data_age[float(env.now)].append(ages)
    add_to_dict_arr(data_age, float(env.now), ages)

    # for each key in image_map2 (data type)
    # in dict "data_age_by_type"
    # time now minus creation time.
    # for the list of object with that data type in all 6 arrays
    for key in data_type_keys:
        add_to_dict_arr(data_age_by_type[key], float(env.now), [env.now - data_object.time for data_object in [
                i for i in (sensor_array_queue + array_analysis_queue + analysis_array_queue +
                            array_action_queue + action_array_queue + array_sensor_queue) if i.type == key]])


# calculate measure of success over time (for a2)
# was 66.7s out of a total of 179s
def calc_success_over_time(successful_operations_total, env, successful_operations, dt):
    index = bisect.bisect_right(successful_operations, env.now - dt)
    add_to_dict_arr(successful_operations_total, float(env.now), len(successful_operations)-index)


# calculate number of objects over time (for a3)
def calculate_number_of_objects(number_of_sensors, env, sensor_list, agent_flow_rates_by_type, array, analysis_station,
                                action_station, total_resource):
    add_to_dict_arr(number_of_sensors, float(env.now), (len(sensor_list)))
    add_to_dict_arr(agent_flow_rates_by_type["Array"], float(env.now), array.flow_rate)
    add_to_dict_arr(agent_flow_rates_by_type["Analysis Station"], float(env.now), analysis_station.flow_rate)
    add_to_dict_arr(agent_flow_rates_by_type["Action Station"], float(env.now), action_station.flow_rate)
    add_to_dict_arr(total_resource, float(env.now), len(sensor_list) + array.flow_rate + analysis_station.flow_rate + action_station.flow_rate)


# accumulated function for all secondary calculation for the simulation.
def clockanddatacalc_func(data_type_keys, data_age_by_type, env, sensor_array_queue, array_analysis_queue,
                          analysis_array_queue, array_action_queue, action_array_queue, array_sensor_queue,
                          data_age, self_organization_measure, dt, agent_flow_rates_by_type, number_of_sensors,
                          successful_operations_total, successful_operations, sensor_list, array, analysis_station,
                          action_station, total_resource, timestep_list):
    prepare_timestep_list(timestep_list, dt, env)

    calc_ages(data_type_keys, data_age_by_type, env, sensor_array_queue, array_analysis_queue, analysis_array_queue,
              array_action_queue, action_array_queue, array_sensor_queue, data_age)
    calculate_number_of_objects(number_of_sensors, env, sensor_list, agent_flow_rates_by_type, array, analysis_station,
                                action_station, total_resource)
    calc_self_org_over_time(self_organization_measure, env, dt, agent_flow_rates_by_type, number_of_sensors,
                            timestep_list)
    calc_success_over_time(successful_operations_total, env, successful_operations, dt)


def calc_average_stdev(success_vs_self_org_dict):
    for self_org_key in success_vs_self_org_dict:
        success_vs_self_org_dict[self_org_key]["average"] = mean(success_vs_self_org_dict[self_org_key]["values"])
        if len(success_vs_self_org_dict[self_org_key]["values"]) > 1:
            success_vs_self_org_dict[self_org_key]["stdev"] = stdev(success_vs_self_org_dict[self_org_key]["values"])
        else:
            success_vs_self_org_dict[self_org_key]["stdev"] = 0


# function that gets as input a graph of self-organization over time, and a graph of success over time and calculates
# the average success over time for a specific value of self-org with stdev.
# create a matrix of self-organization vs success over time
def calc_success_vs_self_org(self_organization_measure_dict, successful_operations_total_dict):
    success_vs_self_org_dict = {}

    for key in self_organization_measure_dict:

        self_org_key = self_organization_measure_dict[key][0]
        successful_op_value = successful_operations_total_dict[key][0]
        if self_org_key not in success_vs_self_org_dict:
            success_vs_self_org_dict[self_org_key] = {"values": []}
        add_to_dict_arr(success_vs_self_org_dict[self_org_key], "values", successful_op_value)

    return success_vs_self_org_dict


def prepare_timestep_list(timestep_list, dt, env):
    if len(timestep_list) >= dt*10:
        timestep_list.pop(0)
    timestep_list.append(float(env.now))

