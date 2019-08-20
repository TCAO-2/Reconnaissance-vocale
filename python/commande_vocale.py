from commun import *
from reconnaissance_vocale import *
import socket
import sys
#from threading import Thread





function_code_modbus = [
[None, 	None, 	None 	],
['r', 	'out', 	'num' 	],
['r', 	'in', 	'num' 	],
['r', 	'out',	'analog'],
['r', 	'in', 	'analog'],
['w', 	'out', 	'num'	],
['w', 	'out', 	'analog']
]

str_chiffre = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']





def str_to_trame(commande_str):
	if len(commande_str) > 3: return -1#trop de mots
	unit_id = str_chiffre.index(commande_str[0])
	commande = commande_str[1]
	try: argument = commande_str[2]
	except: argument = None
	if unit_id_array[unit_id] == None: return -2#unit_id inconnu
	if commande not in [i[0] for i in unit_id_array[unit_id]]: return -3#commande inconnue
	tmp = [i for i in unit_id_array[unit_id] if i[0] == commande and (argument and i[1] in ['arg', argument] or not argument and not i[1])]
	if len(tmp): instruction = tmp[0]
	else: return -4#argument inconnu
	function_code = function_code_modbus.index(instruction[2:5])
	data_address = int(instruction[5])
	if function_code in [1, 2, 3, 4]:
		trame = bytes([unit_id, function_code]) + data_address.to_bytes(2, byteorder='big') + b'\x00\x01'
	elif function_code == 5:
		trame = bytes([unit_id, 5]) + data_address.to_bytes(2, byteorder='big')
		if instruction[6] == 1: trame += b'\xff\x00'
		else: trame += b'\x00\x00'
	else:#function_code == 6
		if argument:
			trame = bytes([unit_id, 6]) + data_address.to_bytes(2, byteorder='big') + (str_chiffre.index(argument)*instruction[6] + instruction[7]).to_bytes(2, byteorder='big')
		else:
			trame = bytes([unit_id, 6]) + data_address.to_bytes(2, byteorder='big') + (instruction[6] + instruction[7]).to_bytes(2, byteorder='big')
	return trame

def trame_to_msg(trame_envoi, trame_recue):
	if trame_recue[1] in [1, 2, 3, 4]:
		trame_envoi_address = int.from_bytes(trame_envoi[2:4], byteorder='big')
		number_reg = int.from_bytes(trame_envoi[4:6], byteorder='big')
		number_trame_recue_bytes = trame_recue[2]
		tmp = int.from_bytes(trame_recue[3:3+number_trame_recue_bytes], byteorder='big')
		if trame_recue[1] < 3:
			for i in range(number_reg):
				print("Adresse : {}\tValeur : {}".format(hex(trame_envoi_address+i), tmp & 1))
				tmp >>= 1
		else:
			for i in range(number_reg):
				print("Adresse : {}\tValeur : {}".format(hex(trame_envoi_address+i), hex(tmp & 0xFFFF)))
				tmp >>= 16
	elif trame_recue[1] in [5, 6, 15, 16]:
		if trame_recue[:6] == trame_envoi[:6]: print("Ecriture ok")
		else: print("Ecriture pas ok")
	else: print("Erreur")






#commande	argument	->		READ/WRITE 	IN/OUT 		NUM/ANALOG 		Adress 		value 		offset
parametres_grue = [
['left', 	'arg', 				'w', 		'out', 		'analog', 		0, 			-1,			0x8000	],
['right',	'arg',				'w',		'out',		'analog',		0,			1,			0x8000	],
['up',		None,				'w',		'out',		'num',			0,			1,			0		],
['down',	None,				'w',		'out',		'num',			0,			0,			0		],
['on',		None,				'w',		'out',		'num',			1,			1,			0		],
['off',		None,				'w',		'out',		'num',			1,			0,			0		],
['yes',		'one',				'r',		'in',		'analog',		0,			1,			-0x8000	],
['yes',		'two',				'r',		'out',		'analog',		0,			1,			-0x8000	],
['yes',		'tree',				'r',		'out',		'num',			0,			1,			0		],
['yes',		'four',				'r',		'out',		'num',			1,			1,			0		],
['stop',	None,				'w',		'out',		'analog',		0,			0,			0x8000	]
]

parametres_four = [
['no',	 	'arg', 				'w', 		'out', 		'analog', 		0, 			1,			0	],
['yes',  	None, 				'r', 		'in', 		'analog', 		0, 			1,			0	],
['stop',	None,				'w',		'out',		'analog',		0,			0,			0	]
]

parametres_convoyeur = [
['no',  	'arg', 				'w', 		'out', 		'analog', 		0, 			1,			0x8000	],
['yes',  	'one', 				'r', 		'in', 		'num', 			0, 			1,			0		],
['yes',  	'two', 				'r', 		'in', 		'num', 			1, 			1,			0		],
['stop',	None,				'w',		'out',		'analog',		0,			0,			0		]
]

unit_id_array = [None for i in range(248)]
unit_id_array[1] = parametres_grue
unit_id_array[2] = parametres_grue
unit_id_array[3] = parametres_four
unit_id_array[4] = parametres_convoyeur










DATA, intensite = lecture_audio()
prediction_brute = prediction(DATA)
prediction_brute = [mult_terme_a_terme(i, i) for i in prediction_brute]
filtre_intensite = [intensite[i + fenetre_mot//2] for i in range(len(DATA) - fenetre_mot)]
prediction_filtre = [mult_terme_a_terme(prediction_brute[i], filtre_intensite) for i in range(len(prediction_brute))]
phrase = transcription(prediction_filtre)
phrase_str = [liste_mots[i] for i in phrase]


os.system('clear')
#phrase = [15, 3, 1]
#phrase_str = [liste_mots[i] for i in phrase]
#phrase_str = ['one', 'yes', 'one']
print(phrase_str)

trame_envoi = str_to_trame(phrase_str)
if trame_envoi == -1: message("Trop de mots", 'erreur')
if trame_envoi == -2: message("Identifiant de machine inconnu", 'erreur')
if trame_envoi == -3: message("Commande inconnue", 'erreur')
if trame_envoi == -4: message("Argument de commande inconnu", 'erreur')




#creation du socket TCP/IP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(.5)

#connection du socket au serveur
server_address = ('localhost', 10002)
print('\nConnection à %s : %s' % server_address)
sock.connect(server_address)

try:
	print("Trame envoyée : ", trame_envoi)
	sock.sendall(trame_envoi)
except: print("Envoi de la trame impossible")
try:
	trame_recue = sock.recv(64)
	print("Trame reçue : ", trame_recue)
	trame_to_msg(trame_envoi, trame_recue)
except: pass
sock.close()