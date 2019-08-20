#Ce script contient toutes les bibliothèques et variables globales que l'utilisateur est suceptible de changer pour adapter le programme a ses besoins

print('Chargement des bibliothèques ...')
import os, shutil, sys, time, datetime, random

import numpy as np
import matplotlib.pyplot as plt

import pyaudio, wave

from keras.models import Model, Sequential, load_model, model_from_json
from keras.layers import *
from keras.utils import np_utils
from keras import backend as K
print("Bibliothèques chargées")





#parametres d'emplacement et de nom de fichiers
NOM_SOURCE = "src_command"								#nom du dossier source contenant le jeu de données à fournir pour l'apprentissage du réseau de neurones
NOM_EXPORT = "command"									#nom sous lequel les dossiers et fichiers crées seront enregistrés

EMPLACEMENT_SOURCE = "../src"							#ici sont stockés les jeux de données au format .wav
EMPLACEMENT_FFT = "../fft"								#ici sont enregistrés les spectrogrammes au format .fft
EMPLACEMENT_MODELE = "../models"						#ici sont enregistrés les fichiers contenant les informations du modèle
EMPLACEMENT_TMP = "../tmp"								#ici sont enregistrés les fichiers temporaires
try: EMPLACEMENT_ARGUMENT = sys.argv[1]					#variable globale éventuellement placée en argument
except: EMPLACEMENT_ARGUMENT = None

DOSSIER_SOURCE = EMPLACEMENT_SOURCE + '/' + NOM_SOURCE
DOSSIER_FFT = EMPLACEMENT_FFT + '/' + NOM_EXPORT
DOSSIER_MODELE = EMPLACEMENT_MODELE + '/' + NOM_EXPORT
DOSSIER_TMP = EMPLACEMENT_TMP + '/' + NOM_EXPORT

MODELE_STAT = DOSSIER_MODELE + '/' + "model.stat"		#ce fichier contient les données statistiques issues de la création des spectrogrammes
MODELE_H5 = DOSSIER_MODELE + '/' + "model.h5"			#ce fichier contient la sauvegarde des poids du réseau de neurone
MODELE_JSON = DOSSIER_MODELE + '/' + "model.json"		#ce fichier contient le modèle du réseau de neurone
MODELE_HISTORY = DOSSIER_MODELE + '/' + "model.history"	#ce fichier contient l'historique d'apprentissage du réseau de neurone





#parametres d'affichage et d'execution
PRECISION_FLOAT = 4						#nombre de décimales dans les fichiers enregistrés
VERIFICATION_DESTINATION = True			#vérifie la destination en fin d'execution
UTILISATION_TMP = True					#utilise des fichiers temporaires pour décharger la mémoire vivie, plus lent de 30% environ pour wav_to_fft.py, adapté aux gros jeux de données
MODE_AUTOMATIQUE = False				#pose le moins de questions possible, prends les paramètres par défaut, n'affiche aucune statistique automatiquement, écrase les fichiers de destination par défaut





#parametres audio
FREQUENCE_MIN = 0						#plage de fréquence utilisée - fréquence minimale (Hz)
FREQUENCE_MAX = 8000					#plage de fréquence utilisée - fréquence maximale (Hz)
FREQUENCE_ECHANTILLONAGE = 16000		#fréquence d'achantillonage (Hz)
FORMAT = pyaudio.paInt16				#format selon lequel les données seront manipulées par la librairie Pyaudio
CANAUX = 1								#nombre de canaux d'enregistrement
CHUNK = 2**8							#taille des lots de données découpés : un petit paramètre favorise la résolution temporelle, un gros paramètre favorise la résolution fréquentielle
FENETRE = np.blackman(CHUNK)			#fenêtre choisie pour la transformée de Fourier
CUT_FFT = False							#optimisation permettant la réduction de la taille des spectrogrammes dans le but de ne correspondre qu'à la durée d'un mot
SEUIL_BRUIT = .05						#seuil à partir duquel l'information est traîtée comme du bruit (unité)
SEUIL_DETECTION = .15					#seuil de probabilité à partir duquel l'information est traitée comme un mot
DUREE_TAMPON = 1						#durée sur laquelle est estimé le déclenchement automatique d'un enregistrement (s)
NOISE = True							#augmentation des données en introduisant du bruit
QUANTUM_TEMPS = CHUNK / FREQUENCE_ECHANTILLONAGE






#parametres d'apprentissage du réseau de neurones
PART_TEST = 1/6							#part du jeu de données dédié aux tests
TAILLE_TMP = 50000						#si UTILISATION_TMP = True, nombre de fichiers utilisés dans un set de données pour l'apprentissage du réseau de neurones, numpy n'arrive pas à convertir plus de 50.000 fichiers environ
MODELE_EXISTANT = True					#utilisation d'un modèle existant pour poursuivre l'apprentissage
NB_EPOCH = 1000							#nombre de passages sur l'intégralité du jeu de données pendant l'apprentissage
NB_EPOCH_SANS_PAUSE = 20				#taille du cycle sans pause pour évaluer le modèle sur le jeu de données test (le modèle est estimé à chaque passage, mais l'évaluation est plus précise que l'estimation)
BATCH_SIZE = 4096						#taille des groupes d'echantillons utilises pour l'apprentissage (plus le paramètre est gros, plus la mémoire vive nécessaire est importante)
APPRENTISSAGE_BOUCLE = False			#tant que le durée indiquée BOUCLE_TEMPS n'est pas dépassée, l'apprentissage se poursuit de NB_EPOCH passages
BOUCLE_TEMPS = 3600						#durée limite déterminant le non-renouvellement de l'apprentissage (s) (active si APPRENTISSAGE_BOUCLE = True)
NB_INITIALISATION_KERAS = 5				#Nombre de tentative d'initialisation de Keras avant abandon du programme (Keras ne peux pas toujours s'initialiser correctement suivant la mémoire instantanément allouable)