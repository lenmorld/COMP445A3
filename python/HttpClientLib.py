"""
COMP445 - A1

HttpClientLib.py

HTTP Client Library
- includes methods used to make HTTP request, process responses, and follow redirections
"""

import socket                           # used to create HTTP socket
from urllib.parse import urlparse       # parse URL                               
import email                # used in parsing HTTP response headers
from io import StringIO     # used in conjunction with email
import pprint               # used in printing Python dictionary and list objects


socket.setdefaulttimeout = 5   # 5sec default timeout
CRLF = "\r\n\r\n"
CR = "\r\n"
custom_user_agent = 'COMP-445-HTTP/1.0'

# global variables used for collecting redirection data
redirect_data_global = ''
redirect_data_brief = ''
redirection_count = 0

"""
REDIRECT SPECIFICATION

Different 3xx redirection codes
# 301 Moved Permanently
# 302 Found (HTTP 1.1) / Moved Temporarily (HTTP 1.0)

Handle redirection by:
1. Get the status code sent at the first request that caused the redirect
2. Get information about the new location (temporary or permanent) and display it
3. Follow new location, collecting responses obtained for each redirection (useful in case of recursive redirects)
4. Verbose option
    - Display only redirect summary and final data with nonverbose
    - Display all response headers and data from each redirection with verbose
"""


"""
<redirect>
make request to new location, this is similar mechanism with PROCESS
after getting redirect data, make a call to <process_response> (possibly recursive)
"""
# make request to new location
def redirect(url, request_dict):
    global redirect_data_global, redirect_data_brief, redirection_count
    url = urlparse(url)
    ## testing ##
    # print("------ redirect ---------") 
    # print(">>Request URL properties:")
    # pprint.pprint(url)
    if len(url.netloc) > 0:
        host = url.netloc
    else:
        host = request_dict['host']
    port = request_dict['port']
    path = url.path
    command = request_dict['command']
    version = request_dict['version']
    if request_dict['query']:
        path = path + '?' + query
    if path == "":
        path = "/"
    params_headers_string = request_dict['params']

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((host, port))
    s.send(bytes("%s %s %s %s%s" %
                 (command, path,  version, params_headers_string, CRLF), "utf-8"))
    data = (s.recv(1000000))
    s.shutdown(1)
    s.close()
    # print(data.decode("utf-8"))
    redirection_count += 1
    redirect_data_global += ("\n<--Redirection# " +
                             str(redirection_count) + "-->\n" + data.decode("utf-8") + "\n")
    response = data.decode("utf-8")
    response_line, body = response.split('\r\n\r\n', 1)

    if body:    # just get body for nonverbose output
        redirect_data_brief += '\r\n' + body

    
    # process redirection again, if there is any
    process_response(data, request_dict)

"""
<process_response>
checks response header, if indicates redirection (i.e. 3xx code detected), calls <redirect> which could be recursive
if no more redirection (i.e. no 3xx code, or status code 200) returns to calling function
"""
def process_response(response, request_dict):
    # use global variables in this method
    global redirect_data_global, redirect_data_brief, redirection_count
    # decode response, using email library
    response = response.decode("utf-8")
    response_line, headers_alone = response.split('\r\n', 1)
    headers = email.message_from_file(StringIO(headers_alone))
    # create dictonary from headers e.g. {"Content-Type":"application/json"}
    response_dict = dict(headers.items())
    body_headers = response.split('\r\n')   # separate headers line-by-line
    # first one should be the redirect code #e.g 'HTTP/1.1 302 FOUND'
    code_str = body_headers[0]

    # check for any redirection codes
    if '301' in code_str or '302' in code_str:
        # ask user first to redirect if POST
        if request_dict['command'] == 'POST':
            x = input("Do you want to redirect this POST request? [Y|N]")
            if x.lower() != 'y':        # if user doesnt want to redirect, just return initial response
                return response, redirect_data_global, redirect_data_brief 

    if '301' in code_str:
        redirect_data_global  += '\r\n>>[Redir Location: ' + response_dict['Location'] + ']' + \
              ' [Status: ' + code_str + ']' + ' [Permanent redirection] ' + "\n>> Redirecting...\n"  
        redirect_data_brief  += '\r\n>>[Redir Location: ' + response_dict['Location'] + ']' + \
              ' [Status: ' + code_str + ']' + ' [Permanent redirection] ' + "\n>> Redirecting...\n"  

        # redirect to new location, passing original request info
        redirect(response_dict['Location'], request_dict)
    elif '302' in code_str:
        redirect_data_global  += '\r\n>>[Redir Location: ' + response_dict['Location'] + ']' + \
              ' [Status: ' + code_str + ']' + ' [Temporary redirection] ' + "\n>> Redirecting...\n"  

        redirect_data_brief  += '\r\n>>[Redir Location: ' + response_dict['Location'] + ']' + \
              ' [Status: ' + code_str + ']' + ' [Temporary redirection] ' + "\n>> Redirecting...\n"  
        
        # redirect to new location, passing original request info
        redirect(response_dict['Location'], request_dict)
    else:
        pass
    return response, redirect_data_global, redirect_data_brief 

"""
<PROCESS>
function that makes the HTTP request based on passed request parameters
other features:
- packages request information in a dictionary, which can be used
  in cases of redirection
- calls <process_response> to see if need to redirect
    execution returns here after (possibly multiple) redirects or none
- returns compiled response to calling function (httpc main)
    compiled response could include redirect data
    clear redirect global variables after compiling responses gathered 
"""
def PROCESS(command, url, headers, data, file, version, port=80):
    global redirect_data_global, redirection_count
    url = urlparse(url)
    ## testing ##
    # print("request URL properties:")
    # pprint.pprint(url)
    query = url.query    # eg. id=1&name=Lenny
    path = url.path
    protocol = 'http://'

    if path == "":
        path = "/"
    if len(query) > 0:    # append query to path if exists
        path = path + '?' + query


    # if localhost:8081, e.g. using a different port than 80
    if ":" in url.netloc:
        url_split = url.netloc.split(":")
        HOST = url_split[0]
        PORT = int(url_split[1])
    else:
        HOST = url.netloc         # The remote host
        PORT = int(port)          # The same port as used by the server


    # create a TCP socket - INET, STREAMing
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # call settimeout() before connect()
    # the system network stack may still return a timeout error of its own
    # regardless
    s.settimeout(5)   # 5 seconds
    # allow reusing of local sokcet without waiting for it to timeout
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # print(HOST)
    # print(PORT)
    s.connect((HOST, PORT))

    #print("Socket:" + HOST + ":" + str(PORT))

    # formulate request based on submitted paramaters
    json_data = False

    # if FILE option, get contents
    file_contents = ''
    if file:
            # read contents of the file
        with open(file, 'r') as file_read:
            for line in file_read:
                file_contents += line
        # print(file_contents)

    # other headers to add
    headers.append('Host: ' + HOST)
    headers.append('User-Agent: ' + custom_user_agent)
    headers.append('Accept: ' + "*/*")

    # add Content-Length header if it's POST
    if command == 'POST' and (data or file):
        if data:
            headers.append('Content-Length:' + str(len(data)))
        if file:
            headers.append('Content-Length:' + str(len(file_contents)))

    params_headers_string = ''
    if len(headers) > 0:
        params_headers_string += CR
        for h in headers:
            if 'json' in h:
                json_data = True
            if 'urlencoded' in h:
                file_data = True
            params_headers_string += (h + CR)

    # append data or file to the request
    if data:
        if len(data) > 0:
            params_headers_string += (CR + data)

    if file:
        params_headers_string += (CR + file_contents)


    ## testing ##
    # print("-------- Original Request--------")
    # print(("%s %s %s %s%s" % (command, path,  version, params_headers_string, CRLF), "utf-8"))
    
    # send request, encoding it in utf-8
    s.send(bytes("%s %s %s %s%s" %
                 (command, path,  version, params_headers_string, CRLF), "utf-8"))

    # save request object for possible redirection use
    request_dict = {}
    request_dict['host'] = HOST
    request_dict['command'] = command
    request_dict['path'] = path
    request_dict['version'] = version
    request_dict['params'] = params_headers_string
    request_dict['port'] = port
    request_dict['query'] = query

    # get response and convert to printable representation - string
    data = (s.recv(1000000))

    # print("orig data recv")
    # print(data)
    # x = input("PAUSE")

    # shutdown and close socket
    s.shutdown(1)
    s.close()

    # process response, see if any redirection codes
    data_response, redirect_data, redirect_data_nonverbose = process_response(data, request_dict)
    #redirect_data_global = ''    # reset global var
    #redirect_data_brief = ''

    # collect response and redirect data in a dictionary, then return it
    data_response_dict = {}
    data_response_dict['data_response'] = data_response

    if redirect_data:
        data_response_dict['redirect_data'] = redirect_data
        data_response_dict['redirect'] = True
        data_response_dict['redirect_data_nonverbose'] = redirect_data_nonverbose
    else:
        data_response_dict['redirect_data'] = None
        data_response_dict['redirect'] = False
        data_response_dict['redirect_data_nonverbose'] = None

    return data_response_dict