import argparse
import socket
import json
import pprint
import sys

import os



from packet import Packet
import process_http_file
import SR_helper
import ReceiverWindowManager


# packet types
DATA = 0
SYN = 1
ACK = 2
SYN_ACK = 3
NAK = 5

PAYLOAD_MAX_SIZE = 1013      # bytes

three_way_handshake_good = False

address = '127.0.0.1'


"""
1. Implement 3-way handshake before sending anything

client  -> (SYN) SEQ=1                                            [SYN, SYN=1, ACK=0]
            (SYN-ACK) ACK=2, SEQ=100    <- server                 [SYN, SYN=1, ACK=1]
client  -> (ACK) ACK=101, SEQ=2                                 [NO SYN, SYN=0, ACK=1]

for now, it is assumed that for every client request, a handshake
needs to be established, since we are using HTTP 1.0 (non-persistent)

after successfull handshake, data is then sent by client and should be accepted by server

"""



def process_http_request(conn, host, port, data, directory, sender, isVerb):
    # need to decide on a fixed window size
    rWindowManager = ReceiverWindowManager.ReceiverWindowManager(33)
    while True:


        # TODO: instead of receiving a HTTP request packet directly from conn
        # receive Packets[] array (already converted or to convert) to an HTTP request)
        # from SR algorithm

        ############################################


        ################### PUT SR_Receiver call here #################
        # packets_from_SR = SR_Receiver()
        packets_from_SR = []
        ###############################################################


        # for now, assume we are only getting one packet and we can decode it right away


        expected_packet_num = 1
        received_packets = 0
        request, sender = conn.recvfrom(1024)
        # do this for all received packets from SR
        p = Packet.from_bytes(request)

        packet_type = p.packet_type
        seq_num = p.seq_num

        while packet_type == DATA:

            rWindowManager.receivePacket(seq_num, p)

            # packets_from_SR.append(p)

            packet_from_SR = rWindowManager.moveWindow()

            for p_s in packet_from_SR:
                # send ACK



                # # create ACK packet, ack will be in payload since we dont have ACK in the Packet data structure
                # my_dict_payload = {}
                # my_dict_payload['ack'] = my_ack
                # my_dict_payload['msg'] = ""
                # msg = json.dumps(my_dict_payload)

                # # create final ACK packet
                # ack_p = Packet(packet_type=ACK,
                #        seq_num=my_seq_num,
                #        peer_ip_addr=peer_ip,
                #        peer_port=server_port,
                #        payload=msg.encode("utf-8"))

                # print("sending ACK: ", my_ack, " SEQ:", my_seq_num)

                # conn.sendto(ack_p.to_bytes(), sender)
                # print("ACK sent... We could also piggyback data here")
                # conn.settimeout(5)
                

            # packets_from_SR.append(packet_from_SR)
            packets_from_SR += packet_from_SR
            received_packets += 1


            # print("payload of p:")
            # print(p.payload.decode("utf-8"))
            
            # next packet
            # conn.settimeout(15)
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
            else:
                break


        ###### APP LAYER ##########
        print("SR result Packet[]")
        print("after SR")
        for pp in packets_from_SR:
            print(type(p))
            print(p.payload)
            print(p.seq_num)
            print(p.peer_ip_addr)


        # pprint.pprint(packets_from_SR)
        http_request, peer_ip, peer_port = SR_helper.SR_to_appmessage(packets_from_SR)

        # assume at this point we have HTTP request
        print("===== HTTP request ======")
        print(http_request)

        #############################################
        
        # formulate response by invoking httpfs
        http_response  = process_http_file.process_Req(http_request, address, port, directory, isVerb)
        print(http_response)

        packets = SR_helper.prepare_SR(peer_ip, peer_port, http_response)

        # TODO transition to a sender and send HTTP response through SR

        ################### PUT SR_Sender call here #################
        # SR_Sender(packets)

        p = packets[0]
        conn.sendto(p.to_bytes(), sender)
        print('Send "{}" to router'.format(p))
        ###############################################################

        print("HTTP Response sent")

def run_server(host, port, directory, isVerb):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # HOST = socket.gethostbyname(socket.gethostname())
        # conn.bind((HOST, port))

        if os.path.isdir(directory):
            pass
        else:
            print("directory entered does not exist", directory)
            return

        conn.bind(('', port))
        # print (conn.getsockname())


        print('Echo server is listening at', port)
        # while True:
        #     data, sender = conn.recvfrom(1024)
        #     handle_client(conn, data, sender)


        ### MULTI-THREADING ###

        # threads = []
        # while True:
        #     conn, addr = listener.accept()
        #     # going to figure out what the threading does exactly
        #     t1 =threading.Thread(target=handle_client, args=(conn, addr, port, directory,isVerb))
        #     t1.start()
        #     threads.append(t1)
        # for t in threads:
        #     t.join()

        conn, data, sender = three_way_handshake(conn)
        print("Handshake done")
        process_http_request(conn, host, port, data, directory, sender, isVerb)

    finally:
        conn.close()

# process_http_request(conn, data, sender, his_seq_num, http_request)



def three_way_handshake(conn):
    initial_seq_num = 500 
    global three_way_handshake_good

    while three_way_handshake_good != True:

        data, sender = conn.recvfrom(1024)
        # handle_client(conn, data, sender)
    
        # generate my own seq_num
        try:
            p = Packet.from_bytes(data)

            packet_type = p.packet_type
            his_seq_num = p.seq_num
            peer_ip = p.peer_ip_addr
            peer_port = p.peer_port 
            his_payload = p.payload.decode("utf-8")

            # check packet type
            if packet_type == SYN:

                print("received SYN with SEQ: ", his_seq_num)

                # 2nd step of handshake : if SYN, this is step 1 of handshake, add 1 to client's seq_num
                my_ack = his_seq_num + 1

                # HANDSHAKE step 2
                # create SYN_ACK packet, ack will be in payload since we dont have ACK in the Packet data structure
                my_dict_payload = {}
                my_dict_payload['ack'] = my_ack
                my_dict_payload['msg'] = ""
                msg = json.dumps(my_dict_payload)

                syn_ack_p = Packet(packet_type=SYN_ACK,
                       seq_num=initial_seq_num,
                       peer_ip_addr=peer_ip,
                       peer_port=peer_port,
                       payload=msg.encode("utf-8"))

                print("Sending SYN_ACK with SEQ: ", initial_seq_num, " ACK: ", my_ack)

                conn.sendto(syn_ack_p.to_bytes(), sender)

                conn.settimeout(5)

                #### wait for final ACK for Handshake from Client

            # receives an ACK
            elif packet_type == ACK:  
                # get ack from payload
                dict_payload = json.loads(his_payload)
                ack_good = False

                try:

                    his_ack = dict_payload['ack']
                    print("received final handshake ACK: ", his_ack, " SEQ: ", his_seq_num)

                    # check if ack sent by client is my seq + 1
                    if his_ack == (initial_seq_num + 1):
                        three_way_handshake_good = True
                        ack_good = True
                        print("Server side: 3 way handshake completed. Waiting for HTTP request...")

                    else:
                        print("Wrong ACK number received")
                        # wrong ACK number recieved, send NAK

                except KeyError:
                    print("ACK not found in packet")

                
                # send NAK if ACK not found in payload or not the correct ACK#
                if ack_good != True:
                    msg = "ack not receieved correctly. restart handshake"
                    nak_p = Packet(packet_type=NAK,
                           seq_num=0,
                           peer_ip_addr=peer_ip,
                           peer_port=peer_port,
                           payload=msg.encode("utf-8"))

                    print("Sending NAK: ")
                    conn.sendto(nak_p.to_bytes(), sender)

                    # conn.settimeout(5)                        

            elif packet_type == DATA:
                if three_way_handshake_good:
                    break
                else:
                    print("3-way handshake not completed yet. Data packet refused")
                    

            # if three_way_handshake_good:
            #     print("Router: ", sender)
            #     print("Packet: ", p)
            #     print("Payload: ", p.payload.decode("utf-8"))
            #     print("Packet Type: ", packet_type)

            # else:
            #     print("waiting for client to (re)start handshake")

            # How to send a reply.
            # The peer address of the packet p is the address of the client already.
            # We will send the same payload of p. Thus we can re-use either `data` or `p`.


            # conn.sendto(p.to_bytes(), sender)

        except Exception as e:
            print("Error: ", e)

    return conn, data, sender


dir_path = os.getcwd()

# Usage python udp_server.py [--port port-number]
parser = argparse.ArgumentParser()
parser.add_argument("--port", help="echo server port", type=int, default=8007)

parser.add_argument("-v", help="prints debugging messagges", action="store_true")
# parser.add_argument("-p", "--port", help="Specifies the port number that the server will listen at default is 8080", type=int, default=8007, metavar="")
parser.add_argument("-d", "--Path", help="Specifies the directory that the server will use to read/write requested files. Default is the current directory when launching the application.",
                    metavar="", default=dir_path, type=str) 

args = parser.parse_args()
run_server('', args.port, args.Path, args.v)
