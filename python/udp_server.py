import argparse
import socket

from packet import Packet

# packet types
DATA = 0
SYN = 1
ACK = 2
SYN_ACK = 3
NAK = -1

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


def handle_client(conn, data, sender):

    three_way_handshake = False

    try:
        p = Packet.from_bytes(data)

        packet_type = p.packet_type
        seq_num = p.seq_num
        peer_ip = p.peer_ip_addr
        peer_port = p.peer_port 


        # check packet type
        if packet_type == DATA:
            if three_way_handshake == False:
                print("3-way handshake not completed. Data packet refused")
            else:
                print("Data accepted")
        elif packet_type == SYN:
            # 2nd step of handshake : if SYN, this is step 1 of handshake, add 1 to client's seq_num
            my_ack = seq_num + 1
            # generate my own seq_num
            my_seq_num = 500

            # create SYN_ACK packet
            msg = ""
            syn_ack_p = Packet(packet_type=3,
                   seq_num=my_seq_num,
                   peer_ip_addr=peer_ip,
                   peer_port=peer_port,
                   payload=msg.encode("utf-8"))

            conn.sendto(syn_ack_p.to_bytes(), sender)



        print("Router: ", sender)
        print("Packet: ", p)
        print("Payload: ", p.payload.decode("utf-8"))
        print("Packet Type: ", packet_type)

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
