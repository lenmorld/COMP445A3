# Usage

1. Step 1: Run the router on the same or different host
   See the router's README

2. Step 2: Run the server
   python udp_server.py --port 8007

3. Step 3: Run the client
   python udp_client.py --routerhost localhost --routerport 3000 --serverhost localhost --serverport 8007



observe handshake that is initiated by client   

1. Implement 3-way handshake before sending anything

client  -> (SYN) SEQ=1                                            [SYN, SYN=1, ACK=0]
            (SYN-ACK) ACK=2, SEQ=100    <- server                 [SYN, SYN=1, ACK=1]
client  -> (ACK) ACK=101, SEQ=2                                 [NO SYN, SYN=0, ACK=1]
