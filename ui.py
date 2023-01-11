import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict

import tkinter as tk
from  UIClasses import ClockAndDataDraw
# -------------------------
# UI/ANIMATION
# -------------------------

main = tk.Tk()
main.title("ISR Simulation")
main.config(bg="#fff")
logo = tk.PhotoImage(file="images/title.png")
top_frame = tk.Frame(main)
top_frame.pack(side=tk.TOP, expand= False)
tk.Label(top_frame, image=logo, bg= "#000007", height=65, width=1300).pack(side=tk.LEFT, expand=False)
canvas = tk.Canvas(main, width=1300, height= 350, bg="white")
canvas.pack(side=tk.TOP, expand=False)

start_row = 95
regular_height = 30

image_map2 = {
    "intel": tk.PhotoImage(file = "images/folder.png"),
    "feedback": tk.PhotoImage(file = "images/feedback.png"),
    "target": tk.PhotoImage(file = "images/target.png")
}

for key in image_map2.keys():
    data_age_by_type[key] = defaultdict(lambda: [])

def save_graph(env):
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

clock = ClockAndDataDraw(canvas, 1100, 260, 1290, 340, 0, main)
grapic=

def ui_refresh(now):
    clock.tick(now)
