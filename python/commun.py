#Ce script contient toutes les fonctions communes à l'utilisation d'autres scripts

from parametres import *





#messages
def message(a_imprimer, caracteristique=None):#permet d'imprimer des messages particuliers d'erreur et de warning
	CRED = '\033[91m'
	CORANGE = '\033[93m'
	CEND = '\033[0m'
	if caracteristique == "warning": print(CORANGE + "Warning : " + a_imprimer + CEND)
	elif caracteristique == "erreur": print(CRED + "Erreur : " + a_imprimer + ", abandon du programme" + CEND); exit()
	else: print(a_imprimer)





#manipulation de fichiers
def creation_dossier(emplacement_dossier):#créer un dossier tout en s'assurant que celui-ci est vide
	try:
		os.mkdir(emplacement_dossier)
		print("Le dossier '{}' à été crée".format(emplacement_dossier))
	except:
		if not MODE_AUTOMATIQUE:
			message("'{}' existe déjà, continuer ? Ceci effacera le contenu du dossier existant [n/O]".format(DOSSIER_FFT), "warning")
			test = 'a'
			while test not in ['n', 'O']: test=input()
			if test == 'n': exit()
		shutil.rmtree(emplacement_dossier)
		os.mkdir(emplacement_dossier)
		print("Le dossier '{}' est a présent vide".format(emplacement_dossier))

def lecture_fichier(emplacement_fichier):#retourne un tableau de flotant contenant les informations du fichier, le fichier ne doit contenir que des nombres. Pour les fichiers matriciels, utiliser np.loadtxt() en priorité
	with open(emplacement_fichier, 'r') as fichier:
		return [[float(i) for i in ligne.split(' ')] for ligne in fichier.readlines()]

def enregistre_fichier(tableau, emplacement_fichier):#enregistre un tableau de flotant dans un fichier
	it_max = len(tableau) - 1
	a_imprimer = ''
	for i in range(len(tableau)):
		a_imprimer += ' '.join([str(round(j, PRECISION_FLOAT)) for j in tableau[i]])
		if i < it_max: a_imprimer += '\n'
	with open(emplacement_fichier, mode='w') as fichier:
		fichier.write(a_imprimer)

def tableau_est_matrice(tableau):#vérifie que le tableau est bien une matrice, renvoie la dimension le cas échéant, renvoie False sinon
	len_lignes = [len(ligne) for ligne in tableau]
	if all(element == len_lignes[0] for element in len_lignes[1:]): return len(len_lignes), len_lignes[0]
	else: return False

def charge_modele_reseau_de_neurones(emplacement_json=MODELE_JSON, emplacement_h5=MODELE_H5):#retourne le modèle du réseau de neurones existant non-compilé
	json_file = open(emplacement_json, 'r')
	loaded_model_json = json_file.read()
	json_file.close()
	modele = model_from_json(loaded_model_json)
	modele.load_weights(emplacement_h5)
	return modele

def sauvegarde_modele_reseau_de_neurones(modele, emplacement_json=MODELE_JSON, emplacement_h5=MODELE_H5):#enregistre le modèle du réseau de neurones
	model_json = modele.to_json()
	with open(MODELE_JSON, "w") as json_file: json_file.write(model_json)
	modele.save_weights(MODELE_H5)





#affichage
def mult_tab(n):#retorune une chaine de caractère composé de '\r' + n fois '\t'
	output = '\r'
	for i in range(n): output += '\t'
	return output

def avancement(etape, total_etape, temps_execution=0., nom_tache=None):#affiche l'avancement d'un processus
	pourcentage_affiche = str(round(100 * etape / total_etape, 1))
	temps_affiche = str(datetime.timedelta(seconds=int(temps_execution*(total_etape/etape - 1))))
	sys.stdout.write("\033[K")#effacement de la ligne précedente
	sys.stdout.write("\rAvancement : {} %{}Temps restant : {}{}Etape : {} sur {}".format(pourcentage_affiche, mult_tab(4), temps_affiche, mult_tab(8), str(etape), str(total_etape)))
	if nom_tache != None: sys.stdout.write(mult_tab(12) + nom_tache)
	if etape == total_etape: sys.stdout.write('\n')





#transformée de Fourier
def fft(donnes_wav, pos_limite_inf, pos_limite_sup, chunk=CHUNK, fenetre=FENETRE):#retourne la transformée de Fourier d'un chunk
	waveData = wave.struct.unpack("%dh"%(chunk), donnes_wav)
	npArrayData = np.array(waveData)
	indata = npArrayData*fenetre
	fftData=np.abs(np.fft.rfft(indata))
	return fftData[pos_limite_inf:pos_limite_sup]

def cherche_pos_lim(abscisses_frequences, frequence_min=FREQUENCE_MIN, frequence_max=FREQUENCE_MAX):#retourne les indices correspondant aux fréquences min et max dans abscisses_frequences
	pos_limite_inf = 0
	while pos_limite_inf < len(abscisses_frequences) and abscisses_frequences[pos_limite_inf] < frequence_min: pos_limite_inf += 1
	pos_limite_sup = pos_limite_inf
	while pos_limite_sup < len(abscisses_frequences) and abscisses_frequences[pos_limite_sup] <= frequence_max: pos_limite_sup += 1
	return pos_limite_inf, pos_limite_sup





#divers
def lisse_liste(liste, n):#retourne une liste comprenant la moyenne des n plus proches voisins de la liste initiale pour chaque itération
	it, output = [i for i in range(len(liste))], []
	a = n//2
	b = n-a
	for i in range(len(liste)):
		tmp = [j for j in it if j in {k for k in range(i-a, i+b)}]
		output.append( sum(liste[tmp[0]:tmp[-1]+1]) / len(tmp) )
	return output

def init_keras():
	for i in range(NB_INITIALISATION_KERAS):
		try:
			K.set_image_dim_ordering('th')#corrige les erreurs avec [?,X,X,X], [X,Y,Z,X]
			K.clear_session()
			print("Keras initialisé"); break
		except: print("Tentative infructueuse d'initialisation de Keras"); time.sleep(1)