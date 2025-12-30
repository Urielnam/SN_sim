import UIClasses, random
from agents.data_packet import DataPacket

# need to create edge processor station, then scada actuator and then start messing with accuracy.
# if one of the intel is true, the intel is correct and the boogie is found. if both are false, the attack failes.
# I need to change it so it ingests one intel article per cycle.
class EdgeProcessor(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.env = ctx.env
        self.action = ctx.env.process(self.run())
        self.ui_flag = ctx.config.ui
        self.flow_rate = 1

        if self.ui_flag:
            self.draw = UIClasses.EdgeStationDraw()

    def run(self):
        bank_size =2

        while True:

            # 1. WAIT
            # The process freezes here. It only wakes up when the Bus delivers a packet to 'bus_edge_queue'.
            moved_item = yield self.ctx.bus_edge_queue.get()

            # record metrics
            self.ctx.edge_data_usage_time.append(self.env.now - moved_item.time)

            # UI visualization
            if self.ui_flag:
                self.draw.run_draw(moved_item)

            # 2. PROCESS (Simulate Latency)
            yield self.env.timeout(1/self.flow_rate)

            if self.ui_flag:
                self.draw.run_delete()

            # 3. LOGIC
            if moved_item.type == 'feedback':
                # Feedback is passed through immediately back to the bus
                # We use the helper to wrap it with a random priority key
                yield self.ctx.send_to_bus(moved_item)

            else:
                # Accumulate 'Intel' packets in the local bank
                self.ctx.edge_sublist.append(moved_item)

                # Fuse data if bank is full
                if len(self.ctx.edge_sublist) >= bank_size:
                    # Pop the first two items
                    item1 = self.ctx.edge_sublist.pop(0)
                    item2 = self.ctx.edge_sublist.pop(0)

                    # Logic: If either source was true, the target is confirmed
                    new_status = item1.status or item2.status

                    # Logic: Attribute to a random creator from the sources
                    new_creator = random.choice([item1, item2]).creator

                    target_packet = DataPacket(
                        status=new_status,
                        time=self.env.now,
                        type='target',
                        creator=new_creator
                    )

                    # Send the fused 'Target' packet to the Bus
                    yield self.ctx.send_to_bus(target_packet)
