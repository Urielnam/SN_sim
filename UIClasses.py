import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import BackendClasses


# UIClasses.py
# Refactored for Event-Driven Architecture (SimPy)

class Visualizer:
    """
    The main UI controller. It owns the Tkinter root, manages subscriptions to
    simulation events, and triggers periodic updates for queues and graphs.
    """

    def __init__(self, ctx):
        self.ctx = ctx

        # 1. Initialize Tkinter Root (Encapsulated)
        self.root = tk.Tk()
        self.root.title("ISR Simulation - Event Driven")
        self.root.config(bg="#fff")

        # 2. Load Assets
        self._load_images()

        # 3. Setup Layout
        self._setup_layout()

        # 4. Initialize Sub-Components
        # Animators (Respond to Events)
        self.bus_animator = BusAnimator(self.canvas, self.image_map)
        self.edge_animator = EdgeAnimator(self.canvas, self.image_map)

        # Queue Inspectors (Respond to Ticks)
        self.queues = self._init_queues()

        # Graphs & Clock (Respond to Ticks)
        self.dashboard = Dashboard(self.ctx, self.canvas, self.graph_frame)

        # 5. Subscribe to Simulation Events (The Observer Pattern)
        # This overwrites the empty hook in SimulationContext
        self.ctx.on_event = self.handle_event

    def _load_images(self):
        """Loads images once to be shared across components."""
        try:
            self.logo_img = tk.PhotoImage(file="images/title.png")
            self.image_map = {
                "intel": tk.PhotoImage(file="images/folder.png"),
                "feedback": tk.PhotoImage(file="images/feedback.png"),
                "target": tk.PhotoImage(file="images/target.png")
            }
        except Exception as e:
            print(f"Warning: Could not load images. UI may look broken. {e}")
            self.logo_img = None
            self.image_map = {}

    def _setup_layout(self):
        # Top Frame (Logo)
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, expand=False)
        if self.logo_img:
            tk.Label(top_frame, image=self.logo_img, bg="#000007", height=65, width=1300).pack(side=tk.LEFT)

        # Middle Frame (Canvas for Animation)
        self.canvas = tk.Canvas(self.root, width=1300, height=350, bg="white")
        self.canvas.pack(side=tk.TOP, expand=False)

        # Bottom Frame (Graphs)
        self.graph_frame = tk.Frame(self.root)
        self.graph_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def _init_queues(self):
        """Initializes the static queue visualizations."""

        # Helper to make code cleaner
        def make_q(selector, name, x):
            return QueueGraphics(self.ctx, self.canvas, self.image_map, selector, name, x)

        return [
            make_q("iiot_to_bus", "IIoT to \n Network Bus", 100),
            make_q("bus_to_iiot", "Network Bus to \n IIoT", 200),
            make_q("bus_to_edge", "Network Bus to \n Edge Processor", 300),
            make_q("edge_buffer", "Edge Processor \n Bank", 600),
            make_q("edge_to_bus", "Edge Processor to \n Network Bus", 700),
            make_q("bus_to_scada", "Network Bus to \n SCADA Actuator", 800),
            make_q("scada_to_bus", "SCADA Actuator to \n Network Bus", 900)
        ]

    def handle_event(self, event_type, payload):
        """
        The Observer Hook. Called by agents when something happens.
        """
        if event_type == "bus_transport_start":
            self.bus_animator.animate_start(payload)

        elif event_type == "bus_transport_end":
            self.bus_animator.animate_end()

        elif event_type == "edge_process_start":
            self.edge_animator.animate_start(payload)

        elif event_type == "edge_process_end":
            self.edge_animator.animate_end()

    def tick(self):
        """
        Called every time step by the Simulation clock loop.
        Updates the static state (queues, graphs, clock).
        """
        # Update all queue visualizers (Inspector)
        for q in self.queues:
            q.paint_queue()

        # Update graphs and clock text
        self.dashboard.tick()

        # Refresh UI
        self.root.update()

    def start(self):
        self.root.mainloop()

    def save_snapshot(self, timestamp_str):
        """
        Saves the current state of the Dashboard figure to an SVG file.
        """
        try:
            # 1. Generate Path using the utility in BackendClasses
            folder_name = "visual_snapshots"
            save_dir = BackendClasses.create_folder(folder_name, timestamp_str)

            # 2. Construct Filename
            # We use the simulation time or just a counter
            filename = f"snapshot_T{int(self.ctx.env.now)}.svg"
            full_path = os.path.join(save_dir, filename)

            # 3. Save the Figure (accessed via the Dashboard)
            self.dashboard.fig.savefig(full_path)
            print(f"Snapshot saved: {full_path}")

        except Exception as e:
            print(f"Failed to save snapshot: {e}")


class QueueGraphics:
    """
    Visualizes the contents of a SimPy Queue (Inspector).
    Uses ctx.get_queue_snapshot() to inspect state without breaking encapsulation.
    """

    def __init__(self, ctx, canvas, image_map, selector, name, x_top):
        self.ctx = ctx
        self.canvas = canvas
        self.image_map = image_map
        self.selector = selector  # String ID used to ask Context for data
        self.x_top = x_top
        self.y_top = 95  # start_row

        self.icons = []

        # Draw Title
        self.canvas.create_text(self.x_top, self.y_top, anchor=tk.NW, text=name)

    def paint_queue(self):
        # 1. Clear old icons
        for icon in self.icons:
            self.canvas.delete(icon)
        self.icons.clear()

        # 2. Fetch Fresh Data (The Snapshot)
        packet_list = self.ctx.get_queue_snapshot(self.selector)

        # 3. Draw
        x = self.x_top + 15
        y = self.y_top + 45
        icon_height = 25

        for packet in packet_list:
            # Safe access to packet attributes
            if packet.type in self.image_map:
                img_id = self.canvas.create_image(x, y, anchor=tk.NW, image=self.image_map[packet.type])
                txt_id = self.canvas.create_text(x - 10, y + 30, anchor=tk.NW, text=packet.id)
                self.icons.extend([img_id, txt_id])

            y = y + icon_height + 45


class BusAnimator:
    """Handles the animation of items moving across the bus."""

    def __init__(self, canvas, image_map):
        self.canvas = canvas
        self.image_map = image_map
        self.active_items = []
        self.x = 105
        self.y = 20

        # Draw the Bus Line
        # IsrElement("Network Bus", 5, 20, 1290, 65) roughly
        self.canvas.create_rectangle(5, 20, 1295, 85)
        self.canvas.create_text(15, 27, anchor=tk.NW, text="Network Bus")

    def animate_start(self, packet):
        if packet.type in self.image_map:
            img_id = self.canvas.create_image(self.x, self.y, anchor=tk.NW, image=self.image_map[packet.type])
            txt_id = self.canvas.create_text(self.x, self.y + 30, anchor=tk.NW, text=packet.id)
            self.active_items.extend([img_id, txt_id])

    def animate_end(self):
        # Clear specific items or all active (assuming single lane bus for now)
        while self.active_items:
            item = self.active_items.pop()
            self.canvas.delete(item)


class EdgeAnimator:
    """Handles the animation of the Edge Processor working."""

    def __init__(self, canvas, image_map):
        self.canvas = canvas
        self.image_map = image_map
        self.active_items = []
        self.x = 405
        self.y = 95  # start_row

    def animate_start(self, packet):
        if packet.type in self.image_map:
            img_id = self.canvas.create_image(self.x, self.y + 45, anchor=tk.NW, image=self.image_map[packet.type])
            txt_id = self.canvas.create_text(self.x, self.y + 75, anchor=tk.NW, text=packet.id)
            self.active_items.extend([img_id, txt_id])

    def animate_end(self):
        while self.active_items:
            item = self.active_items.pop()
            self.canvas.delete(item)


class Dashboard:
    """Manages the Matplotlib graphs and the Clock text."""

    def __init__(self, ctx, canvas, graph_frame):
        self.ctx = ctx
        self.canvas = canvas

        # Clock Text
        self.clock_text_id = None
        self.x_clock = 1100
        self.y_clock = 260
        self.canvas.create_rectangle(self.x_clock, self.y_clock, 1290, 340, fill="#fff")

        # Matplotlib Setup
        self.fig = plt.Figure(figsize=(2, 2), dpi=72)
        self.ax_age = self.fig.add_subplot(222)
        self.ax_success = self.fig.add_subplot(224)
        self.ax_cost = self.fig.add_subplot(121)

        self.plot_canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.plot_canvas.get_tk_widget().config(height=400)
        self.plot_canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def tick(self):
        # 1. Update Clock
        time = self.ctx.env.now
        if self.clock_text_id:
            self.canvas.delete(self.clock_text_id)
        self.clock_text_id = self.canvas.create_text(
            self.x_clock + 10, self.y_clock + 10,
            text="Time = " + str(round(time, 1)) + "m",
            anchor=tk.NW
        )

        # 2. Update Graphs (Simplified for performance, full redraw is heavy)
        # Only redraw every 5 ticks or so if performance lags, but for now we do every tick

        # Data Age Plot
        self.ax_age.cla()
        self.ax_age.set_xlabel("Time")
        self.ax_age.set_ylabel("Avg Data Age")

        if self.ctx.data_age:
            times = list(self.ctx.data_age.keys())
            avgs = [np.mean(v) for v in self.ctx.data_age.values()]
            self.ax_age.plot(times, avgs, label="All")
        self.ax_age.legend(loc="upper left")

        # Success Plot
        self.ax_success.cla()
        self.ax_success.set_xlabel("Time")
        self.ax_success.set_ylabel("Accum. Success")
        if self.ctx.successful_operations_total:
            t = list(self.ctx.successful_operations_total.keys())
            v = list(self.ctx.successful_operations_total.values())
            self.ax_success.plot(t, v, label="Success")
        self.ax_success.legend(loc="upper left")

        # Cost/Resource Plot
        self.ax_cost.cla()
        self.ax_cost.set_xlabel("Time")
        self.ax_cost.set_ylabel("System Cost")
        if self.ctx.number_of_iiots:
            t = list(self.ctx.number_of_iiots.keys())
            v = list(self.ctx.number_of_iiots.values())
            self.ax_cost.plot(t, v, label="IIoT Nodes")

        self.ax_cost.legend(loc="upper left")

        self.plot_canvas.draw()