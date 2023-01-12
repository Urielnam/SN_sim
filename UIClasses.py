import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import numpy as np

import os
import csv

main = tk.Tk()
main.title("ISR Simulation")
main.config(bg="#fff")
logo = tk.PhotoImage(file="images/title.png")
top_frame = tk.Frame(main)
top_frame.pack(side=tk.TOP, expand= False)
tk.Label(top_frame, image=logo, bg= "#000007", height=65, width=1300).pack(side=tk.LEFT, expand=False)
canvas = tk.Canvas(main, width=1300, height= 350, bg="white")
canvas.pack(side=tk.TOP, expand=False)

f = plt.Figure(figsize=(2, 2), dpi=72)
a3 = f.add_subplot(121)
a3.plot()
a1 = f.add_subplot(222)
a1.plot()
a2 = f.add_subplot(224)
a2.plot()

start_row = 95
regular_height = 30

image_map2 = {
    "intel": tk.PhotoImage(file="images/folder.png"),
    "feedback": tk.PhotoImage(file="images/feedback.png"),
    "target": tk.PhotoImage(file="images/target.png")
}


class ArrayDraw:
    def __init__(self):
        self.item_presentation = []
        self.x = 5
        self.y = 20
        self.canvas = canvas
        self.presentation = IsrElement("Array", self.x, self.y, 1290, start_row-30)

    def arr_move_item(self, moved_item):
        # draw inside box
        self.item_presentation.append(
            self.canvas.create_image(self.x + 100, self.y, anchor=tk.NW, image=image_map2[moved_item.type])
        )
        self.item_presentation.append(self.canvas.create_text(self.x + 100, self.y + 30, anchor=tk.NW,
                                                              text=moved_item.id))

        self.canvas.update()

    def arr_clear_item(self):
        for i in self.item_presentation:
            to_del = self.item_presentation.pop()
            self.canvas.delete(to_del)
            self.canvas.update()


class IsrElement:
    text_height = 30
    icon_top_margin = -8

    def __init__(self, element_name, x_top, y_top, length, height):
        self.element_name = element_name
        self.x_top = x_top
        self.y_top = y_top
        self.length = length
        self.canvas = canvas

        canvas.create_rectangle(x_top, y_top, x_top + length, y_top + height)
        canvas.create_text(x_top + 10, y_top + 7, anchor=tk.NW, text=f"{element_name}")
        self.canvas.update()



class QueueGraphics:
    text_height = 30
    icon_top_margin = -8

    def __init__(self, data_container, icon_height, data_name, x_top):
        # self.icon_file = icon_file
        self.icon_height = icon_height
        self.queue_name = data_name
        self.canvas = canvas
        self.x_top = x_top
        self.y_top = start_row

        # self.image = tk.PhotoImage(file = self.icon_file)
        self.icons = []
        self.data_contained = data_container
        canvas.create_text(self.x_top, self.y_top, anchor = tk.NW, text = f"{data_name}")
        self.canvas.update()

    def paint_queue(self):
        # delete all current representations
        for i in self.icons:
            to_del = self.icons.pop()
            self.canvas.delete(to_del)
            self.canvas.update()
        # redraw for all current items contained
        x = self.x_top + 15
        y = self.y_top + 45

        for i in self.data_contained:
            self.icons.append(
                self.canvas.create_image(x, y, anchor = tk.NW, image = image_map2[i.type])
            )
            self.icons.append(self.canvas.create_text(x - 10, y + 30, anchor = tk.NW, text = i.id))
            y = y + self.icon_height + 45
        self.canvas.update()


class PaintGrapic:

    def __init__(
            self,
            sensor_array_queue,
            array_sensor_queue,
            array_analysis_queue,
            analysis_sublist,
            analysis_array_queue,
            array_action_queue,
            action_array_queue
            ):
        self.sensor_array = QueueGraphics(sensor_array_queue, 25, "Sensor to \n Array", 100)
        self.array_sensor = QueueGraphics(array_sensor_queue, 25, "Array to \n Sensor", 200)
        self.array_analysis = QueueGraphics(array_analysis_queue, 25, "Array to \n Analysis", 300)
        self.analysis_sublist_visual = QueueGraphics(analysis_sublist, 25, "Analysis Station \n Bank", 600)
        self.analysis_array = QueueGraphics(analysis_array_queue, 25, "Analysis to \n Array", 700)
        self.array_action = QueueGraphics(array_action_queue, 25, "Array to \n Action", 800)
        self.action_array = QueueGraphics(action_array_queue, 25, "Action to \n Array", 900)

    def tick(self):
        self.sensor_array.paint_queue()
        self.array_sensor.paint_queue()
        self.array_analysis.paint_queue()
        self.analysis_array.paint_queue()
        self.array_action.paint_queue()
        self.action_array.paint_queue()
        self.analysis_sublist_visual.paint_queue()


class ClockAndDataDraw:

    def __init__(self, x1, y1, x2, y2, time, sensor_list, data_age, data_age_by_type, successful_operations_total,
                 number_of_sensors, agent_flow_rates_by_type, total_resource, self_organization_measure):
        # Draw the inital state of the clock and data on the canvas
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.canvas = canvas
        self.train = canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, fill="#fff")
        self.time = canvas.create_text(self.x1 + 10, self.y1 + 10, text="Time = " + str(round(time, 1)) + "m",
                                       anchor=tk.NW)
        # Code to show the seller wait time at queue.
        #self.seller_wait = canvas.create_text(self.x1 + 10, self.y1 + 40,
        #                                      text="Avg. Seller Wait  = " + str(avg_wait(seller_waits)), anchor=tk.NW)
        # Code to show the scanner wait time at queue.
        #self.scan_wait = canvas.create_text(self.x1 + 10, self.y1 + 70,
        #                                    text="Avg. Scanner Wait = " + str(avg_wait(scan_waits)), anchor=tk.NW)
        self.canvas.update()
        self.data_plot = FigureCanvasTkAgg(f, master=main)
        self.data_plot.get_tk_widget().config(height=400)
        self.data_plot.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.sensor_list_visual = []
        self.sensor_list = sensor_list
        self.data_age = data_age
        self.data_age_by_type = data_age_by_type
        self.successful_operations_total = successful_operations_total
        self.number_of_sensors = number_of_sensors
        self.agent_flow_rates_by_type = agent_flow_rates_by_type
        self.total_resource = total_resource
        self.self_organization_measure = self_organization_measure

    def paint_sensors(self):
        for i in self.sensor_list_visual:
            to_del = self.sensor_list_visual.pop()
            canvas.delete(to_del)
            canvas.update()

        n = 1

        for x in self.sensor_list:
            element_name = x.name
            x_top = 5
            y_top = start_row + (regular_height + 10) * (n - 1)
            n = n + 1
            length = 60
            height = regular_height

            self.sensor_list_visual.append(canvas.create_rectangle(x_top, y_top, x_top + length, y_top + height))
            self.sensor_list_visual.append(canvas.create_text(x_top + 10, y_top + 7, anchor=tk.NW,
                                                              text=f"{element_name}"))
            canvas.update()

    def tick(self, time):
        # re-draw the clock and data fields on the canvas. Also update the matplotlib charts
        canvas.delete(self.time)

        # Delete previous data.
        #self.canvas.delete(self.seller_wait)
        #self.canvas.delete(self.scan_wait)

        self.time = canvas.create_text(self.x1 + 10, self.y1 + 10, text="Time = " + str(round(time, 1)) + "m",
                                       anchor=tk.NW)

        self.paint_sensors()

        a1.cla()
        a1.set_xlabel("Time")
        a1.set_ylabel("Average Data Age")

        a1.plot([t for (t, age) in self.data_age.items()], [np.mean(age) for (t, age) in self.data_age.items()],
                label="all")

        for key in image_map2.keys():
            a1.plot([t for (t, age) in self.data_age_by_type[key].items()],
                    [np.mean(age) for (t, age) in self.data_age_by_type[key].items()], label = key)
        a1.legend(loc="upper left")

        dt = 5

        a2.cla()
        a2.set_xlabel("Time")
        a2.set_ylabel("Accumulated Success")
        # code to calculate step function.
        # successful_operations_total[float(env.now)].append(len([x for x in successful_operations if x > env.now - dt]))
        a2.plot([t for (t, success) in self.successful_operations_total.items()],
                [success for (t, success) in self.successful_operations_total.items()],
                label="Average success over last " + str(dt) + " timesteps")

        a3.cla()
        a3.set_xlabel("Time")
        a3.set_ylabel("System Cost")

        a3.plot([t for (t, a) in self.number_of_sensors.items()],
                [a for (t, a) in self.number_of_sensors.items()],
                label="Sensors")

        for key in self.agent_flow_rates_by_type.keys():
            a3.plot([t for (t, a) in self.agent_flow_rates_by_type[key].items()],
                    [a for (t, a) in self.agent_flow_rates_by_type[key].items()],
                    label=key)
        a3.plot([t for (t, a) in self.total_resource.items()],
                [a for (t, a) in self.total_resource.items()],
                label="Total")

        a3.legend(loc="upper left")

        # to calculate self-org, check how much the system has been
        # "in motion" for the last X timesteps.
        # sum of number of times the resources were re-allocated.

        # self_organization_measure[float(env.now)].append(calc_self_org(dt))
        a2.plot([t for (t, a) in self.self_organization_measure.items()],
                [a for (t, a) in self.self_organization_measure.items()],
                label="Self-organization effort over last " + str(dt) + " timesteps")

        a2.legend(loc="upper left")

        self.data_plot.draw()
        self.canvas.update()


class AnalysisStationDraw:
    def __init__(self):
        self.station_item_presentation = []
        self.x = 405
        self.y = start_row

    def run_draw(self, moved):
        self.station_item_presentation.append(
            canvas.create_image(self.x, self.y + 45, anchor=tk.NW, image=image_map2[moved.type])
        )
        self.station_item_presentation.append(canvas.create_text(self.x, self.y + 75, anchor=tk.NW, text=moved.id))

        canvas.update()

    def run_delete(self):
        for i in self.station_item_presentation:
            to_del = self.station_item_presentation.pop()
            canvas.delete(to_del)
            canvas.update()


def save_graph(env, end_time):
    yield env.timeout(end_time-0.1)
    save_name = "self org plot " + datetime.now().ctime() + " end time " + str(end_time)
    save_name = save_name.replace(":","_")

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(ROOT_DIR, save_name)
    os.mkdir(DATA_DIR)
    CSV_PATH = DATA_DIR + "//data"

    with open(CSV_PATH, 'w', encoding='UTF8') as file:
        writer = csv.writer(file)

        for ax in f.get_axes():
            writer.writerow([ax.get_xlabel,ax.get_ylabel])
            for line in a2.lines:
                d = line.get_label
                writer.writerow([line.get_label])
                x = line.get_xdata()
                y = line.get_ydata()
                for n in range(len(x)):
                    writer.writerow([x[n],y[n]])

    svg_file_name = DATA_DIR + "\\" + save_name + ".svg"
    f.savefig(svg_file_name)

