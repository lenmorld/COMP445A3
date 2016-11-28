import sys
import pprint
from packet import Packet
import time

import SenderWindowManager
import ReceiverWindowManager


PAYLOAD_MAX_SIZE = 1013      # bytes

# packet types
DATA = 0
SYN = 1
ACK = 2
SYN_ACK = 3
ACK_HANDSHAKE = 4
NAK = 5
FINAL_ACK = 6
FINAL_ACK_B = 7
SYN_LENGTH = 8
SYN_ACK_LENGTH = 9
ACK_LENGTH = 10

def prepare_SR(peer_ip, server_port, payload):

    # encode before | after we split

    packets = {}
    seq_num = 0

    with open("temp.bin", "wb") as f:
        f.write(bytes(payload, "utf-8"))

    with open("temp.bin", "rb") as f:
        payload = f.read(PAYLOAD_MAX_SIZE)

        while payload != b"":

            p = Packet(packet_type=DATA,
                       seq_num=seq_num,
                       peer_ip_addr=peer_ip,
                       peer_port=server_port,
                       payload=payload)
        
            packets[seq_num] = p
            seq_num += 1
            payload = f.read(PAYLOAD_MAX_SIZE)

    print ("HTTP request|response broken into 1013-byte Packets[]")
    for k,v in packets.items():
        print (k, ":", sys.getsizeof(v), " bytes")
        pprint.pprint(vars(v))


    return packets


def SR_to_appmessage(packets):

    # get Packet[] array from SR then package together into original form
    # as HTTP request | response

    http_message = ""

    # we assume all of them have the same host:port
    
    # pprint.pprint(packets[0])
    # print(packets[0].payload)
    # print(type(packets))
    # print(type(packets[0]))
    # print(packets[0].payload.decode("utf-8"))

    peer_ip = packets[0].peer_ip_addr
    server_port = packets[0].peer_port

    # with open("temp.bin", "rb"):
    for p in packets:
        http_message += p.payload.decode("utf-8")
         

    print("HTTP message assembled from SR:")
    print(http_message)


    return http_message, peer_ip, server_port


def SR_Sender(router_addr, router_port, conn, packets):

    timeout = 1

    receiver_ip = None
    receiver_port = None

    conn.settimeout(timeout)

    num_packets = len(packets)
    print("packet length ", num_packets)

    windowManager =SenderWindowManager.SenderWindowManager(20)
    indexReceived=0
    indexSent=0;
    index=0
    while(indexReceived < num_packets):  
        print("indexReceived: ", indexReceived)
        print("num_packets: ", num_packets)

        while (windowManager.needMorePacket() and indexSent<num_packets):
            p = packets[indexSent]

            # print("payload of p:")
            # print(p.payload.decode("utf-8"))

            p_seq_num = p.seq_num

            receiver_ip = p.peer_ip_addr
            receiver_port = p.peer_port

            print('Send "{}" to router'.format(p))
            windowManager.pushPacket(p)
            conn.sendto(p.to_bytes(),(router_addr,router_port))
            print ("send packet number", p_seq_num)
            indexSent = indexSent+1

            # input()

        #handle receivec packets here

        # conn.settimeout(timeout)

        ### RECEIVE ACKs ####
        # conn.setblocking(0)
        try:
            data, sender = conn.recvfrom(1024)
            p = Packet.from_bytes(data)
            packet_type = p.packet_type
        except:
            print("No ACK yet")
            packet_type = None


        ####################################################################
        if packet_type == FINAL_ACK_B:
            print("Receiver received everything. HTTP transaction complete")
            break
        ####################################################################
        
        while packet_type == ACK or packet_type==NAK:
            if packet_type==NAK:
                nack_num= p.seq_num
                windowManager.setWindowTrue(nack_num)
            else:
                ack_num = p.seq_num
                windowManager.receiveAck(ack_num)
                indexReceived = indexReceived+1
                print("ACK#  received", ack_num)
    
                # get next ACK
                print("wait for next ACK")
    
                #conn.setblocking(0)
                # data, sender = conn.recvfrom(1024)
            try:
                data, sender = conn.recvfrom(1024)
                p = Packet.from_bytes(data)
                packet_type = p.packet_type
            except:
                print("No ACK yet")
                packet_type = None


        print("indexReceived: ", indexReceived)
        print("num_packets: ", num_packets)

        if indexReceived >= num_packets:
            print("received all packets")
            print("index received", indexReceived)
            print("total packets sent",num_packets)
            break
        else: 
            pass

        windowManager.moveWindow()
        #hanlde socket timeout
        resendList = windowManager.resendPacket()

        for p in resendList:
            conn.sendto(p.to_bytes(),(router_addr,router_port))
            print('Send "{}" to router'.format(p))
        if windowManager.isBuffering():
            pass
        else:
            print("you killed the loop")
            break




    # final ack if all ACKs are received

    msg = ""   # no payload in handshake
    p = Packet(packet_type=FINAL_ACK,
               seq_num=678678,
               peer_ip_addr=receiver_ip,
               peer_port=receiver_port,
               payload=msg.encode("utf-8"))

    # conn.sendto(p.to_bytes(), (router_addr, router_port))
    conn.settimeout(timeout)

    # send FINAL_ACK 5 times

    send_ctr_2 = 0

    while (send_ctr_2 < 5):

        print("->sending FINAL_ACK: ", p)
        conn.sendto(p.to_bytes(), (router_addr, router_port))
        print("FINAL_ACK sent... ")
        
        send_ctr_2 += 1


    # print("sending final ACK")
    print("left loop")


def SR_Receiver(conn, num_packets):

    # conn.settimeout(50)
    timeout = 10

    # receiver_ip = None
    # receiver_port = None

    print("Expected num of packets: ", num_packets)

    # rWindowManager = ReceiverWindowManager.ReceiverWindowManager(33)

    # supply num of packets expected from client
    rWindowManager = ReceiverWindowManager.ReceiverWindowManager(20)


    # TODO: instead of receiving a HTTP request packet directly from conn
    # receive Packets[] array (already converted or to convert) to an HTTP request)
    # from SR algorithm

    ############################################


    ################### PUT SR_Receiver call here #################
    # packets_from_SR = SR_Receiver()
    packets_from_SR = []
    ###############################################################

    # for now, assume we are only getting one packet and we can decode it right away

    # expected_packet_num = 10
    expected_packet_num = num_packets
    received_packets = 0
    request, sender = conn.recvfrom(1024)
    # do this for all received packets from SR
    p = Packet.from_bytes(request)

    packet_type = p.packet_type
    seq_num = p.seq_num

    receiver_ip = p.peer_ip_addr
    receiver_port = p.peer_port


    if packet_type == FINAL_ACK:
        print ("--- final ACK received  ---")

    print(packet_type)

    print("here")
    # if final ACK received dont go here


    # while packet_type == DATA or packet_type == ACK_HANDSHAKE \
    #     or packet_type == ACK_LENGTH or packet_type == FINAL_ACK or packet_type == FINAL_ACK_B:

    while packet_type in [DATA, SYN, ACK, SYN_ACK, ACK_HANDSHAKE, NAK, FINAL_ACK, FINAL_ACK_B, SYN_LENGTH, SYN_ACK_LENGTH, ACK_LENGTH]:
        try:

            # if packet_type == ACK_HANDSHAKE:
            #     print("---- extra ACK_HANDSHAKE received, ignore ----")
            #     # continue
            # elif packet_type == ACK_LENGTH:
            #     print("---- extra ACK_LENGTH_HANDSHAKE received, ignore ----")
            # elif packet_type == FINAL_ACK:
            #     print("---- extra FINAL_ACK received, ignore ---")
            # elif packet_type == FINAL_ACK_B:
            #     print("---- extra FINAL_ACK_B received, ignore ---")

            if packet_type in [SYN,ACK, SYN_ACK, ACK_HANDSHAKE, NAK, FINAL_ACK, FINAL_ACK_B, SYN_LENGTH, SYN_ACK_LENGTH, ACK_LENGTH]:
                print("Packet type invalid", packet_type)

            else:

                print("receive packet# ", seq_num)

                rWindowManager.receivePacket(seq_num, p)

                # packets_from_SR.append(p)
                          
                packet_from_SR = rWindowManager.moveWindow()

                # for each packet received, send ACK
                for p_s in packet_from_SR:

                    print("Packet to be ACKed: ", p_s.seq_num)
                    msg = ""
                    # create ACK packet with ACK# in seq_num
                    ack_p = Packet(packet_type=ACK,
                           seq_num=p_s.seq_num,
                           peer_ip_addr=p_s.peer_ip_addr,
                           peer_port=p_s.peer_port,
                           payload=msg.encode("utf-8"))

                    # receiver_ip = p_s.peer_ip_addr
                    # receiver_port = p_s.peer_port

                    print("sending ACK: ", p_s.seq_num)
                    conn.sendto(ack_p.to_bytes(), sender)

                    received_packets += 1

                # packets_from_SR.append(packet_from_SR)
                packets_from_SR += packet_from_SR
                # only needed if whole buffer is not cleared
                packets_out = rWindowManager.packetsOutOfOrder()
                print(packets_out)
                #maybe we will send twice cause really important
                if rWindowManager.outOfOrder:
                    print("packet out of order")
                    print("sending a nack for ",rWindowManager.windowStart)
                    errorMsg="out of order"
                    nck_p = Packet(packet_type=NAK,
                           seq_num=rWindowManager.windowStart,
                           peer_ip_addr=p_s.peer_ip_addr,
                           peer_port=p_s.peer_port,
                           payload=errorMsg.encode("utf-8"))
                    rWindowManager.outOfOrder =False
                    conn.sendto(nck_p.to_bytes(), sender)
                    
                """
                for p_s in packets_out:
                    print("Packet to be ACKed: ", p_s.seq_num)
                    msg = ""
                    # create ACK packet with ACK# in seq_num
                    ack_p = Packet(packet_type=ACK,
                           seq_num=p_s.seq_num,
                           peer_ip_addr=p_s.peer_ip_addr,
                           peer_port=p_s.peer_port,
                           payload=msg.encode("utf-8"))

                    receiver_ip = p_s.peer_ip_addr
                    receiver_port = p_s.peer_port

                    print("sending ACK: ", p_s.seq_num)
                    conn.sendto(ack_p.to_bytes(), sender)
                    #done count received only count when we clear the buffer
                    #received_packets += 1
                """

                # Try to receive ACKs within timeout
                conn.settimeout(timeout)

            # next packet
            if received_packets < expected_packet_num:
                print("**** next packet ****")
                request, sender = conn.recvfrom(1024)
                print(request, sender)
                print("Type of sender" ,type(sender))
                if sender == None:
                    break

                # do this for all received packets from SR
                p = Packet.from_bytes(request)
                packet_type = p.packet_type
                seq_num = p.seq_num
            else:
                print(">> more packets expected")
                break

        except:
            print('No response after {}s'.format(timeout))
            return

        finally:
            pass


    print("either finish or final ACK received")


    # TODO: what if this final ACK is lost

    ###########################################################
    # final ack if all ACKs are received

    msg = ""   # no payload in handshake
    p = Packet(packet_type=FINAL_ACK_B,
               seq_num=789789,
               peer_ip_addr=receiver_ip,
               peer_port=receiver_port,
               payload=msg.encode("utf-8"))

    # send SYN packet
    # conn.sendto(p.to_bytes(), sender)
    conn.settimeout(timeout)

    print("sending final ACK to finalize HTTP transaction")

    # send FINAL_ACK_B 5 times to make sure

    send_ctr_2 = 0

    while (send_ctr_2 < 5):

        print("->sending FINAL_ACK_B: ", p)
        conn.sendto(p.to_bytes(), sender)
        print("FINAL_ACK_B sent... ")
        
        send_ctr_2 += 1

    ###############################################################

    ###### APP LAYER ##########
    print("SR result Packet[]")
    print("len packets: ", len(packets_from_SR))
    print("after SR")
    for pp in packets_from_SR:
        print(type(p))
        print(p.payload)
        print(p.seq_num)
        print(p.peer_ip_addr)

    return packets_from_SR, sender


    # alert Sender that everything received


