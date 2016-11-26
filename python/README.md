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


if at any point ACK is not found in payload where it is expected
or SEQ/ACK is not the expected num,
the handshake must be restarted

either by letting it timeout, or sending a NAK


# testing GET and POST

run Router
for now without delay or lost

./router_x64



run Server to start in data directory, default would also work

python udp_server.py --port 8007 -d data

# GET

# display contents of dir
python udp_client.py --routerhost localhost --routerport 3000 --serverhost localhost --serverport 8007 get /

# display contents of file
python udp_client.py --routerhost localhost --routerport 3000 --serverhost localhost --serverport 8007 get /foo



# POST

 python udp_client.py --routerhost localhost --routerport 3000 --serverhost localhost --serverport 8007 post -h Content-Type:application/json -f foo /foo




### NOTES ####
when delay introduced, handshake is delayed but still worked
but HTTP didnt

./router_x64 --drop-rate 0 --max-delay 5s



BIG FILES


GETTING a big file

python udp_client.py --routerhost localhost --routerport 3000 --serverhost localhost get /bigfile -o bigfile_dload.txt --serverport 8001


POSTING a big file

python udp_client.py --routerhost localhost --routerport 3000 --serverhost localhost post -f file_10kb.txt /file10kb2.txt --serverport 8001