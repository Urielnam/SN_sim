import numpy as np
from statistics import mean, stdev


def calc_self_org(dt, agent_flow_rates_by_type, number_of_sensors, env):
    changes_by_key = []

    # for every agent type
    for key_n in agent_flow_rates_by_type.keys():
        # create new parameter
        change_count = 0
        # create a list of timesteps that is in the range of [env.now, env.now-dt]
        relevant_list_of_timesteps_keys = [timestep for timestep in agent_flow_rates_by_type[key_n].keys() if timestep > (env.now - dt)]

        # iterate over the total number of timesteps
        for i in range(len(relevant_list_of_timesteps_keys) - 1):
            # if there was a change in previous timestep - add 1
            if agent_flow_rates_by_type[key_n][relevant_list_of_timesteps_keys[i]] != \
                    agent_flow_rates_by_type[key_n][relevant_list_of_timesteps_keys[i + 1]]:
                change_count += 1
        changes_by_key.append(change_count)

    change_count = 0
    relevant_list_of_timesteps = [x for x in number_of_sensors.keys() if x > (env.now - dt)]
    for x in range(len(relevant_list_of_timesteps) - 1):
        if number_of_sensors[relevant_list_of_timesteps[x]] != \
                number_of_sensors[relevant_list_of_timesteps[x + 1]]:
            change_count += 1
    changes_by_key.append(change_count)

    return np.sum(changes_by_key)


# calculate system self organization over time (for a2).
def calc_self_org_over_time(self_organization_measure, env, dt, agent_flow_rates_by_type, number_of_sensors):
    self_organization_measure[float(env.now)].append(calc_self_org(dt, agent_flow_rates_by_type, number_of_sensors,
                                                                   env))


# calculate data type age over time (for a1).
def calc_ages(data_type_keys, data_age_by_type, env, sensor_array_queue, array_analysis_queue, analysis_array_queue,
              array_action_queue, action_array_queue, array_sensor_queue, data_age):
    # calculate average time for all objects.

    ages = [env.now - data_object.time for data_object in (sensor_array_queue + array_analysis_queue +
                                                           analysis_array_queue + array_action_queue +
                                                           action_array_queue + array_sensor_queue)]
    data_age[float(env.now)].append(ages)

    # for each key in image_map2 (data type)
    # in dict "data_age_by_type"
    # time now minus creation time.
    # for the list of object with that data type in all 6 arrays
    for key in data_type_keys:
        data_age_by_type[key][float(env.now)].append(
            [env.now - data_object.time for data_object in [
                i for i in (sensor_array_queue + array_analysis_queue + analysis_array_queue +
                            array_action_queue + action_array_queue + array_sensor_queue) if i.type == key]])


# calculate measure of success over time (for a2)
def calc_success_over_time(successful_operations_total, env, successful_operations, dt):
    successful_operations_total[float(env.now)].append(len([x for x in successful_operations if x > env.now - dt]))


# calculate number of objects over time (for a3)
def calculate_number_of_objects(number_of_sensors, env, sensor_list, agent_flow_rates_by_type, array, analysis_station,
                                action_station, total_resource):
    number_of_sensors[float(env.now)].append(len(sensor_list))
    agent_flow_rates_by_type["Array"][float(env.now)].append(array.flow_rate)
    agent_flow_rates_by_type["Analysis Station"][float(env.now)].append(
        analysis_station.flow_rate)
    agent_flow_rates_by_type["Action Station"][float(env.now)].append(
        action_station.flow_rate)
    total_resource[float(env.now)].append(len(sensor_list) + array.flow_rate +
                                          analysis_station.flow_rate +
                                          action_station.flow_rate)


# accumulated function for all secondary calculation for the simulation.
def clockanddatacalc_func(data_type_keys, data_age_by_type, env, sensor_array_queue, array_analysis_queue,
                          analysis_array_queue, array_action_queue, action_array_queue, array_sensor_queue,
                          data_age, self_organization_measure, dt, agent_flow_rates_by_type, number_of_sensors,
                          successful_operations_total, successful_operations, sensor_list, array, analysis_station,
                          action_station, total_resource):
    calc_ages(data_type_keys, data_age_by_type, env, sensor_array_queue, array_analysis_queue, analysis_array_queue,
              array_action_queue, action_array_queue, array_sensor_queue, data_age)
    calc_self_org_over_time(self_organization_measure, env, dt, agent_flow_rates_by_type, number_of_sensors)
    calc_success_over_time(successful_operations_total, env, successful_operations, dt)
    calculate_number_of_objects(number_of_sensors, env, sensor_list, agent_flow_rates_by_type, array, analysis_station,
                                action_station, total_resource)


def calc_average_stdev(success_vs_self_org_dict):
    for self_org_key in success_vs_self_org_dict:
        success_vs_self_org_dict[self_org_key]["average"]= mean(success_vs_self_org_dict[self_org_key]["values"])
        if len(success_vs_self_org_dict[self_org_key]["values"])>1:
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
            success_vs_self_org_dict[self_org_key] = {"values" : []}
        success_vs_self_org_dict[self_org_key]["values"].append(successful_op_value)

    return success_vs_self_org_dict


