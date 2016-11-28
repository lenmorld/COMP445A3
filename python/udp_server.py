import argparse
import socket
import json
import pprint
import sys

import os
import time



from packet import Packet
import process_http_file
import SR_helper
import ReceiverWindowManager


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

PAYLOAD_MAX_SIZE = 1013      # bytes



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


def length_handshake(len_packets, peer_ip, peer_port, conn, sender):

    ############# send client number of packets in HTTP Response ####
    # sort of like a handshake just for length #
    # length will be sent in seq_num

    timeout = 15
    length_sent = False

    initial_seq_num = 200


    # while length_sent == False:

    try:

        msg = ""   # no payload in handshake
        p = Packet(packet_type=SYN_LENGTH,
                   seq_num=initial_seq_num,
                   peer_ip_addr=peer_ip,
                   peer_port=peer_port,
                   payload=msg.encode("utf-8"))

        # send SYN packet
        conn.sendto(p.to_bytes(), sender)

        # print("#### sending Length of HTTP Response: ", len_packets)
        
        # Try to receive a response within timeout
        conn.settimeout(timeout)


        print('Sending SYN_LENGTH with SEQ ', initial_seq_num)

        response, sender = conn.recvfrom(1024)
        length_handshake_packet = Packet.from_bytes(response)
        l_hs_payload = length_handshake_packet.payload.decode("utf-8")

        packet_type = length_handshake_packet.packet_type
        his_seq_num = length_handshake_packet.seq_num
        # get ack from payload

        print("LENGTH P PAYLOAD")
        print(l_hs_payload)
        # input()

        dict_payload = json.loads(l_hs_payload)
        his_ack = dict_payload['ack']

        # # wait for ACK_LENGTH
        # # print("### waiting to receive ACK_length from receiver ####")

        # response, sender = conn.recvfrom(1024)
        # al_packet = Packet.from_bytes(response)
        # al_packet_type = al_packet.packet_type


        print("PACKET TYPE: ", packet_type)

        if packet_type == SYN_ACK_LENGTH:
            # length_sent = True
            print("received SYN_ACK from server, ACK:", his_ack, " SEQ:", his_seq_num )

            # check if ack sent by server is my seq + 1
            if his_ack == (initial_seq_num + 1):

                # HANDSHAKE step 3, server sent SYN_ACK, send final ACK
                # add 1 to client's seq_num
                my_ack = his_seq_num + 1
                # generate my own seq_num
                my_seq_num = initial_seq_num + 1    # increment my seq num

                # create ACK packet, ack will be in payload since we dont have ACK in the Packet data structure
                my_dict_payload = {}
                my_dict_payload['ack'] = my_ack
                my_dict_payload['msg'] = ""
                my_dict_payload['num_packets'] = len_packets    # include num of packets expected
                msg = json.dumps(my_dict_payload)

                # create final ACK packet
                ack_p = Packet(packet_type=ACK_LENGTH,
                       seq_num=my_seq_num,
                       peer_ip_addr=peer_ip,
                       peer_port=peer_port,
                       payload=msg.encode("utf-8"))

                print("sending ACK_LENGTH: ", my_ack, " SEQ:", my_seq_num)

                conn.sendto(ack_p.to_bytes(), sender)
                print("ACK_LENGTH sent")
                conn.settimeout(timeout)

                ####### 3-way handshake good #########

                # print('Router: ', sender)
                # print('Packet: ', p)
                # print('Payload: ' + p.payload.decode("utf-8"))
                return True  

            else:
                # its someone else's SYN_ACK
                print("ACK_LENGTH # didnt match my initial SEQ num. Redo handshake")
                return False

        elif packet_type == NAK:
            print("NAK sent by server.Redo handshake")
            return False

    except:  # conn.timeout

        print('ACK_Length wasnt received after {}s'.format(timeout))
        print('Repeat handshake')
        # input()
        return False
    
    #################################################################


def process_http_request(conn, host, port, data, directory, sender, isVerb, num_packets):
    # need to decide on a fixed window size


    # while True:

    print("numpackets:", num_packets)

    packets_from_SR, sender = SR_helper.SR_Receiver(conn, num_packets)

    # pprint.pprint(packets_from_SR)
    http_request, peer_ip, peer_port = SR_helper.SR_to_appmessage(packets_from_SR)

    # assume at this point we have HTTP request
    print("===== HTTP request received ======")
    print(http_request)
    print("-> sending http response")

    # formulate response by invoking httpfs
    http_response  = process_http_file.process_Req(http_request, address, port, directory, isVerb)
    print(http_response)

    packets = SR_helper.prepare_SR(peer_ip, peer_port, http_response)


    ############# send client number of packets in HTTP Response ####
    while True:
        if length_handshake(len(packets), peer_ip, peer_port, conn, sender):
            print("ACK LENGTH Successfully sent to Client")
            break
        else:
            print('Length handshake failed. Repeat handshake')

    # since response length is communicated to client, start sending packets
    # transition to a sender and send HTTP response through SR
    print("==== SR sending http response ====")
    SR_helper.SR_Sender(sender[0], sender[1],  conn, packets)


    print("========= HTTP Response sent =========")


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


        while True:

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


            conn, data, sender, num_packets = three_way_handshake(conn)

            print("Handshake done")
            process_http_request(conn, host, port, data, directory, sender, isVerb, num_packets)
            print(" HTTP request | response round-trip done")
    finally:
        conn.close()

# process_http_request(conn, data, sender, his_seq_num, http_request)



def three_way_handshake(conn):

    three_way_handshake_good = False
    initial_seq_num = 500 
    # global three_way_handshake_good

    data = None
    sender = None

    num_packets = None

    timeout = 30

    syn_sent_time = 0
    syn_received = 0

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


            syn_elapsed_time = time.time() - syn_sent_time


            # check packet type
            if packet_type == SYN:

                

                syn_received += 1

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

                syn_sent_time = time.time()

                conn.settimeout(timeout)
                #### wait for final ACK for Handshake from Client

            # receives an ACK
            elif packet_type == ACK_HANDSHAKE:  

                # get ack from payload
                dict_payload = json.loads(his_payload)
                ack_good = False

                try:

                    his_ack = dict_payload['ack']
                    num_packets = dict_payload['num_packets']

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

                    conn.settimeout(timeout)

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
        # conn.timeout
        except Exception as e:
            print("Error: ", e)
        except:
            print("handshake timeout")

    return conn, data, sender, num_packets


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
