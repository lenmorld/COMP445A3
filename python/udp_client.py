import argparse
import ipaddress
import socket

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
NAK = -1




def three_way_handshake(router_addr, router_port, server_addr, server_port):
    peer_ip = ipaddress.ip_address(socket.gethostbyname(server_addr))
    
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    timeout = 5    


    my_seq_num = 100

    try:
        msg = ""   # no payload in handshake
        p = Packet(packet_type=1,
                   seq_num=my_seq_num,
                   peer_ip_addr=peer_ip,
                   peer_port=server_port,
                   payload=msg.encode("utf-8"))

        # 1st step of handshake : send SYN
        conn.sendto(p.to_bytes(), (router_addr, router_port))
        print('Send "{}" to router'.format(msg))

        # wait for SYN-ACK
        # Try to receive a response within timeout
        conn.settimeout(timeout)
        print('SYN with SEQ ', my_seq_num, ' sent ')
        print('Waiting for a response...')
        
        response, sender = conn.recvfrom(1024)
        handshake_packet = Packet.from_bytes(response)

        packet_type = handshake_packet.packet_type
        seq_num = handshake_packet.seq_num

        # check packet type
        if packet_type == SYN_ACK:   # 3rd step of handshake: server sent SYN_ACK, send final ACK
            # if SYN, this is step 1 of handshake, add 1 to client's seq_num
            my_ack = seq_num + 1
            # generate my own seq_num
            my_seq_num = my_seq_num + 1    # increment my seq num

            # create final ACK packet
            msg = ""
            ack_p = Packet(packet_type=2,
                   seq_num=my_seq_num,
                   peer_ip_addr=peer_ip,
                   peer_port=server_port,
                   payload=msg.encode("utf-8"))

            conn.sendto(ack_p.to_bytes(), sender)
            print("ACK sent... We could also piggyback data here")

        elif packet_type == NAK:
            print("NAK sent by server. CRASH AND BURN!!!")

        print('Router: ', sender)
        print('Packet: ', p)
        print('Payload: ' + p.payload.decode("utf-8"))
        return True

    except socket.timeout:
        print('No response after {}s'.format(timeout))
        print('Repeat handshake')
        return False
    finally:
        conn.close()


def run_client(router_addr, router_port, server_addr, server_port):
    peer_ip = ipaddress.ip_address(socket.gethostbyname(server_addr))
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    timeout = 5
    try:
        msg = "Hello World 123"
        p = Packet(packet_type=0,
                   seq_num=1,
                   peer_ip_addr=peer_ip,
                   peer_port=server_port,
                   payload=msg.encode("utf-8"))


        ### implement handshake before sending data ###
        if three_way_handshake(router_addr, router_port, server_addr, server_port):
            print("3-way handshake successfull")
        else:
            print("3-way handshake failed")
            sys.exit()


        sys.exit()



        conn.sendto(p.to_bytes(), (router_addr, router_port))
        print('Send "{}" to router'.format(msg))

        # Try to receive a response within timeout
        conn.settimeout(timeout)
        print('Waiting for a response')
        response, sender = conn.recvfrom(1024)
        p = Packet.from_bytes(response)
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
