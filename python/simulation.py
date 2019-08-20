#Ce script contient la partie serveur TCP ainsi que les différents objets permettant l'émulation du fonctionnement du ModBus côté serveur
#Tous les objets sont des esclaves ModBus, ainsi ils sont capables de communiquer avec le client en fonction de l'interprétation des trames entrantes
#3 types de machines sont disponibles : la grue, le four et le convoyeur
#2 threads sont exécutés : l'un pour la mise à jour régulière de la simulation et l'autre pour la communication avec le client

import socket
import os, sys
import time, datetime
from threading import Thread
import math, random





#variables globales utilisées dans plusieurs threads
trame_recue_save, trame_retour_save = None, None





class ModbusDevice():#classe commune à toutes les machines, permet de gérer la partie ModBus

    def __init__(self, unit_id):
        self._unit_id = unit_id
        self._num_out_coils = [0 for i in range(10000)]
        self._num_in_contacts = [0 for i in range(10000)]
        self._analog_out_reg = [0 for i in range(10000)]
        self._analog_in_reg = [0 for i in range(10000)]

    def read_status(self, trame, tableau):
        trame_recue_address = int.from_bytes(trame[2:4], byteorder='big')
        number_reg = int.from_bytes(trame[4:6], byteorder='big')
        number_trame_recue_bytes = number_reg//8 + (number_reg%8 != 0)
        tmp = 0
        for i in range(number_reg):
            tmp += tableau[trame_recue_address+i] << i
        trame_recue_bytes = (tmp).to_bytes(number_trame_recue_bytes, byteorder='big')
        return trame[0:2] + bytes([number_trame_recue_bytes]) + trame_recue_bytes

    def read_register(self, trame, tableau):
        trame_recue_address = int.from_bytes(trame[2:4], byteorder='big')
        number_reg = int.from_bytes(trame[4:6], byteorder='big')
        number_trame_recue_bytes = number_reg*2
        tmp = []
        for i in range(number_reg):
            tmp.append(tableau[trame_recue_address+i] >> 8)
            tmp.append(tableau[trame_recue_address+i] & 0xFF)
        return trame[0:2] + bytes([number_trame_recue_bytes]) + bytes(tmp)

    def read_coil_status(self, trame):#fonction_code == 01
        return self.read_status(trame, self._num_out_coils)

    def read_input_status(self, trame):#fonction_code == 02
        return self.read_status(trame, self._num_in_contacts)

    def read_holding_register(self, trame):#fonction_code == 03
        return self.read_register(trame, self._analog_out_reg)

    def read_input_register(self, trame):#fonction_code == 04
        return self.read_register(trame, self._analog_in_reg)

    def force_single_coil(self, trame):#fonction_code == 05
        trame_recue_address = int.from_bytes(trame[2:4], byteorder='big')
        self._num_out_coils[trame_recue_address] = (trame[4] == 0xff)
        return trame

    def force_single_register(self, trame):#fonction_code == 06
        trame_recue_address = int.from_bytes(trame[2:4], byteorder='big')
        self._analog_out_reg[trame_recue_address] = int.from_bytes(trame[4:6], byteorder='big')
        return trame

    def force_multiple_coils(self, trame):#fonction_code == 15
        trame_recue_address = int.from_bytes(trame[2:4], byteorder='big')
        number_coils = int.from_bytes(trame[4:6], byteorder='big')
        number_trame_recue_bytes = trame[6]
        tmp = int.from_bytes(trame[7:7+number_trame_recue_bytes], byteorder='big')
        i = 0
        while tmp != 0:
            self._num_out_coils[trame_recue_address+i] = tmp & 1
            tmp >>= 1
            i += 1
        return trame[:6]

    def preset_multiple_registers(self, trame):#fonction_code == 16
        trame_recue_address = int.from_bytes(trame[2:4], byteorder='big')
        number_reg = int.from_bytes(trame[4:6], byteorder='big')
        number_trame_recue_bytes = trame[6]
        for i in range(number_trame_recue_bytes):
            self._analog_out_reg[trame_recue_address+i] = int.from_bytes(trame[7+2*i:9+2*i], byteorder='big')
        return trame[:6]

    def lire_trame(self, trame):
        unit_id = trame[0]
        if unit_id != self._unit_id: return
        function_code = trame[1]
        if function_code == 1: return self.read_coil_status(trame)
        elif function_code == 2: return self.read_input_status(trame)
        elif function_code == 3: return self.read_holding_register(trame)
        elif function_code == 4: return self.read_input_register(trame)
        elif function_code == 5: return self.force_single_coil(trame)
        elif function_code == 6: return self.force_single_register(trame)
        elif function_code == 15: return self.force_multiple_coils(trame)
        elif function_code == 16: return self.preset_multiple_registers(trame)
        else: return trame





class Grue(ModbusDevice):#la grue peut se déplacer suivant un axe et utilise une pince en position haute ou basse, ouverte ou fermée

    def __init__(self, unit_id):
        super().__init__(unit_id)
        #parametres physiques
        self.__unit_id = unit_id
        self.__position = 0
        self.__vitesse = 0
        self.__hauteur = True#grue en haut
        self.__etat_pince = False#pince ouverte
        #initialisation des valeurs des registres correspondantes
        self._analog_in_reg[0] = int(self.__position + 0x8000)
        self._analog_out_reg[0] = int(self.__vitesse + 0x8000)
        self._num_out_coils[0] = self.__hauteur
        self._num_out_coils[1] = self.__etat_pince

    def maj_etat(self, dt):
        self.__position += self.__vitesse * dt
        if self.__position > 500: self.__position = 500
        elif self.__position < -500: self.__position = -500
        self._analog_in_reg[0] = int(self.__position + 0x8000)
        self.__vitesse = self._analog_out_reg[0] - 0x8000
        self.__hauteur = self._num_out_coils[0]
        self.__etat_pince = self._num_out_coils[1]
        
    def lire_etat(self):
        print("__________________________________________________",
                "\nGrue\t\tID = ", self.__unit_id,
                "\nPosition de la grue\t", round(self.__position, 2),
                "\nVitesse de la grue\t", round(self.__vitesse, 2),
                "\nPosition haute\t\t", self.__hauteur,
                "\nPince fermée\t\t", self.__etat_pince)

class Four(ModbusDevice):##le four peut changer de température suivant la commande du thermostat

    def __init__(self, unit_id):
        super().__init__(unit_id)
        #parametres physiques
        self.__unit_id = unit_id
        self.__thermostat = 0
        self.__temperature_ref = self.__thermostat * 30
        self.__temperature = 20
        #initialisation des valeurs des registres correspondantes
        self._analog_out_reg[0] = int(self.__thermostat)
        self._analog_in_reg[0] = int(self.__temperature)

    def maj_etat(self, dt):
        self.__temperature_ref = self.__thermostat * 30
        if self.__temperature_ref > 20: dT = self.__temperature_ref - self.__temperature
        else: dT = 20 - self.__temperature
        self.__temperature += dt * 10 *  dT/abs(dT-5) * ((500 - self.__temperature)/500)**2
        self._analog_in_reg[0] = int(self.__temperature)
        self.__thermostat = self._analog_out_reg[0]

    def lire_etat(self):
        print("__________________________________________________",
                "\nFour\t\tID = ", self.__unit_id,
                "\nThermostat\t\t", self.__thermostat,
                "\nTempérature réf\t\t", round(self.__temperature_ref, 2),
                "\nTempérature\t\t", round(self.__temperature, 2))

class Convoyeur(ModbusDevice):#le convoyeur possède une vitess et deux capteurs de présence à l'entrée et à la sortie

    def __init__(self, unit_id):
        super().__init__(unit_id)
        #parametres physiques
        self.__unit_id = unit_id        
        self.__nxtcaisse = random.randint(0, 50)
        self.__position_caisses = []
        self.__position = 0
        self.__vitesse = 0
        self.__capteur1 = False
        self.__capteur2 = False
        #initialisation des valeurs des registres correspondantes
        self._analog_out_reg[0] = int(self.__vitesse + 0x8000)
        self._num_in_contacts[0] = self.__capteur1
        self._num_in_contacts[1] = self.__capteur2

    def maj_etat(self, dt):
        self.__position += self.__vitesse * dt
        for i in range(len(self.__position_caisses)): self.__position_caisses[i] += self.__vitesse * dt#mise a jour des caisses
        if self.__position > self.__nxtcaisse:#ajout de nouvelles caisses
            self.__position = 0
            self.__position_caisses.append(0)
            for i in range(len(self.__position_caisses)-1, 0, -1): self.__position_caisses[i] = self.__position_caisses[i-1]
            self.__position_caisses[0] = 0
            self.__nxtcaisse = random.randint(0, 50)
        while(self.__position_caisses and self.__position_caisses[-1] > 100):self.__position_caisses.pop(-1)#retrait des caisses existentes
        if self.__position_caisses and self.__position_caisses[0] < 5: self.__capteur1 = True
        else: self.__capteur1 = False
        if self.__position_caisses and self.__position_caisses[-1] > 95: self.__capteur2 = True
        else: self.__capteur2 = False
        self._num_in_contacts[0] = self.__capteur1
        self._num_in_contacts[1] = self.__capteur2
        self.__vitesse = self._analog_out_reg[0] - 0x8000

    def lire_etat(self):
        print("__________________________________________________",
                "\nConvoyeur\tID = ", self.__unit_id,
                "\nVitesse\t\t\t", round(self.__vitesse, 2),
                "\nPositions caisses\t", [int(i) for i in self.__position_caisses],
                "\nCapteur présence 1\t", self.__capteur1,
                "\nCapteur présence 2\t", self.__capteur2)





class MajSimulation(Thread):#thread servant à la mise à jour régulière et à l'affichage dans la console de l'état de la simulation

    def __init__(self, liste_machines, time_step, server_address):
        super().__init__()
        self.__liste_machines = liste_machines
        self.__time_step = time_step
        self.__server_address = server_address

    def run(self):
        global trame_recue_save, trame_retour_save
        date_depart = time.time()
        while True:
            os.system('clear')
            print(str(self.__server_address[0]) + ':' + str(self.__server_address[1]) + '\t\t' + str(datetime.timedelta(seconds=int(time.time() - date_depart))))
            for machine in liste_machines:
                machine.maj_etat(self.__time_step)
                machine.lire_etat()
            print("__________________________________________________")
            print("Dernière trame reçue :\t\t\t", trame_recue_save)
            print("Dernière(s) trame(s) renvoyée(s) :\t", trame_retour_save)
            print("__________________________________________________")
            print("En attente d'instruction ...")
            time.sleep(self.__time_step)





class Transmission(Thread):#thread servant à la partie communication TCP du réseau ModBus

    def __init__(self, server_address):
        super().__init__()
        self.__server_address = server_address

    def run(self):
        global trame_recue_save, trame_retour_save
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Démarrage du serveur TCP à l'adresse %s port %s" % self.__server_address)
        sock.bind(self.__server_address)
        sock.listen(1)
        while True:
            #attente de connection
            connection, client_address = sock.accept()
            connection.settimeout(.5)
            try:
                while True:
                    trame_recue = connection.recv(64)
                    if trame_recue:
                        trame_recue_save = trame_recue
                        liste_trame_retour = [machine.lire_trame(trame_recue) for machine in liste_machines]
                        trame_retour_save = []
                        for i in liste_trame_retour:
                            try:
                                connection.sendall(i)
                                trame_retour_save.append(i)
                            except: pass
                    else: break
            finally: connection.close()





#paramétrage et lancement de la simulation
liste_machines = [Grue(unit_id=1), Grue(unit_id=2), Four(unit_id=3), Convoyeur(unit_id=4)]
pas_simulation = .1#en secondes
server_address = ('localhost', 10002)

thread_1 = MajSimulation(liste_machines, pas_simulation, server_address)
thread_2 = Transmission(server_address)
thread_1.start()
thread_2.start()