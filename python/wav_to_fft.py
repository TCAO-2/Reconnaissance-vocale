#Ce script permet la transformation des fichiers .wav en fichiers .fft

from commun import *
from visualisation_fft import plot_spectrogramme





#vérification du dossier source
try: dictionnaire = os.listdir(DOSSIER_SOURCE)
except: message("Le dossier source n'existe pas", "erreur")
nb_etape_total = 2
etape_courante = 1
if CUT_FFT: nb_etape_total += 1
if VERIFICATION_DESTINATION: nb_etape_total += 1





def wav_to_fft(emplacement_fichier, frequence_min=FREQUENCE_MIN, frequence_max=FREQUENCE_MAX, frequence_echantionnage=FREQUENCE_ECHANTILLONAGE, chunk=CHUNK, fenetre=FENETRE):
	abscisses_frequences = np.linspace(0, frequence_echantionnage/2, chunk/2+1)
	pos_limite_inf, pos_limite_sup = cherche_pos_lim(abscisses_frequences)
	spectrogramme = []
	wf = wave.open(emplacement_fichier, 'rb')
	p = pyaudio.PyAudio()

	def callback(in_data, frame_count, time_info, status):
		data = wf.readframes(frame_count)
		return (data, pyaudio.paContinue)

	stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    stream_callback=callback)
	stream.start_stream()
	data = wf.readframes(chunk)
	l = len(data)
	while len(data) == l:#enregistrement des chunks complets uniquement
		spectrogramme.append(fft(data, pos_limite_inf, pos_limite_sup, chunk, fenetre))
		data = wf.readframes(chunk)
	stream.stop_stream()
	stream.close()
	wf.close()
	p.terminate()
	return np.vstack((np.array([abscisses_frequences[pos_limite_inf:pos_limite_sup]]), np.array(spectrogramme)/np.max(spectrogramme)))

def profil_spectrogramme(spectrogramme):#retourne une caractéristique montrant ou est situé l'information selon un critère des moindres carrés
	len_spectrogramme = len(spectrogramme)
	profil = []
	for i in range(len_spectrogramme):
		somme = 0.
		for j in range(len_spectrogramme):
			if j != i: somme += sum(spectrogramme[j]) / abs(i - j)**2
		profil.append(somme)
	return profil

def limites(liste, seuil):#recherche les limites suivant le seuil voulu
	lim = seuil * max(liste)
	lim_min, lim_max = 2, -2
	while liste[lim_min] < lim: lim_min += 1
	while liste[lim_max] < lim: lim_max -= 1
	return lim_min-2, len(liste) + lim_max + 2 - 1

def cherche_limite(stat):#recherche de l'iteration limite avant les fichiers parasites, doit être fait sur une fonction lisse
	i = 1
	while stat[i] <= stat[i+1]: i+=1#recherche du premier maximum local
	while stat[i] >= stat[i+1]: i+=1#recherche du minimum local suivant
	return i

def modif_limites(lim_min, lim_max, amplitude, glob_min, glob_max):#tout en gardant l'interval centré, modifie les limites pour que l'intervalle corresponde à l'amplitude désirée
	milieu = (lim_max + lim_min)//2
	inf, sup = milieu, milieu
	amp = 0
	while amp < amplitude:
		if (milieu - inf < sup - milieu) and (inf > glob_min): inf -= 1
		elif sup < glob_max: sup += 1
		elif inf > glob_min: inf -= 1
		else: break
		amp = sup - inf
	return inf, sup

def agrandissement_tableau(tableau, taille):#aggrandit un tableau numpy en vertical de part et d'autre
	nb_lignes_manquantes = taille - len(tableau)
	a = nb_lignes_manquantes//2
	b = nb_lignes_manquantes - a
	tab_a = np.array([np.zeros(len(tableau[0])) for ligne in range(a)])
	tab_b = np.array([np.zeros(len(tableau[0])) for ligne in range(b)])
	if b == 0: return np.array(tableau)
	elif a == 0: return np.vstack((np.array(tableau), tab_b))
	else: return np.vstack((tab_a, np.array(tableau), tab_b))

def intersection(spectrogramme, bruit):#utile à l'ajout de bruit
	abscisses_frequences, output = spectrogramme[0], []
	len_spectrogramme, len_bruit = len(spectrogramme), len(bruit)
	debut = random.randint(0, len_bruit - len_spectrogramme)
	for i in range(1, len_spectrogramme):
		output.append(spectrogramme[i] + bruit[debut+i])
	return np.vstack((np.array(abscisses_frequences), np.array(output)/np.max(output)))





#préparation
noise = []
try:
	dictionnaire.remove('noise')
	noise_list = os.listdir(DOSSIER_SOURCE + '/' + 'noise')
	for i in noise_list:
		tmp = wav_to_fft(DOSSIER_SOURCE + '/' + 'noise' + '/' + i)
		moy = np.sum(tmp) / ((len(tmp) - 1) * len(tmp[0]))
		noise.append(tmp/(10 * moy))
except: pass
date_execution_integralite_programme = time.time()
creation_dossier(DOSSIER_FFT)
if UTILISATION_TMP == True: creation_dossier(DOSSIER_TMP)
try: os.mkdir(DOSSIER_MODELE)
except: pass
len_dictionnaire = len(dictionnaire)
liste_wav = [os.listdir(DOSSIER_SOURCE + '/' + mot) for mot in dictionnaire]
nombre_wav = sum([len(i) for i in liste_wav])
print("{} mots à traîter pour un total de {} fichiers".format(len_dictionnaire, nombre_wav))





#conversion
print("Etape {} sur {} - Conversion des fichiers audio ...".format(etape_courante, nb_etape_total))
etape, date_depart = 1, time.time()
nb_chunk_max = 0

if UTILISATION_TMP:
	for i in range(len_dictionnaire):
		mot = dictionnaire[i]
		os.mkdir(DOSSIER_TMP + '/' + mot)
		for nom_fichier in liste_wav[i]:
			avancement(etape, nombre_wav, time.time()-date_depart, nom_fichier)
			spectrogramme = wav_to_fft(DOSSIER_SOURCE + '/' + mot + '/' + nom_fichier)
			if len(spectrogramme)-1 > nb_chunk_max: nb_chunk_max = len(spectrogramme) - 1
			enregistre_fichier(spectrogramme, DOSSIER_TMP + '/' + mot + '/' + nom_fichier[:-4] + '.fft')
			etape += 1
else:
	tableau_spectrogrammes = []
	for i in range(len_dictionnaire):
		mot = dictionnaire[i]
		tmp = []
		for nom_fichier in liste_wav[i]:
			avancement(etape, nombre_wav, time.time()-date_depart, nom_fichier)
			spectrogramme = wav_to_fft(DOSSIER_SOURCE + '/' + mot + '/' + nom_fichier)
			if len(spectrogramme)-1 > nb_chunk_max: nb_chunk_max = len(spectrogramme) - 1
			tmp.append(spectrogramme)
			etape += 1
		tableau_spectrogrammes.append(tmp)





os.system("clear")
print("Conversion des fichiers audio terminée")
etape_courante += 1




if CUT_FFT:
	#simplification
	print("Etape {} sur {} - Analyse de la pertinence des donnees ...".format(etape_courante, nb_etape_total))
	etape, date_depart = 1, time.time()
	liste_min, liste_max, stat = [], [], [0 for i in range(nb_chunk_max + 1)]

	if UTILISATION_TMP:
		for mot in dictionnaire:
			for nom_fichier in os.listdir(DOSSIER_TMP + '/' + mot):
				avancement(etape, nombre_wav, time.time()-date_depart, nom_fichier)
				emplacement_fichier = DOSSIER_TMP + '/' + mot + '/' + nom_fichier
				lim_min, lim_max = limites(profil_spectrogramme(np.loadtxt(emplacement_fichier, skiprows = 1)), SEUIL_BRUIT)
				stat[lim_max - lim_min] += 1
				liste_min.append(lim_min)
				liste_max.append(lim_max)
				etape += 1
	else:
		for i in range(len_dictionnaire):
			for j in range(len(liste_wav[i])):
				nom_fichier = liste_wav[i][j]
				avancement(etape, nombre_wav, time.time()-date_depart, nom_fichier[:-4] + '.fft')
				lim_min, lim_max = limites(profil_spectrogramme(tableau_spectrogrammes[i][j][1:]), SEUIL_BRUIT)
				stat[lim_max - lim_min] += 1
				liste_min.append(lim_min)
				liste_max.append(lim_max)
				etape += 1

	print("Analyse de la pertinence des données terminée")

	stat_lisse = lisse_liste(stat, nb_chunk_max//10)
	limite = cherche_limite(stat_lisse)#permet d'obtenir la longueur d'un mot à retenir

	if not MODE_AUTOMATIQUE:
		print("Limite suggérée : {}\t\tconserver cette limite ? [n/O]\nAvec ces paramètres {} fichiers seront conservés et {} seront rejetés".format(limite, sum(stat[:limite]), sum(stat[limite:])))
		plt.plot(stat)
		plt.plot(stat_lisse)
		plt.plot([limite, limite], [0, max(stat)], color = 'grey', linestyle = '--')
		plt.title("Graphe de répartition de la longueur des mots")
		plt.xlabel("Nombre de chunks")
		plt.ylabel("Nombre de fichiers")
		plt.show()

		test = 'a'
		while test not in ['n', 'O']: test=input()
		if test == 'n':
			print("Saisie de la nouvelle limite : [|0,{}|]".format(len(stat)-1))
			test = -1
			while test not in [i for i in range(len(stat))]:
				test = input()
				try: test=int(test)
				except: pass
			limite = test

	print("Limite choisie : {}\nFichiers a conserver : {}  Fichiers a rejeter : {}".format(limite, sum(stat[:limite]), sum(stat[limite:])))
	etape_courante += 1





	#application des opérations de simplification et sauvegarde des nouveaux fichiers
	print("Etape {} sur {} - Sauvegarde des nouveaux fichiers ...".format(etape_courante, nb_etape_total))
	etape, date_depart, stat2 = 1, time.time(), []

	if UTILISATION_TMP:
		for mot in dictionnaire:
			os.mkdir(DOSSIER_FFT + '/' + mot)
			stat3 = np.zeros(limite)
			for nom_fichier in os.listdir(DOSSIER_TMP + '/' + mot):
				avancement(etape, nombre_wav, time.time()-date_depart, nom_fichier)
				if liste_max[etape-1] - liste_min[etape-1] < limite:
					tmp = np.loadtxt(DOSSIER_TMP + '/' + mot + '/' + nom_fichier)
					abscisses_frequences, tmp = tmp[0], tmp[1:]
					lim_min, lim_max = modif_limites(liste_min[etape-1], liste_max[etape-1], limite, 0, len(tmp))
					spectrogramme = np.array(tmp[lim_min:lim_max])#réduction
					spectrogramme = agrandissement_tableau(spectrogramme, limite)#agrandissement
					stat3 += profil_spectrogramme(spectrogramme)
					enregistre_fichier(np.vstack((abscisses_frequences, spectrogramme/np.max(spectrogramme))), DOSSIER_FFT + '/' + mot + '/' + nom_fichier)
				etape += 1
			stat2.append(stat3/len(liste_wav[i]))
	else:
		for i in range(len_dictionnaire):
			mot = dictionnaire[i]
			os.mkdir(DOSSIER_FFT + '/' + mot)
			stat3 = np.zeros(limite)
			for j in range(len(liste_wav[i])):
				nom_fichier = liste_wav[i][j]
				avancement(etape, nombre_wav, time.time()-date_depart, nom_fichier[:-4] + '.fft')
				if liste_max[etape-1] - liste_min[etape-1] < limite:
					tmp = tableau_spectrogrammes[i][j][1:]
					lim_min, lim_max = modif_limites(liste_min[etape-1], liste_max[etape-1], limite, 0, len(tmp))
					spectrogramme = np.array(tmp[lim_min:lim_max])#réduction
					spectrogramme = agrandissement_tableau(spectrogramme, limite)#agrandissement
					stat3 += profil_spectrogramme(spectrogramme)
					enregistre_fichier(np.vstack((tableau_spectrogrammes[i][j][0], spectrogramme/np.max(spectrogramme))) , DOSSIER_FFT + '/' + mot + '/' + nom_fichier[:-4] + '.fft')
				etape += 1
			stat2.append(stat3/len(liste_wav[i]))
else:
	#aggrandissement et sauvegarde des nouveaux fichiers
	print("Etape {} sur {} - Sauvegarde des nouveaux fichiers ...".format(etape_courante, nb_etape_total))
	etape, date_depart, stat2 = 1, time.time(), []
	if UTILISATION_TMP:
		for mot in dictionnaire:
			os.mkdir(DOSSIER_FFT + '/' + mot)
			stat3 = np.zeros(nb_chunk_max)
			for nom_fichier in os.listdir(DOSSIER_TMP + '/' + mot):
				avancement(etape, nombre_wav, time.time()-date_depart, nom_fichier)
				tmp = np.loadtxt(DOSSIER_TMP + '/' + mot + '/' + nom_fichier)
				abscisses_frequences, tmp = tmp[0], tmp[1:]
				spectrogramme = agrandissement_tableau(tmp, nb_chunk_max)#agrandissement
				stat3 += profil_spectrogramme(spectrogramme)
				enregistre_fichier(np.vstack((abscisses_frequences, spectrogramme)), DOSSIER_FFT + '/' + mot + '/' + nom_fichier)
				etape += 1
			stat2.append(stat3/len(liste_wav[i]))
	else:
		for i in range(len_dictionnaire):
			mot = dictionnaire[i]
			os.mkdir(DOSSIER_FFT + '/' + mot)
			stat3 = np.zeros(nb_chunk_max)
			for j in range(len(liste_wav[i])):
				nom_fichier = liste_wav[i][j]
				avancement(etape, nombre_wav, time.time()-date_depart, nom_fichier[:-4] + '.fft')
				tmp = tableau_spectrogrammes[i][j][1:]
				spectrogramme = agrandissement_tableau(tmp, nb_chunk_max)#agrandissement
				stat3 += profil_spectrogramme(spectrogramme)
				enregistre_fichier(np.vstack((tableau_spectrogrammes[i][j][0], spectrogramme)) , DOSSIER_FFT + '/' + mot + '/' + nom_fichier[:-4] + '.fft')
				if NOISE == True:
					l=0
					for k in noise:
						spectrogramme2 = intersection(np.vstack((tableau_spectrogrammes[i][j][0], spectrogramme)), k)
						enregistre_fichier(spectrogramme2, DOSSIER_FFT + '/' + mot + '/' + nom_fichier[:-4] + '_' + noise_list[l] + '.fft')
						l += 1
				etape += 1
			stat2.append(stat3/len(liste_wav[i]))
	

print("Sauvegarde des fichiers terminée")
etape_courante += 1





#nettoyage des éventuels fichiers temporaires et vérification
if UTILISATION_TMP:
	shutil.rmtree(DOSSIER_TMP)
	print("Dossier temporaire supprimé")

enregistre_fichier(stat2, MODELE_STAT)
print("Profils sonores enregistrés")

if VERIFICATION_DESTINATION:
	print("Etape {} sur {} - Vérification de la destination ...".format(etape_courante, nb_etape_total))
	etape, date_depart = 1, time.time()
	if CUT_FFT: total_etape = sum(stat[:limite])
	else: total_etape = nombre_wav
	if NOISE: total_etape *= (len(noise_list) + 1)
	tmp = []
	for mot in dictionnaire:
		tmp2 = []
		for nom_fichier in os.listdir(DOSSIER_FFT + '/' + mot):
			avancement(etape, total_etape, time.time()-date_depart, nom_fichier)
			try:
				tmp3 = tableau_est_matrice(lecture_fichier(DOSSIER_FFT + '/' + mot + '/' + nom_fichier))
				if tmp3 == False: print('\n'); message("Fichier non matriciel {}".format(DOSSIER_FFT + '/' + mot + '/' + nom_fichier), "warning")
				else: tmp2.append(tmp3)
			except: print('\n'); message("Impossible de lire {}".format(DOSSIER_FFT + '/' + mot + '/' + nom_fichier), "warning")
			etape += 1
		tmp+=tmp2
	if etape-1 != total_etape: print('\n'); message("{} fichiers convertis sur {}".format(etape-1, total_etape), "warning")
	if not all(element == tmp[0] for element in tmp): message("Tous les fichiers enregistrés ne sont pas de la même taille", "warning")
	print("Vérification de la destination terminée ...")





duree_totale_execution = datetime.timedelta(seconds=(time.time() - date_execution_integralite_programme))
print("Durée totale d'exécution : {}".format(str(duree_totale_execution)))