'''
Created on Nov 19, 2016

@author: Elliot
'''

from packet import Packet

class ReceiverWindowManager:
    def __init__(self, sequenceSize):
        self.sequenceSize = sequenceSize
        if(self.sequenceSize == 1):
            self.windowSize = 1
        else:
            self.windowSize = int(self.sequenceSize / 2)
        self.sequenceArray = [False] * self.sequenceSize
        self.bufferArray = [None] * self.windowSize
        self.sizeArray = [0] * self.windowSize
        self.windowStart = 0
        self.windowEnd = self.windowSize

    def receivePacket(self, sequenceNumber,buf):

        if(self.isValidSequenceNumber(sequenceNumber)):
            # index = self.sequenceToWindowIndex(sequenceNumber)
            index = sequenceNumber
            if(self.sequenceArray[index] is False):
                self.sequenceArray[index] = True
                self.bufferArray[index] = buf
                print("")
            else:
                print("need to resend ACK")

    def moveWindow(self):
        result = []
        while(self.sequenceArray[self.windowStart]):
            self.windowStart = (self.windowStart + 1) % self.windowSize
            self.windowEnd = (self.windowEnd + 1) % self.windowEnd
            self.sequenceArray[self.windowEnd] = False
            pack = self.bufferArray.pop(0)
            # print("in movewindow")
            # print(type(pack))
            result.append(pack)
            #result.append()
            #append result with stuff
    
        # print(result)
        return result
               
    def sequenceToWindowIndex(self, sequenceNumber):
        ptr = self.windowStart
        index = 0
        while(ptr != sequenceNumber):
            ptr = (ptr + 1) % self.sequenceSize
            index = index + 1
        return index

    def isValidSequenceNumber(self, sequenceNumber):
        if(self.windowStart < self.windowEnd):
            if(self.windowStart <= sequenceNumber and sequenceNumber < self.windowEnd):
                return True
            else:
                return False
            if(self.windowEnd < self.windowStart):
                if(sequenceNumber < self.windowEnd or self.windowStart <= sequenceNumber):
                    return True
                else:
                    return False