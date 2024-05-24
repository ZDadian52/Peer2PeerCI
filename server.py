import os
import sys
import socket
import threading

#Contains needed info for server
class Server:
    def __init__(self, rfcList = None, peerList = None, serverSocket = None, port = None):

        #Holds all RFCs that were added by clients
        self.rfcList = []

        #Holds all connected clients
        self.peerList = []

        #Server address, change to actual address if on a different machine from clients
        serverHost = '127.0.0.1'
        
        #Well known port for server
        self.port = 7734

        #Creates socket for server
        self.serverSocket = socket.socket()

        #Binds server to well known port 7734
        self.serverSocket.bind((serverHost, self.port))

    #Handles all server/client messaging setup
    def connectToNewClient(self, clientSocket, addr):
        while True:
            message = clientSocket.recv(1024).decode()
            print("Connection recv: " +  str(addr)) #confirm connection

            #Splits original message
            splitMessage = message.split()

            #if this is a new client/they are doing something other than ending the connection then add it to the list of peers
            if not "END" in message:
                for i in range(len(splitMessage)-1):
                    if "Port:" in splitMessage[i]:
                        
                        #check peerList for entry
                        hostPort = splitMessage[i+1]
                for i in range(len(splitMessage)-1):
                    if "Host:" in splitMessage[i]:
                        hostName = splitMessage[i+1]
                self.peerList.append((hostName, hostPort))

            #Start of client request handling
            if "ADD" in message:
                entry = []

                #Add message format to client
                messageOK = "P2P-CI/1.0 200 OK\r\n\r\n"
                
                entry.append(int(splitMessage[2]))
                
                # Allows multiple same name entries
                for i in range(len(splitMessage)-1):
                    if "Title" in str(splitMessage[i]):
                        title = splitMessage[i+1]
                        entry.append(title)

                for i in range(len(splitMessage)-1):
                    if "Host" in str(splitMessage[i]):
                        serverHost = splitMessage[i+1]
                        entry.append(serverHost)
                
                for i in range(len(splitMessage)-1):
                    if "Port:" in splitMessage[i]:
                        
                        #check list for client and adds if they do not exist
                        hostPort = splitMessage[i+1]
                        entry.append(hostPort)
                messageOK = messageOK + splitMessage[1] + " " + title + " " + serverHost + " " + hostPort + "\r\n\r\n"

                #Sends ok to client for succesful add request
                clientSocket.send(messageOK.encode())
                self.rfcList.append(entry)
            elif "LOOKUP" in message:

                #Lookup message format to client
                messageLookup = "P2P-CI/1.0 "
                for i in self.rfcList:
                    if int(message.split()[2]) == int(i[0]):
                        messageLookup = messageLookup + "200 OK\r\n\r\n"
                        messageLookup = messageLookup + str(i[0]) + " " + i[1] + " " + i[2] + " " + str(i[3]) + " " + socket.gethostbyname(i[2])+ "\r\n"
                        messageLookup = messageLookup + "\r\n"
                        clientSocket.send(messageLookup.encode())
                        return

                #If client file for lookup is not found
                messageLookupError = messageLookup + "404 Not Found\r\n\r\n"
                messageLookupError = messageLookupError + "N/A " + "N/A " + "N/A " + "N/A\r\n"
                messageLookupError = messageLookupError + "\r\n"
                clientSocket.send(messageLookupError.encode())
            elif "LIST" in message:

                #List message format to client
                messageList = "P2P-CI/1.0 200 OK\r\n\r\n"
                for i in self.rfcList:
                    #print(socket.gethostbyname(i[2]))
                    messageList = messageList + str(i[0]) + " " + i[1] + " " + i[2] + " " + str(i[3]) + " " + socket.gethostbyname(i[2]) + "\r\n"
                messageList = messageList + "\r\n"
                clientSocket.send(messageList.encode())
            elif "END" in message:

                #Begins to end client connection
                print("Attempting to end client connection")

                #Make new peer/rfc list without client that is ending connection
                newPeerList = []
                newRFCList = []
                for i in range(len(splitMessage)-1):
                    if "Port:" in splitMessage[i]:
                        
                        #check peer list
                        hostPort = splitMessage[i+1]
                        
                #clean peerList of entry
                for i in self.peerList:
                    if not hostPort in i:
                        newPeerList.append(i)
                        
                #clean rfcList of entry
                for i in self.rfcList:
                    if not hostPort in i:
                        newRFCList.append(i)
                self.rfcList = newRFCList
                self.peerList = newPeerList
                clientSocket.close()
                print("Client connection ended successfully")
                sys.exit()
            
        clientSocket.close()


#Handles main functionality
def main():

    #Create server obj
    server = Server()
    try:
        server.serverSocket.listen(5) 
        while True:
            
            #Client connection accepted
            (client, addr) = server.serverSocket.accept()

            #Create a thread for client connection
            thread = threading.Thread(target=server.connectToNewClient, args=(client, addr))
            thread.start()
            
            
    except KeyboardInterrupt:
        server.serverSocket.close()
        sys.exit(1)
    
main()
