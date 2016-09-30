import sys
class sensor_client:
    def __init__(self, username, password):
        self.running_count = 0
        self.running_sum = 0
        self.max_temp = sys.maxint * -1 + 1
        self.min_temp = sys.maxint
        self.username = username
        self.password = password
    def update(self, temp):
        if (temp > self.max_temp):
            self.max_temp = temp
        if (temp < self.min_temp):
            self.min_temp = temp
        self.running_count+= 1
        self.running_sum += temp
    def average(self):
        return self.running_sum/self.running_count

class protocol:
    AUTH = "AUTH"
    CHAL = "CHAL"
    RESP = "RESP"
    CONT = "CONT"
    REFD = "REFD"
    TEMP = "TEMP"
    END = "END"
