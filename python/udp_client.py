import argparse
import ipaddress
import socket
import json

from packet import Packet
import sys


# packet type #
# Data, ACK, SYN, SYN-ACK, NAK

"""
1. Implement 3-way handshake before sending anything

client  -> (SYN) SEQ=1                                            [SYN, SYN=1, ACK=0]
            (SYN-ACK) ACK=2, SEQ=100    <- server                 [SYN, SYN=1, ACK=1]
client  -> (ACK) ACK=101, SEQ=2                                 [NO SYN, SYN=0, ACK=1]


"""

# packet types
DATA = 0
SYN = 1
ACK = 2
SYN_ACK = 3
NAK = 5




def three_way_handshake(router_addr, router_port, server_addr, server_port, conn):
    peer_ip = ipaddress.ip_address(socket.gethostbyname(server_addr))

    # ---> just use conn from run_client, we won't create seperate conn for handshake
    # conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # timeout = 5    

    initial_seq_num = 100

    try:

        # HANDSHAKE step 1: create SYN packet
        # TODO: implement timeout for this

        msg = ""   # no payload in handshake
        p = Packet(packet_type=1,
                   seq_num=initial_seq_num,
                   peer_ip_addr=peer_ip,
                   peer_port=server_port,
                   payload=msg.encode("utf-8"))

        # send SYN packet
        conn.sendto(p.to_bytes(), (router_addr, router_port))
        # print('Send "{}" to router'.format(msg))

        # wait for SYN-ACK

        # Try to receive a response within timeout
        conn.settimeout(5)

        print('Sending SYN with SEQ ', initial_seq_num)
        print('Waiting for a response...')
        
        response, sender = conn.recvfrom(1024)
        handshake_packet = Packet.from_bytes(response)
        hs_payload = handshake_packet.payload.decode("utf-8")

        packet_type = handshake_packet.packet_type
        his_seq_num = handshake_packet.seq_num
        # get ack from payload
        dict_payload = json.loads(hs_payload)
        his_ack = dict_payload['ack']


        # check packet type
        if packet_type == SYN_ACK:   

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
                msg = json.dumps(my_dict_payload)

                # create final ACK packet
                ack_p = Packet(packet_type=ACK,
                       seq_num=my_seq_num,
                       peer_ip_addr=peer_ip,
                       peer_port=server_port,
                       payload=msg.encode("utf-8"))

                print("sending ACK: ", my_ack, " SEQ:", my_seq_num)

                conn.sendto(ack_p.to_bytes(), sender)
                print("ACK sent... We could also piggyback data here")
                conn.settimeout(5)

                ####### 3-way handshake good #########

                # print('Router: ', sender)
                # print('Packet: ', p)
                # print('Payload: ' + p.payload.decode("utf-8"))
                return True                

            else:
                # its someone else's SYN_ACK
                print("ACK # didnt match my initial SEQ num. Redo handshake")
                return False

        elif packet_type == NAK:
            print("NAK sent by server.Redo handshake")
            return False

    except socket.timeout:
        print('No response after {}s'.format(5))
        print('Repeat handshake')
        return False
    # finally:
    #     conn.close()


def run_client(router_addr, router_port, server_addr, server_port):
    peer_ip = ipaddress.ip_address(socket.gethostbyname(server_addr))
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    timeout = 5

    ### implement handshake before sending data ###
    while True:
        if three_way_handshake(router_addr, router_port, server_addr, server_port, conn):
            print("Cleint side: 3-way handshake successful"), conn
            print("Sending HTTP Request")
            break
        else:   # loop to do three_way_handshake again
            print("3-way handshake failed")


    try:     
        msg = "Put HTTP request here"
        p = Packet(packet_type=DATA,
                   seq_num=1,
                   peer_ip_addr=peer_ip,
                   peer_port=server_port,
                   payload=msg.encode("utf-8"))

        # sys.exit()

        conn.sendto(p.to_bytes(), (router_addr, router_port))
        print('Send "{}" to router'.format(msg))

        # Try to receive a response within timeout
        conn.settimeout(timeout)
        print('Waiting for a response')
        response, sender = conn.recvfrom(1024)
        p = Packet.from_bytes(response)
        print("===== HTTP Response ====")
        print('Router: ', sender)
        print('Packet: ', p)
        print('Payload: ' + p.payload.decode("utf-8"))

    except socket.timeout:
        print('No response after {}s'.format(timeout))
    finally:
        conn.close()


# Usage:
# python echoclient.py --routerhost localhost --routerport 3000 --serverhost localhost --serverport 8007

parser = argparse.ArgumentParser()
parser.add_argument("--routerhost", help="router host", default="localhost")
parser.add_argument("--routerport", help="router port", type=int, default=3000)

parser.add_argument("--serverhost", help="server host", default="localhost")
parser.add_argument("--serverport", help="server port", type=int, default=8007)
args = parser.parse_args()

run_client(args.routerhost, args.routerport, args.serverhost, args.serverport)
