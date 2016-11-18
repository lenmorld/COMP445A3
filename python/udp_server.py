import argparse
import socket
import json
import pprint

from packet import Packet

# packet types
DATA = 0
SYN = 1
ACK = 2
SYN_ACK = 3
NAK = -1


three_way_handshake_good = False

"""
1. Implement 3-way handshake before sending anything

client  -> (SYN) SEQ=1                                            [SYN, SYN=1, ACK=0]
            (SYN-ACK) ACK=2, SEQ=100    <- server                 [SYN, SYN=1, ACK=1]
client  -> (ACK) ACK=101, SEQ=2                                 [NO SYN, SYN=0, ACK=1]

for now, it is assumed that for every client request, a handshake
needs to be established, since we are using HTTP 1.0 (non-persistent)

after successfull handshake, data is then sent by client and should be accepted by server

"""


def run_server(port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        conn.bind(('', port))
        print('Echo server is listening at', port)
        while True:
            data, sender = conn.recvfrom(1024)
            handle_client(conn, data, sender)

    finally:
        conn.close()



def start_http(conn, data, sender, p):

    try:
        p = Packet.from_bytes(data)

        packet_type = p.packet_type
        his_seq_num = p.seq_num
        peer_ip = p.peer_ip_addr
        peer_port = p.peer_port 
        his_payload = p.payload.decode("utf-8")    # this is the HTTP request

    except Exception as e:
        print("Error: ", e)

    msg = "HTTP Response, last client seq_num: " + str(his_seq_num)
    syn_ack_p = Packet(packet_type=0,
           seq_num=his_seq_num,
           peer_ip_addr=peer_ip,
           peer_port=peer_port,
           payload=msg.encode("utf-8"))

    conn.sendto(syn_ack_p.to_bytes(), sender)


def handle_client(conn, data, sender):

    global three_way_handshake_good

    
    # generate my own seq_num
    initial_seq_num = 500    

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

            syn_ack_p = Packet(packet_type=3,
                   seq_num=initial_seq_num,
                   peer_ip_addr=peer_ip,
                   peer_port=peer_port,
                   payload=msg.encode("utf-8"))

            print("Sending SYN_ACK with SEQ: ", initial_seq_num, " ACK: ", my_ack)

            conn.sendto(syn_ack_p.to_bytes(), sender)

            #### wait for final ACK for Handshake from Client

        # receives an ACK
        elif packet_type == ACK:  
            # get ack from payload
            dict_payload = json.loads(his_payload)

            try:

                his_ack = dict_payload['ack']
                print("received final handshake ACK: ", his_ack, " SEQ: ", his_seq_num)

                # check if ack sent by client is my seq + 1
                if his_ack == (initial_seq_num + 1):
                    three_way_handshake_good = True
                    print("Server side: 3 way handshake completed. Waiting for HTTP request...")

                else:
                    print("Wrong ACK number received")
                    # wrong ACK number recieved, send NAK

            except KeyError:
                print("ACK not found in packet")

                # keep waiting for correct ACK for handshake            

        elif packet_type == DATA:
            if three_way_handshake_good:
                print("===== HTTP request ======")
                print("Router: ", sender)
                print("Packet: ", p)
                print("Payload: ", p.payload.decode("utf-8"))
                print("Packet Type: ", packet_type)

                start_http(conn, data, sender, his_seq_num)

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


# Usage python udp_server.py [--port port-number]
parser = argparse.ArgumentParser()
parser.add_argument("--port", help="echo server port", type=int, default=8007)
args = parser.parse_args()
run_server(args.port)
