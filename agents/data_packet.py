class DataPacket:
    def __init__(self, status, time, type, creator):
        # status parameter is real/false - it's the notion of if the data is right or wrong.
        self.status = status
        self.time = time
        # data types - intel, feedback
        self.type = type
        self.creator = creator
        # adds an image so that we can paint it later
        self.id = self.type + " from " + self.creator + "\n at time " + str(self.time)