import argparse
import ipaddress
import socket
import json
import pprint

from packet import Packet
import sys

import httpc
import handshake
import SR_helper
import SenderWindowManager

# packet types
DATA = 0
SYN = 1
ACK = 2
SYN_ACK = 3
NAK = 5
FINAL_ACK = 6
FINAL_ACK_B = 7
SYN_LENGTH = 8
SYN_ACK_LENGTH = 9
ACK_LENGTH = 10


def length_handshake(conn):


    length_handshake_good = False
    initial_seq_num = 1200

    ############# recieve number of packets in HTTP Response ####
    # sort of like a handshake just for length #
    # length will be sent in seq_num

    length_http_response = None
    timeout = 10

    # print("### waiting to receive length of HTTP response ####")

    while length_handshake_good != True:

        response, sender = conn.recvfrom(1024)

        try:
            p = Packet.from_bytes(response)
            packet_type = p.packet_type
            his_seq_num = p.seq_num
            peer_ip = p.peer_ip_addr
            peer_port = p.peer_port 
            his_payload = p.payload.decode("utf-8")
            

            if packet_type == SYN_LENGTH:
                # length_http_response = l_packet.seq_num

                # print("#### Length of HTTP Response: ####", length_http_response)
                # length_handshake_good = True

                print("received SYN_LENGTH with SEQ: ", his_seq_num)

                # 2nd step of handshake : if SYN, this is step 1 of handshake, add 1 to client's seq_num
                my_ack = his_seq_num + 1


                # HANDSHAKE step 2
                # create SYN_ACK packet, ack will be in payload since we dont have ACK in the Packet data structure
                my_dict_payload = {}
                my_dict_payload['ack'] = my_ack
                my_dict_payload['msg'] = ""
                msg = json.dumps(my_dict_payload)

                syn_ack_p = Packet(packet_type=SYN_ACK_LENGTH,
                       seq_num=initial_seq_num,
                       peer_ip_addr=peer_ip,
                       peer_port=peer_port,
                       payload=msg.encode("utf-8"))

                print("Sending SYN_ACK_LENGTH with SEQ: ", initial_seq_num, " ACK: ", my_ack)

                conn.sendto(syn_ack_p.to_bytes(), sender)

                conn.settimeout(timeout)
                #### wait for final ACK for Handshake from Client


            # receives an ACK
            elif packet_type == ACK_LENGTH:  
                # get ack from payload
                dict_payload = json.loads(his_payload)
                ack_good = False

                try:

                    his_ack = dict_payload['ack']
                    length_http_response = dict_payload['num_packets']

                    print("received final length handshake ACK: ", his_ack, " SEQ: ", his_seq_num)

                    # check if ack sent by client is my seq + 1
                    if his_ack == (initial_seq_num + 1):
                        length_handshake_good = True
                        ack_good = True
                        print("Server side: 3 way handshake completed. Waiting for HTTP request...")

                    else:
                        print("Wrong ACK_LENGTH number received")
                        # wrong ACK number recieved, send NAK

                except KeyError:
                    print("ACK_LENGTH not found in packet")

                
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

            # packet type is something else
            else:
                if length_handshake_good:
                    break
                else:
                    print("3-way handshake not completed yet. Data packet refused")
                

                # # send ACK for length
                # msg= ""
                # ack_l = Packet(packet_type=ACK_LENGTH,
                #        seq_num=0,
                #        peer_ip_addr=peer_ip,
                #        peer_port=server_port,
                #        payload=msg.encode("utf-8"))

                # print("sending length ACK: ")

                # conn.sendto(ack_l.to_bytes(), sender)
                # conn.settimeout(timeout)

        except conn.timeout:
            print("LENGTH handshake timedout")
        except Exception as e:
            print("Error: ", e)

    return length_http_response
    #################################################################


def run_client(router_addr, router_port, server_addr, server_port, http_request):
    peer_ip = ipaddress.ip_address(socket.gethostbyname(server_addr))
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # timeout = 10


    packets = SR_helper.prepare_SR(peer_ip, server_port, http_request)
    num_packets = len(packets)
    # print("packet length ", num_packets)

    ### implement handshake before sending data ###
    while True:
        if handshake.three_way_handshake(router_addr, router_port, server_addr, server_port, conn, num_packets):
            print("Client side: 3-way handshake successful"), conn
            print("Sending HTTP Request")
            break
        else:  # loop to do three_way_handshake again
            print("3-way handshake failed")

    print("=== Client sending HTTP Request ===")
    SR_helper.SR_Sender(router_addr, router_port,  conn, packets)
    
    
    ###### WAIT TO RECEIVE HTTP RESPONSE #####
    print('===== Waiting for HTTP response =====')

    ############# recieve number of packets in HTTP Response ####
    length_http_response = length_handshake(conn)

    # length_http_response = length_handshake(conn, peer_ip, server_port)

    ################### PUT SR_Receiver call here #################
    print("SR receiving response")

    # packets_from_SR, sender = SR_helper.SR_Receiver(conn, num_packets)
    packets_from_SR, sender = SR_helper.SR_Receiver(conn, length_http_response)

    ###############################################################

    # packets_from_SR = []
    # # for now, assume we are only getting one packet and we can decode it right away
    # response, sender = conn.recvfrom(1024)
    
    # # do this for all received packets from SR
    # p = Packet.from_bytes(response)
    # packets_from_SR.append(p)

    http_response_final, peer_ip, server_port = SR_helper.SR_to_appmessage(packets_from_SR)

    print("===== HTTP Response ====")
    print('Router: ', sender)
    print(http_response_final)
        

    # except socket.timeout:
    #     print('No response after {}s'.format(timeout))
    # finally:
    #     conn.close()


# Usage:
# python echoclient.py --routerhost localhost --routerport 3000 --serverhost localhost --serverport 8007

parser = argparse.ArgumentParser()

# HTTPC STUFF
# POSITIONAL arguments
parser = argparse.ArgumentParser(description='httpc', add_help=False)
parser.add_argument("command", help="(get|post|help)") 
# this would be get|post if commad=help, or URL if command=get|post
parser.add_argument("command_args", nargs='*', type=str)

# OPTIONAL arguments
parser.add_argument("-v", "--verbose", help="verbose output",
                    action="store_true")
parser.add_argument("-h", "--headers", default=[], action='append')  # append allows -h a:b -h c:d
parser.add_argument("-o", "--output", default=[], type=str)  

# add mutually exclusive group -h | -f
group = parser.add_mutually_exclusive_group() 
group.add_argument('-d', '--data', default='', type=str)  # string data
group.add_argument("-f", "--file", default='', type=str)  # string data

# UDP CLIENT STUFF
parser.add_argument("--routerhost", help="router host", default="localhost")
parser.add_argument("--routerport", help="router port", type=int, default=3000)

parser.add_argument("--serverhost", help="server host", default="localhost")
parser.add_argument("--serverport", help="server port", type=int, default=8007)

# args = parser.parse_args()

args, extra_params = parser.parse_known_args()

command, URL, headers, data, file = httpc.decode_args(args, extra_params)

print("=== HTTP request parameters ===")
print (command, URL, headers, data, file)
print("===============================")

http_request = httpc.construct_http_request(command, URL, headers, data, file)

print("=== HTTP request ===")
print(http_request)
print("================================")

run_client(args.routerhost, args.routerport, args.serverhost, args.serverport, http_request)
