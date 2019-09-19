#!/usr/bin/python
# -*- coding: UTF-8 -*-
from socket import *
from select import select
#import time
from sys import stdin,argv

PORT = 1664

PERSONAL_CODE = "696"

START = "START"
HELLO = "HELLO"
IPS = "IPS"
PM = "PM"
BM = "BM"

START_CODE = "1"+PERSONAL_CODE
HELLO_CODE = "2"+PERSONAL_CODE
IPS_CODE   = "3"+PERSONAL_CODE
PM_CODE    = "4"+PERSONAL_CODE
BM_CODE    = "5"+PERSONAL_CODE

BM_CMD = "bm"
PM_CMD = "pm"
BAN_CMD = "ban"
UNBAN_CMD = "unban"
QUIT_CMD = "quit"

dicoIpSock = {}
dicoPseudoIp = {}
anonymous = []
banList = []

#Envoi d'un paquet
def send(curS, code, cmd, content):
    #print "code : %s command : %s content : %s" % (code, cmd, content)
    curS.send("%s\001%s\043%s\r\n" % (code, cmd, content))

#Décapsulation d'un paquet
def decodeRecvd(msg):
    [code, content] = msg.split('\001')
    [command, message] = content.split('\043')
    message = message.split('\r')[0]
    #print "code : %s command : %s content : %s" % (code, command, message)
    return (code[1:], command, message)

#Ajout d'une nouvelle connexion
def newConnection():
    (c,addr) = s.accept()
    dicoIpSock[addr[0]] = c

#Suppression d'une connexion
def connectionRemoved(curS):
    dicoIpSock.pop(curS.getpeername()[0])
    for (psd, addr) in dicoPseudoIp.items():
        if addr == curS.getpeername()[0]:
            who = psd
            dicoPseudoIp.pop(psd)
            gdbye = "Goodbye %s !" % (who)
            print gdbye
            break

#Traitement de l'entrée utilisateur
def inputTreatment():
    data = stdin.readline().strip("\n")
    if data:
        cmd = ""
        for i in range(len(data)): #récupération de la commande
            if data[i] == " ":
                break
            cmd += data[i]
        received = data[len(cmd)+1:]

        if cmd == BM_CMD:
            sendBM(received)
        elif cmd == PM_CMD:
            dest = ""
            for i in range(len(received)): #récupération du pseudo du destinataire
                if received[i] == " ":
                    break
                dest+=received[i]
            message = received[len(dest)+1:] #récupération du message
            sendPM(dest, message)
        elif cmd == BAN_CMD:
            if received in dicoPseudoIp.keys(): #Si le pseudo existe
                ipToBan = dicoPseudoIp[received]
                if ipToBan not in banList: #Si le pseudo n'a pas été banni
                    banList.append(ipToBan)
                    print "Vous avez banni %s !" % (received)
                else:
                    print "%s a deja été banni." % (received)
            else:
                print "%s inexistant." % (received)
        elif cmd == UNBAN_CMD:
            if received in dicoPseudoIp.keys(): #Si le pseudo existe
                ipToUnban = dicoPseudoIp[received]
                if ipToUnban in banList: #Si le pseudo a pas été banni
                    banList.remove(ipToUnban)
                    print "%s a été débanni !" % (received)
                else:
                    print "%s n'a pas été banni." % (received)
            else:
                print "%s inexistant." % (received)
        elif cmd == QUIT_CMD:
            s.close()
            print "Vous avez quitté la conversation."
            quit()
        else:
            print "commande incorrecte. \n Veuillez utiliser une des commandes listées ci-dessous :"
            print "%s <message> : Envoi votre message à toutes les personnes connectées." % (BM_CMD)
            print "%s <pseudo> <message> : Envoie votre message à la personne avec le pseudo correspondant."  % (PM_CMD)
            print "%s <pseudo> : Banni l'utilisateur avec le pseudo correspondant. Vous ne pourrez plus interragir avec lui." % (BAN_CMD)
            print "%s <pseudo> : Débanni l'utilisateur avec le pseudo correspondant." % (UNBAN_CMD)
            print "%s : Ferme le chat." % (QUIT_CMD)

def sendStart(ipAddr): #Envoi d'un START à l'addresse IP ipAddr
    s2 = socket(AF_INET, SOCK_STREAM)
    try:
        s2.connect((ipAddr, PORT))
        dicoIpSock[ipAddr] = s2
        anonymous.append(ipAddr)
        send(s2, START_CODE, START, psd)
    except:
        print "Connexion à %s refusée.\n Vérifiez bien que l'adresse ip est correcte et qu'un chat est hébergé sur son port %s." % (ipAddr, PORT)

def sendHello(curS): #Envoi d'un HELLO à curS
    send(curS, HELLO_CODE, HELLO, psd)

def sendIPS(curS): #Envoi de la liste des addresses IP à curS
    if len(dicoIpSock.keys()) > 1: #Si le chat ne contient que deux utilisateurs (utilisateur courant et le nouvel utilisateur)
        msg = "("
        ips = dicoPseudoIp.values()
        ips.remove(curS.getpeername()[0])
        for i in range(len(ips)):
            addr = ips[i]
            msg+=addr
            if i != len(ips)-1:
                msg+=','
        msg+=")"
        send(curS, IPS_CODE, IPS, msg)

def sendBM(message): #Envoi d'un message en broadcast
    print "[%s] Vous : %s" % (PERSONAL_CODE, message)
    for st in dicoIpSock.values():
        if st.getpeername()[0] not in banList: #Si le destinataire n'a pas été banni
            send(st, BM_CODE, BM, message)

def sendPM(dest, message): #Envoi d'un message personnel au destinataire dest
    if dest in dicoPseudoIp.keys():
        if dicoPseudoIp[dest] not in banList: #Si le destinataire n'a pas été banni
            print "[%s] Vous pour %s : %s" % (PERSONAL_CODE, dest, message)
            curS = dicoIpSock[dicoPseudoIp[dest]]
            send(curS, PM_CODE, PM, message)
        else:
            print "%s a été banni. Brisez la malédiction pour pouvoir lui parler." % (dest)
    else:
        print "%s n'existe pas." % (dest)

def recvStart(curS, code, pseudo): #Réception d'un START
    dicoPseudoIp[pseudo] = curS.getpeername()[0]
    print "[%s] %s se joint a la conversation !" % (code, pseudo)
    sendHello(curS)
    sendIPS(curS)

def recvIPS(ips): #Réception d'un IPS
    ips = ips[1:-1] #Décapsulation de la liste des IPS
    ips = ips.split(",")
    for ip in ips:
        if ip != "" and ip not in dicoIpSock.keys(): #Si l'adresse IP ne fait pas déjà partie des connexions déjà réalisées
            s2 = socket(AF_INET, SOCK_STREAM)
            s2.connect((ip, PORT))
            dicoIpSock[ip] = s2
            anonymous.append(ip)
            sendHello(s2)

def recvHello(curS, code, pseudo): #Réception d"un HELLO
    ipAddr = curS.getpeername()[0]
    print "[%s] %s se joint a la conversation !" % (code, pseudo)
    dicoPseudoIp[pseudo] = ipAddr
    if ipAddr in anonymous: #Si un HELLO ou un START vers cette adresse a déjà été envoyé
        anonymous.remove(ipAddr)
    else:
        sendHello(dicoIpSock[ipAddr])

def recvBM(curS, code, received): #Réception d'un message broadcasté
    if curS.getpeername()[0] not in banList: #Si l'émetteur n'a pas été banni
        for (psd, ipAddr) in dicoPseudoIp.items():
            if ipAddr == curS.getpeername()[0]:
                print "[%s][public]  %s : %s" % (code, psd, received)
                break

def recvPM(curS, code, message): #Réception d'un message personnel
    if curS.getpeername()[0] not in banList: #Si l'émetteur n'a pas été banni
        for (psd, ipAddr) in dicoPseudoIp.items():
            if ipAddr == curS.getpeername()[0]:
                print "[%s][private] %s : %s" % (code, psd, received)
                break

psd = raw_input("Entrez votre pseudo  : ")
print ""
#Ouverture socket locale sur le port PORT
s = socket(AF_INET, SOCK_STREAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.bind(("0.0.0.0", PORT))
s.listen(3)

if len(argv) > 1:
    ip = argv[1]
    if len(ip.split('.')) == 4: #format IPv4 respecté
        sendStart(ip)
    else:
        print "Adresse ip incorrecte."
        s.close()
        quit()

while True:
    allSocks = [s, stdin]
    allSocks.extend(dicoIpSock.values())
    lin, lout,lex = select(allSocks, [],[])
    for t in lin:
        if t == stdin:
            #traitement des commandes entrées par l'utilisateur
            inputTreatment()
        elif t == s:
            #traitement des nouvelles connexions
            newConnection()
        else:
            #récéption d'un message
            data = t.recv(1024)
            if data:
                #si le message n'est pas vide
                (code, command, received) = decodeRecvd(data)
                if command == START:
                    recvStart(t, code, received)
                elif command == IPS:
                    recvIPS(received)
                elif command == HELLO:
                    recvHello(t, code, received)
                elif command == BM:
                    recvBM(t, code, received)
                elif command == PM:
                    recvPM(t, code, received)
            else:
                #si déconnexion
                connectionRemoved(t)
