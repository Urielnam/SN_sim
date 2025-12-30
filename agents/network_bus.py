# The network bus moves data between different queues. It can move only one object per lane.

def check_queue(ctx):
    return len(ctx.iiot_bus_queue) + len(ctx.edge_bus_queue) + len(ctx.scada_bus_queue)

class NetworkBus(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.env = ctx.env
        self.action = self.env.process(self.run())

        self.flow_rate = 1


    def run(self):

        while True:

            # 1. WAIT: freeze process until a packet arrives in the shared bus queue.
            wrapper = yield self.ctx.bus_input_queue.get()

            # Unwrap to get the item from simpy PriorityItem object
            packet = wrapper.item

            # OBSERVER HOOK: Announce transport start
            self.ctx.on_event("bus_transport_start", packet)

            # 2. TRANSPORT DELAY: Simulate the time it takes to move data based on the bus 'flow rate' (Bandwidth).
            yield self.env.timeout(1 / self.flow_rate)

            # OBSERVER HOOK: Announce transport end
            self.ctx.on_event("bus_transport_end", packet)

            # 3. ROUTE: Determine the destination and deliver.
            self._route_packet(packet)

    def _route_packet(self, packet):
        """
        Routes data based on its type.
        """

        if packet.type == 'intel':
            # Raw data goes to Edge Processor
            self.ctx.bus_edge_queue.put(packet)

        elif packet.type == 'target':
            # Processed tragets go to SCADA Actuator
            self.ctx.bus_scada_queue.put(packet)

        elif packet.type == 'feedback':
            # Feedback goes back to IIoT Nodes
            self.ctx.bus_iiot_queue.put(packet)