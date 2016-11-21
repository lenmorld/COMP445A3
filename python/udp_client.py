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



def run_client(router_addr, router_port, server_addr, server_port, http_request):
    peer_ip = ipaddress.ip_address(socket.gethostbyname(server_addr))
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    timeout = 10

    ### implement handshake before sending data ###
    while True:
        if handshake.three_way_handshake(router_addr, router_port, server_addr, server_port, conn):
            print("Cleint side: 3-way handshake successful"), conn
            print("Sending HTTP Request")
            break
        else:  # loop to do three_way_handshake again
            print("3-way handshake failed")

    try:     
        # msg = "Put HTTP request here"


        packets = SR_helper.prepare_SR(peer_ip, server_port, http_request)
        print("packet length ", len(packets))


        # TODO: break payload_data into Packets[] array and send
        # using Selective Repeat
        # instead of sending all at once


        ################### PUT SR_Sender call here #################
        # SR_Sender(packets)
        
        p = packets[0]
        #conn.sendto(p.to_bytes(), (router_addr, router_port))
        print('Send "{}" to router'.format(p))
        
        ###############################################################

        windowManager =SenderWindowManager.SenderWindowManager(len(packets))
        indexReceived=0
        indexSent=0;
        index=0
        while(indexReceived <len(packets)):            
            while (windowManager.needMorePacket() and indexSent<len(packets)):
                p = packets[indexSent]
                print('Send "{}" to router'.format(p))
                windowManager.pushPacket(p)
                conn.sendto(p.to_bytes(),(router_addr,router_port))
                print ("send packet number",indexSent)
                indexSent = indexSent+1
            #handle receivec packets here
            
            windowManager.receiveAck(indexReceived)
            indexReceived = indexReceived+1
            print("index received",indexReceived)
            windowManager.moveWindow()
            #hanlde socket timeout
            resendList = windowManager.resendPacket()
            for p in resendList:
                conn.sendto(p.to_bytes(),(router_addr,router_port))
                print('Send "{}" to router'.format(p))
            if windowManager.isBuffering():
                pass
            else:
                break
        
        
        ###### WAIT TO RECEIVE HTTP RESPONSE #####
        # print('Waiting for a response')

        # Try to receive a response within timeout
        conn.settimeout(timeout)

        # TODO: transition into SR_receiver and
        # instead of receiving a HTTP request packet directly from conn
        # receive Packets[] array (already converted or to convert) to an HTTP request)
        # from SR algorithm


        ################### PUT SR_Receiver call here #################
        # packets_from_SR = SR_Receiver()
        packets_from_SR = []
        ###############################################################


        # for now, assume we are only getting one packet and we can decode it right away
        response, sender = conn.recvfrom(1024)
        
        # do this for all received packets from SR
        p = Packet.from_bytes(response)
        packets_from_SR.append(p)

        http_response_final, peer_ip, server_port = SR_helper.SR_to_appmessage(packets_from_SR)

        print("===== HTTP Response ====")
        print('Router: ', sender)
        print(http_response_final)

    except socket.timeout:
        print('No response after {}s'.format(timeout))
    finally:
        conn.close()


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
