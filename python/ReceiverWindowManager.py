'''
Created on Nov 19, 2016

@author: Elliot
'''

from packet import Packet
import pprint

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

        # print("CONSTRUCTOR---")
        # print("Sequence size: ", self.sequenceSize)
        # print("Window size: ", self.windowSize)
        # print("Window start: ", self.windowStart)
        # print("Window end: ", self.windowEnd)               

    def receivePacket(self, sequenceNumber,buf):

        print("Received packet: ", sequenceNumber)
        print(buf)
        if(self.isValidSequenceNumber(sequenceNumber)):
            print("Valid seq")
            index = self.sequenceToWindowIndex(sequenceNumber)
            print("index of actual value ",index)
            #index = sequenceNumber
            if(self.sequenceArray[sequenceNumber] is False):
                print("Actual receive")
                self.sequenceArray[sequenceNumber] = True
                self.bufferArray[index] = buf
                print("")
            else:
                print("need to resend ACK")

    def moveWindow(self):
        print("in move window")
        pprint.pprint(self.bufferArray)
        print("did not make it to good part of move window yet")
        result = []
        while(self.sequenceArray[self.windowStart]):
            print("moving the actual window")
            # self.windowStart = (self.windowStart + 1) % self.windowSize
            # self.windowEnd = (self.windowEnd + 1) % self.windowEnd
            self.windowStart = (self.windowStart + 1) % self.sequenceSize
            self.windowEnd = (self.windowEnd + 1) % self.sequenceSize            
            self.sequenceArray[self.windowEnd] = False
            print("buffer length", len(self.bufferArray))
            #printing the buffer array not seeing this now
            pprint.pprint(self.bufferArray)
            pack = self.bufferArray.pop(0)
            self.bufferArray.append(None)
            #print("in movewindow")
            print(pack)
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
        # print("IF VALID SEQNUM")
        # print("Seq num: ", sequenceNumber)
        # print("Sequence size: ", self.sequenceSize)
        # print("Window size: ", self.windowSize)
        # print("Window start: ", self.windowStart)
        # print("Window end: ", self.windowEnd)   

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