import sys
import pprint
from packet import Packet

import SenderWindowManager
import ReceiverWindowManager


PAYLOAD_MAX_SIZE = 1013      # bytes

# packet types
DATA = 0
SYN = 1
ACK = 2
SYN_ACK = 3
NAK = 5
FINAL_ACK = 6
FINAL_ACK_B = 7


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

    timeout = 7

    receiver_ip = None
    receiver_port = None

    num_packets = len(packets)
    print("packet length ", num_packets)

    windowManager =SenderWindowManager.SenderWindowManager(num_packets)
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
        
        while packet_type == ACK:
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
    p = Packet(packet_type=6,
               seq_num=1,
               peer_ip_addr=receiver_ip,
               peer_port=receiver_port,
               payload=msg.encode("utf-8"))

    # send SYN packet
    conn.sendto(p.to_bytes(), (router_addr, router_port))
    conn.settimeout(timeout)

    print("sending final ACK")
    print("left loop")


def SR_Receiver(conn, num_packets):

    # conn.settimeout(50)
    timeout = 5

    print("Expected num of packets: ", num_packets)

    # rWindowManager = ReceiverWindowManager.ReceiverWindowManager(33)

    # supply num of packets expected from client
    rWindowManager = ReceiverWindowManager.ReceiverWindowManager(num_packets)


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


    if packet_type == FINAL_ACK:
        print ("--- final ACK received  ---")

    print("here")

    # if final ACK received dont go here

    while packet_type == DATA:

        try:

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

                print("sending ACK: ", p_s.seq_num)
                conn.sendto(ack_p.to_bytes(), sender)

                received_packets += 1

            # packets_from_SR.append(packet_from_SR)
            packets_from_SR += packet_from_SR
            

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

        except conn.timeout:
            print('No response after {}s'.format(5))
            return False

        finally:
            pass


    print("either finish or final ACK received")

    ###### APP LAYER ##########
    print("SR result Packet[]")
    print("after SR")
    for pp in packets_from_SR:
        print(type(p))
        print(p.payload)
        print(p.seq_num)
        print(p.peer_ip_addr)

    return packets_from_SR, sender