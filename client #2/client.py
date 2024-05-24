import os
import sys
import platform
import socket
import time
from datetime import datetime
import threading
import re

#Defines all needed methods and parameters for the client
class Client:
    def __init__(self, rfcList = None, clientSocket = None, uploadSocket = None):

        #contains all RFC .txt files that are in the same file directory as client.py
        self.rfcList = [] 
        tempRFC = os.listdir()

        #Retrieves all RFC text files in the same folder as client.py file
        for x in tempRFC:
            if ".txt" in x:
                self.rfcList.append(x)

        #prints list of RFCs avaliable at time opening client.py file
        print(self.rfcList)

        #Creates TCP socket for server client connection
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #Gets the name of the local machine
        host = socket.gethostname()

        #Setup for single machine use, if using server is on different machine change to correct address
        serverHost = input("Type in Server Address: ")
        print("\n")

        #Reserves well known port that server is listening on
        port = 7734

        #Connects client to server on well known port
        self.clientSocket.connect((serverHost, port))

        #Define a UDP socket for P2P
        self.uploadSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #Binds to an unused and random port
        self.uploadSocket.bind((host, 0))

    def get(self, cmd):

        #Split the passed command into chunks
        commandSegments = cmd.split()
        fileName = commandSegments[1]
        ip = commandSegments[2]
        port = commandSegments[3]

        socketInfo = ('' + ip, int(port))

        #For checks, make sure socket info is correct
        print(socketInfo)

        #Get Request to send to peer
        rfcNumber = ''.join(i for i in fileName if i.isdigit())

        #Get format for peer request
        requestLine1 = "GET RFC" + str(rfcNumber) + " P2P-CI/1.0\r\n"
        requestLine2 = "Host: " + ip + "\r\n"
        requestLine3 = "OS: " + platform.system() + " " + platform.release()

        request = requestLine1 + requestLine2 + requestLine3
        print(request + "\r\n")

        #Connect to peer socket given needed info
        peerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        peerSocket.connect(socketInfo)
        peerSocket.send(request.encode())

        (packetNumber, serverAddress) = peerSocket.recvfrom(65535)
        packetLenDecoded = packetNumber.decode()
        #print(packetLenDecoded)

        #Init a counter for packets
        packetsReceived = 0

        #Init the content to be put in file
        totalContent = ""

        #Gathers packets from peer and increments current packet count
        while packetsReceived < int(packetLenDecoded):
            (packet, serverAddress) = peerSocket.recvfrom(65535)
            totalContent = totalContent + (packet.decode()[150:])

            packetsReceived = packetsReceived + 1

        #If error occurs when gathering total content from file       
        if "404" in totalContent:
            print("404 Error: File Not Found")
        else:
            f = open(fileName, "w")
            f.write(totalContent)
            f.close()
        return


    def addToServerList(self,fileName):

        #Takes the RFC number from the input
        rfcNumber = ''.join(i for i in fileName if i.isdigit())

        #Add format request for server
        requestLine1 = "ADD RFC " + str(rfcNumber) + " P2P-CI/1.0\r\n" 
        requestLine2 = "Host: " + socket.gethostname() + "\r\n"
        requestLine3 = "Port: " + str(self.uploadSocket.getsockname()[1]) + "\r\n"
        requestLine4 = "Title: " + fileName + "\r\n\r\n"

        #Concats the request lines into one request
        request = requestLine1 + requestLine2 + requestLine3 + requestLine4
        print(request)
        
        self.clientSocket.send(request.encode())
        

    def lookup(self, fileName):

        #Takes the RFC number from the input
        rfcNumber = ''.join(i for i in fileName if i.isdigit())

        #Lookup format request for server
        requestLine1 = "LOOKUP RFC " + str(rfcNumber) + " P2P-CI/1.0\r\n" 
        requestLine2 = "Host: " + socket.gethostname() + "\r\n"
        requestLine3 = "Port: " + str(self.uploadSocket.getsockname()[1]) + "\r\n"
        requestLine4 = "Title: " + fileName + "\r\n\r\n"

        #Concats the request lines into one request
        request = requestLine1 + requestLine2 + requestLine3 + requestLine4
        print(request)
        
        self.clientSocket.send(request.encode())
        

    def list(self, fileName):

        #List format request for server
        requestLine1 = "LIST ALL P2P-CI/1.0\r\n" 
        requestLine2 = "Host: " + socket.gethostname() + "\r\n"
        requestLine3 = "Port: " + str(self.uploadSocket.getsockname()[1]) + "\r\n\r\n"

        #Concats the request lines into one request
        request = requestLine1 + requestLine2 + requestLine3
        print(request)
        #print(request.encode)
        self.clientSocket.send(request.encode())

        
    def end(self):

        #End format request for server
        requestLine1 = "END P2P-CI/1.0\r\n" 
        requestLine2 = "Host: " + socket.gethostname() + "\r\n"
        requestLine3 = "Port: " + str(self.uploadSocket.getsockname()[1]) + "\r\n\r\n"

        #Concats the request lines into one request
        request = requestLine1 + requestLine2 + requestLine3
        self.clientSocket.send(request.encode())
        self.clientSocket.close()
        

def listenToUploadPort(client, x):

        global hasStopped
        #thread = threading.current_thread()

        hasStopped = False

        #getattr(thread, "hasStopped", True)
        while not hasStopped:
            (request, addr) = client.uploadSocket.recvfrom(1024)
            request = request.decode()
            fileName = request.split()[1]+".txt"
            
            now = datetime.now()
            date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
            
            #Look for the file in directory
            files = os.listdir()
            isFileFound = False
            for name in files:
                if fileName == name:
                    isFileFound = True
            if isFileFound:      
                fileFound = open(fileName, 'r')
                data = fileFound.read()
                packets = getPackets(data, 2048)
                numberOfPackets = len(packets)

                #send the peer the number of packets to expect
                client.uploadSocket.sendto(str(numberOfPackets).encode(), addr)

                for i in packets:

                    #Get time and size of message
                    time = os.path.getmtime(fileName)
                    size = os.path.getsize(fileName)

                    #Formats message to send via upload socket
                    messageLine1 = "P2P-CI/1.0 200 OK\r\n"
                    messageLine2 = "Date: " + date_time + "\r\n"
                    messageLine3 = "OS: " +  platform.system() + " " + platform.release() + "\r\n"
                    messageLine4 = "Last-Modified: " + str(time) + "\r\n"
                    messageLine5 = "Content-Length: " + str(size) + "\r\n"
                    messageLine6 = "Content-Type: text/text\r\n" 
                    messageLine7 = "\r\n" + i
                    message = messageLine1 + messageLine2 + messageLine3 + messageLine4 + messageLine5 + messageLine6 + messageLine7

                    #Below line is meant for testing
                    #print(message)
                    client.uploadSocket.sendto(message.encode(), addr)
                return
            else:

                #Handles 404 error for if the file is not found
                messageError1 = "P2P-CI/1.0 404 NOT FOUND\r\n"
                messageError2 = "Date: " + date_time + "\r\n"
                messageError3 = "OS: " +  platform.system() + " " + platform.release() + "\r\n"
                messageError4 = "Last-Modified: N/A" + "\r\n"
                messageError5 = "Content-Length: N/A" +  "\r\n"
                messageError6 = "Content-Type: N/A\r\n"
                messageError = messageError1 + messageError2 + messageError3 + messageError4 + messageError5 + messageError6
                client.uploadSocket.sendto(messageError.encode(), addr)
                return


def getPackets(data, size):
    
    #divide up the packets using regex
    packets = re.compile(r'.{%s}|.+' % str(size),re.S)
    return packets.findall(data)

def printInfo():
    print("Valid Commands:\nADD <RFCfile>\nLOOKUP <RFCfile>\nLIST\nEND\nGET <RFCfile> <host name> <port number>\n")

def main():
    
    clientProcess = Client()

    #Thread is created for upload port listening
    thread = threading.Thread(target=listenToUploadPort, args=(clientProcess, 0))
    thread.daemon = True
    thread.start()
    
    try:
        while True:

            #Prints out command information for user
            printInfo()

            #Gets client input for commands
            userInput = input("$")
            if "ADD" in userInput:
                fileName = userInput.replace("ADD ", "")
                if fileName in clientProcess.rfcList:
                    clientProcess.addToServerList(fileName)
                    print(clientProcess.clientSocket.recv(1024).decode())
                else:
                    print("Invalid Command: RFC does not exist in directory\r\n")
            elif "LOOKUP" in userInput:
                fileName = userInput.replace("LOOKUP ", "")
                clientProcess.lookup(fileName)
                print(clientProcess.clientSocket.recv(1024).decode())
            elif "LIST" in userInput:
                clientProcess.list("LIST")
                print(clientProcess.clientSocket.recv(1024).decode())
            elif "GET" in userInput:
                clientProcess.get(userInput)
                print("File Written to Directory Successfully\n")
            elif "END" in userInput:
                clientProcess.end()
                clientProcess.clientSocket.close()
                print("clientProcess thread has stopped, exiting")
                sys.exit(0)
            else:
                print("P2P-CI/1.0 400 Bad Request\r\nPlease Enter a Valid Request\n")
            
    except KeyboardInterrupt:

        #Closes socket to server
        clientProcess.clientSocket.close()
        print("clientProcess thread has stopped, exiting")
        sys.exit(1)
    
    
    
main()
