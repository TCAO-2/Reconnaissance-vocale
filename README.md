# Application de reconnaissance vocale

Cette application utilisant un réseau de neurones s'utilise en plusieurs phases :
- Lecture des exemples (.wav) et conversion en spectrogrammes (.fft)
- Apprentissage du réseau de neurones basé sur les spectrogrammes de référence
- Reconnaissance vocale utilisant le réseau de neurones entraîné

Les différents dossiers servent entre-autres à garder en mémoire le travail réalisé à chaque étape :
- 'fft' contient les spectrogrammes (.fft) obtenus à partir des fichiers sources (.wav)
- 'livrables' contient les compte-rendus liés aux projets
- 'models' contient les modèles de réseaux de neurones et les statistiques associées aux modèles
- 'python' contient les fichiers python des différents scripts qui constituent le programme
- 'src' contient les fichiers source (.wav) utilisés comme base pour les jeux de données
- 'tmp' est l'emplacement de sauvegarde des fichiers temporaires

Tous les paramètres que l'utilisateur est susceptible de modifier pour adapter le programme à son usage se trouvent dans le fichier parametres.py





## Lecture des exemples (.wav) et conversion en spectrogrammes (.fft) - wav_to_fft.py

Chaque fichier source (.wav) est convertis en spectrogramme (.fft) et enregistré dans le dossier 'fft'.

Les paramètres importants pour cette phase sont :
NOM_SOURCE = "src_command"				nom du dossier source contenant le jeu de données à fournir pour l'apprentissage du réseau de neurones
NOM_EXPORT = "command_number"			nom du sous répertoire se situant dans le dossier 'fft' où les fichiers .fft seront enregistrés, sera crée si il n'existe pas, sera vidé s'il existe

PRECISION_FLOAT = 4						nombre de décimales dans les fichiers enregistrés
VERIFICATION_DESTINATION = True			vérifie la destination 'fft' en fin d'exécution (taille des fichiers, nombre de fichiers) par mesure de précaution
UTILISATION_TMP = False					utilise des fichiers temporaires pour décharger la mémoire vive, plus lent de 30% environ, évite au programme de planter à cause d'un manque de mémoire vive lors de l'utilisation de gros jeux de données
MODE_AUTOMATIQUE = False				écrase le sous-dossier de destination sans demander de confirmation, ne présente pas les statistiques de simplification et choisi une valeur prédéterminée censé être optimale

FREQUENCE_MIN = 0						plage de fréquence utilisée - fréquence minimale (Hz)
FREQUENCE_MAX = 8000					plage de fréquence utilisée - fréquence maximale (Hz)
FREQUENCE_ECHANTILLONAGE = 16000		fréquence d'échantillonage (Hz)
FORMAT = pyaudio.paInt16				format selon lequel les données seront manipulées par la librairie Pyaudio
CANAUX = 1								nombre de canaux d'enregistrement
CHUNK = 2^8								taille des lots de données découpés : un petit paramètre favorise la résolution temporelle, un gros paramètre favorise la résolution fréquentielle
FENETRE = np.blackman(CHUNK)			fenêtre choisie pour la transformée de Fourier
CUT_FFT = False							réduction de la taille des spectrogrammes dans le but de ne correspondre qu'à la durée d'un mot
SEUIL_BRUIT = .05						seuil à partir duquel l'information est traîtée comme du bruit
NOISE = True							augmentation des données en introduisant du bruit

C'est cette étape qui déterminera la taille des entrées du réseau de neurones ainsi que le nom attribué au modèle.
L'exécution peut s'avérer longue, compter 1h30 -> 2h pour le jeu de données fourni, 5h -> 6h avec l'ajout du bruit fourni.
La console est remplie d'erreurs pendant la première étape du à la librairie PyAudio, ces erreurs sont mineures
Une sauvegarde des statistiques faites sur les spectrogrammes est disponible sous MODELE_STAT





## Entraînement du réseau de neurones - model_learning.py

L'entraînement du réseau de neurones permet d'avoir un modèle prédictif performant. Le programme permet de créer un nouveau modèle pour l'entraîner ou de continuer l'entraînement d'un modèle déjà existant.

Les paramètres importants pour cette phase sont :
UTILISATION_TMP = False					évite au programme de planter à cause d'un manque de mémoire vive lors de l'utilisation de gros jeux de données en découpant l'apprentissage en plusieurs phases contant une plus petite partie du jeu de données
TAILLE_TMP = 50000						si UTILISATION_TMP = True, nombre de fichiers utilisés dans un set de données pour l'apprentissage du réseau de neurones, numpy n'arrive pas à convertir plus de 50.000 fichiers environ en un seul tableau

PART_TEST = 1/6							part du jeu de données dédié aux tests
MODELE_EXISTANT = False					utilisation d'un modèle existant pour poursuivre l'apprentissage
NB_EPOCH = 100							nombre de passages sur l'intégralité du jeu de données pendant l'apprentissage
NB_EPOCH_SANS_PAUSE = 5					taille du cycle sans pause pour évaluer le modèle sur le jeu de données test (le modèle est estimé à chaque passage, mais l'évaluation est plus précise que l'estimation)
BATCH_SIZE = 4096						taille des groupes d'échantillons utilisés pour l'apprentissage (plus le paramètre est gros, plus la mémoire vive nécessaire est importante)
APPRENTISSAGE_BOUCLE = False			tant que le durée indiquée BOUCLE_TEMPS n'est pas dépassée, l'apprentissage se poursuit de NB_EPOCH passages
BOUCLE_TEMPS = 3600						Durée limite déterminant le non-renouvellement de l'apprentissage (s) (active si APPRENTISSAGE_BOUCLE = True)
NB_INITIALISATION_KERAS = 5				Nombre de tentative d'initialisation de Keras avant abandon du programme (Keras ne peux pas toujours s'initialiser correctement suivant la mémoire instantanément allouable)

L'exécution a toujours été réalisée avec la librairie Tensorflow compatible GPU, je ne connais pas les conséquences d'une exécution CPU uniquement
L'exécution est assez longue, mais une évaluation étant faite régulièrement, il est facile de se faire une idée des performances du modèle
Une sauvegarde de l'évolution est disponible sous MODELE_HISTORY





## Visualisation des données - visualisation_fft.py - visualisation_history.py - visualisation_stat.py

Ces scripts permettent de visualiser les différentes données mises en mémoire. Les fonctions de visualisation peuvent être appelées dans d'autres scripts ou être utilisés directement par la commande au choix :
* python3 visualisation_fft.py chemin_fichier
* python3 visualisation_history.py chemin_fichier
* python3 visualisation_stat.py chemin_fichier





## Transcription à la volée en texte d'une acquisition audio - reconnaissance_vocale.py

Permet la transcription après avoir capté un enregistrement audio de l'utilisateur

Les parametres importants pour cette phase sont :
SEUIL_DETECTION = .15					seuil de probabilité à partir duquel l'information est traitée comme un mot
DUREE_TAMPON = 1						durée sur laquelle est estimé le déclenchement automatique d'un enregistrement (s)





## Commande vocale par ModBus et client TCP - commande_vocale.py

Permet de transmettre les commandes ModBus en tant que client TCP sur le réseau après avoir capté et interprété un enregistrement audio de l'utilisateur

Les paramètres importants pour cette phase sont :
SEUIL_DETECTION = .15					seuil de probabilité à partir duquel l'information est traitée comme un mot
DUREE_TAMPON = 1						durée sur laquelle est estimé le déclenchement automatique d'un enregistrement (s)

Les paramètres propres aux commandes à interpréter à partir des enregistrement sont à modifier directement dans le fichier commande_vocale.py dans les tableaux de la forme :
commande	argument	->		READ/WRITE 	IN/OUT 		NUM/ANALOG 		Adress 		value 		offset

Le script simulation.py est à exécuter en parallèle et avant commande_vocale.py





## Emulation de machines ModBus et serveur TCP - simulation.py

Permet d'émuler le fonctionnement de machines ModBus sur le réseau afin de commander ces dernières et d'observer leurs évolutions sans avoir à utiliser de vraies machines

3 types de machines sont disponibles : la grue, le four et le convoyeur
