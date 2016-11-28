'''
Created on Nov 19, 2016

@author: Elliot
'''
import time
import pprint
class SenderWindowManager:
    def __init__(self, sequenceSize):
        self.sequenceSize = sequenceSize
        if sequenceSize == 1:
            self.windowSize = 1
        else:
            self.windowSize = int(self.sequenceSize / 2)
        self.sequenceArray = [False] * self.sequenceSize
        self.packetArray = []
        self.timerArray = []
        self.windowStart = 0
        self.windowEnd = self.windowSize
        self.lastSequence = 0
        self.timeout = 2
    def needMorePacket(self):
        print("last sequence " ,self.lastSequence)
        print("window End ",self.windowEnd)
        return self.lastSequence != self.windowEnd
    #when we push a packet coming from a loop so it is assumed to be a valid number -no delay problem
    def pushPacket(self, pack):
        self.packetArray.append(pack)
        self.timerArray.append(time.time())
        self.lastSequence = (self.lastSequence + 1) % self.sequenceSize
        # need to add more
    def setWindowTrue(self,nackP):
        if nackP != (self.windowEnd)%self.sequenceSize:
            return
        index=0
        while(index<self.windowSize):
            self.sequenceArray[(self.windowStart+index)%self.sequenceSize] =True
            index = index+1
    def moveWindow(self):
        # to do while loop
        print("moving window")
        while(self.sequenceArray[self.windowStart]):
            self.windowStart = (self.windowStart + 1) % self.sequenceSize
            self.windowEnd = (self.windowEnd + 1) % self.sequenceSize
            self.sequenceArray[self.windowEnd] = False
            self.packetArray.pop(0)
            self.timerArray.pop(0)
     #resends a packet if the time since the packet was last sent is great then self.timeout
     #will only increment on the actual number of elements in the timerArray as not every packet may 
     #actually need to be resent   
    def resendPacket(self):
        currentTime = time.time()
        index = 0
        packetsResend = []
        print("resending packets")
        pprint.pprint(self.packetArray)
        while (index < len(self.timerArray)):
            if(self.timeout < (currentTime - self.timerArray[index])):
                
                seqIndex =  (index+self.windowStart)%self.sequenceSize
                if(not self.sequenceArray[seqIndex]):
                    print("WindowNumber ", (self.windowStart+index), " Was resent")
                    packetsResend.append(self.packetArray[index])
                    self.timerArray[index] = currentTime
            index = index + 1
        return packetsResend
    def receiveAck(self, ack):
        # maybe add something to parse the pack nicely
        ack = ack%self.sequenceSize
        self.sequenceArray[ack] = True
    def isBuffering(self):
        return True
        #return len(self.packetArray) != 0
        
        
        
