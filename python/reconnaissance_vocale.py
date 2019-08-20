from commun import *




#chargement du reseau de neurone existant
try:
	modele = charge_modele_reseau_de_neurones()
	print("Modèle chargé")
except: message("Impossible de charger le modèle existant", "erreur")

liste_mots = os.listdir(DOSSIER_FFT)
nombre_mots = len(liste_mots)
abscisses_frequences = np.linspace(0, FREQUENCE_ECHANTILLONAGE/2, CHUNK/2+1)
pos_limite_inf, pos_limite_sup = cherche_pos_lim(abscisses_frequences)
taille_tampon = DUREE_TAMPON//QUANTUM_TEMPS + 1
stat = lecture_fichier(MODELE_STAT)
fenetre_mot = len(stat[0])
len_fft = pos_limite_sup - pos_limite_inf




def mult_terme_a_terme(liste1, liste2):
	liste_out = []
	for i in range(len(liste1)):
		liste_out.append(liste1[i]*liste2[i])
	return liste_out

def fin_phrase(intensite):
	if len(intensite) > 140 and sum(intensite[len(intensite)-140:])/(140*max(intensite)) < .1: return True
	if len(intensite) > 2000: return True
	return False

def append_decal(liste, element):#ajoute un element en fin de liste en decalant tous les precedents et en supprimant le premier
	for i in range(1, len(liste)):
		liste[i-1] = liste[i]
	liste[-1] = element

def min_matrice(matrice):#matrice triée selon l'axe secondaire
	return min([i[0] for i in matrice if i != []])

def indice_min_matrice(matrice):#renvoie la ligne suivant laquelle le minimum se trouve, matrice triée selon l'axe secondaire
	tmp = min_matrice(matrice)
	tmp2 = [i[0] if i != [] else -1 for i in matrice]
	return tmp2.index(tmp)

def lecture_audio():#retourne DATA et intensite
	print("Initialisation de l'enregistrement ...")
	p = pyaudio.PyAudio()
	stream = p.open(format=FORMAT,
	            channels=CANAUX,
	            rate=FREQUENCE_ECHANTILLONAGE,
	            input=True,
	            frames_per_buffer=CHUNK)
	stream.start_stream()
	frames, tmp, intensite = [], [], []
	while(len(frames) < taille_tampon):
		data = stream.read(CHUNK)
		tmp = fft(data, pos_limite_inf, pos_limite_sup)
		frames.append(tmp)
		intensite.append(sum(tmp))
	print("\n\nParlez maintenant ...\n\n")

	while((intensite[-1] - sum(intensite)/taille_tampon)/max(intensite) < .6):
		data = stream.read(CHUNK)
		tmp = fft(data, pos_limite_inf, pos_limite_sup)
		append_decal(frames, tmp)
		append_decal(intensite, sum(tmp))
	print("Debut de la phrase")
	while(not fin_phrase(intensite)):
		data = stream.read(CHUNK)
		tmp = fft(data, pos_limite_inf, pos_limite_sup)
		frames.append(tmp)
		intensite.append(sum(tmp))
	print("Enregistrement terminé")
	stream.stop_stream()
	stream.close()
	p.terminate()
	DATA = np.array(frames)
	DATA /= np.max(DATA)
	intensite /= max(intensite)
	return DATA, intensite

def prediction(donnees_brutes):
	pre = []
	for i in range(len(donnees_brutes) - fenetre_mot):
		echantillon = (donnees_brutes[i:fenetre_mot+i]/np.max(donnees_brutes[i:fenetre_mot+i])).reshape(1, 1, fenetre_mot, len_fft)
		pre.append(modele.predict(echantillon)[0])
	return np.transpose(pre)

def transcription(prediction, seuil_detection=SEUIL_DETECTION, proximite=fenetre_mot//2):#passe d'une prédiction a une chaîne de caractères
	len_prediction = len(prediction[0])
	date_mots = []
	integrale_mots = []
	for pre in prediction:
		tmp1, tmp2, i = [], [], 0
		while(i < len_prediction and pre[i] < SEUIL_DETECTION):	i += 1
		while(i < len_prediction):
			date_debut, integrale = i, 0
			while(i < len_prediction and pre[i] >= SEUIL_DETECTION): integrale += pre[i]; i += 1
			tmp1.append((date_debut + i)//2)
			tmp2.append(integrale)
			while(i < len_prediction and pre[i] < SEUIL_DETECTION):	i += 1
		date_mots.append(tmp1)
		integrale_mots.append(tmp2)
	output = []
	while(sum([len(i) for i in date_mots])):
		date_min = min_matrice(date_mots)
		max_score, mot_retenu = 0, -1
		while(min_matrice(date_mots) < date_min + proximite):
			indice = indice_min_matrice(date_mots)
			score = integrale_mots[indice].pop(0)
			if max_score < score: max_score, mot_retenu = score, indice
			date_mots[indice].pop(0)
			if not sum([len(i) for i in date_mots]): break
		output.append(mot_retenu)
	return output



if __name__ == '__main__':
	DATA, intensite = lecture_audio()
	prediction_brute = prediction(DATA)

	filtre_intensite = [intensite[i + fenetre_mot//2] for i in range(len(DATA) - fenetre_mot)]
	filtre_conv = [np.correlate(intensite, i) for i in stat]
	filtre_intensite /= max(filtre_intensite)
	filtre_conv = [i/max(i) for i in filtre_conv]


	prediction1 = [mult_terme_a_terme(prediction_brute[i], filtre_intensite) for i in range(len(prediction_brute))]#prediction suivant le filtre intensité
	prediction2 = [mult_terme_a_terme(prediction_brute[i], filtre_conv[i]) for i in range(len(prediction_brute))]#prediction suivant le filtre convolutif

	prediction_brute = [mult_terme_a_terme(i, i) for i in prediction_brute]

	prediction3 = [mult_terme_a_terme(prediction_brute[i], filtre_intensite) for i in range(len(prediction_brute))]#prediction suivant le filtre intensité
	prediction4 = [mult_terme_a_terme(prediction_brute[i], filtre_conv[i]) for i in range(len(prediction_brute))]#prediction suivant le filtre convolutif

	prediction_brute = prediction(DATA)
	filtre_intensite = mult_terme_a_terme(filtre_intensite, filtre_intensite)

	prediction5 = [mult_terme_a_terme(prediction_brute[i], filtre_intensite) for i in range(len(prediction_brute))]#prediction suivant le filtre intensité
	prediction6 = [mult_terme_a_terme(prediction_brute[i], filtre_conv[i]) for i in range(len(prediction_brute))]#prediction suivant le filtre convolutif

	prediction_brute = [mult_terme_a_terme(i, i) for i in prediction_brute]

	prediction7 = [mult_terme_a_terme(prediction_brute[i], filtre_intensite) for i in range(len(prediction_brute))]#prediction suivant le filtre intensité
	prediction8 = [mult_terme_a_terme(prediction_brute[i], filtre_conv[i]) for i in range(len(prediction_brute))]#prediction suivant le filtre convolutif



	print([liste_mots[i] for i in transcription(prediction1)])
	"""
	print([liste_mots[i] for i in transcription(prediction2)])
	print([liste_mots[i] for i in transcription(prediction3)])
	print([liste_mots[i] for i in transcription(prediction4)])
	print([liste_mots[i] for i in transcription(prediction5)])
	print([liste_mots[i] for i in transcription(prediction6)])
	print([liste_mots[i] for i in transcription(prediction7)])
	print([liste_mots[i] for i in transcription(prediction8)])
	"""