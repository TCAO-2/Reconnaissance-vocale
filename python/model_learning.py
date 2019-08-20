#Ce script contient la partie apprentissage du réseau de neurones, l'architecture de ce dernier est disponible dans la fonction 'creation_modele'

from commun import *
from visualisation_history import plot_history





#initialisation de la mise en memoire des donnes
dictionnaire = os.listdir(DOSSIER_FFT)								#liste de tous les mots differents
len_dictionnaire = len(dictionnaire)								#nombre de mots differents
nom_fichiers = [os.listdir(DOSSIER_FFT + '/' + mot) for mot in dictionnaire]
nb_fichiers = sum([len(dossier) for dossier in nom_fichiers])		#utile a l'affichage de la progression pendant le chargement des donnees





def melange_liste(liste):
	out = []
	for i in range(len(liste)):
		out.append(liste.pop(random.randint(0, len(liste) - 1)))
	return out

def charge_donnee(set_train, set_test):#charge les données à partir de l'itération nb_init et jusqu'à nb_set
	X_train, X_test, y_train, y_test = [], [], [], []
	date_depart = time.time()
	etape = 1
	total_etape = len(set_train) + len(set_test)
	for emplacement_fichier in set_train:
		tmp = emplacement_fichier.split('/')
		mot, nom_fichier = tmp[3], tmp[4]
		avancement(etape, total_etape, time.time()-date_depart, nom_fichier)
		X_train.append(np.loadtxt(emplacement_fichier, skiprows=1))
		y_train.append(dictionnaire.index(mot))
		etape += 1
	for emplacement_fichier in set_test:
		tmp = emplacement_fichier.split('/')
		mot, nom_fichier = tmp[3], tmp[4]
		avancement(etape, total_etape, time.time()-date_depart, nom_fichier)
		X_test.append(np.loadtxt(emplacement_fichier, skiprows=1))
		y_test.append(dictionnaire.index(mot))
		etape += 1
	return X_train, X_test, y_train, y_test

def creation_modele(input_shape, output_shape):#retourne le modèle de réseau de neurones non compilé
	img_in = Input(shape=input_shape, name='img_in')
	x = img_in

	x = Convolution2D(2, (5,5), strides=(2,2), use_bias=False)(x)       
	x = BatchNormalization()(x)
	x = Activation("relu")(x)
	x = Dropout(.4)(x)
	x = Convolution2D(4, (5,5), strides=(2,2), use_bias=False)(x)       
	x = BatchNormalization()(x)
	x = Activation("relu")(x)
	x = Dropout(.4)(x)

	x = Flatten(name='flattened')(x)

	x = Dense(100, use_bias=False)(x)
	x = BatchNormalization()(x)
	x = Activation("relu")(x)
	x = Dropout(.4)(x)
	x = Dense(50, use_bias=False)(x)
	x = BatchNormalization()(x)
	x = Activation("relu")(x)
	x = Dropout(.3)(x)

	out_dir = Dense(output_shape, activation='softmax')(x)
	
	return Model(inputs=[img_in], outputs=[out_dir])

def entraine_modele(modele, X_train, y_train, batch_size=BATCH_SIZE, nb_epoch=NB_EPOCH, nb_epoch_sans_pause=NB_EPOCH_SANS_PAUSE):#retourne le modèle entraîné ainsi que les statistiques associées
	acc, loss, eval_acc, eval_loss = [], [], [], []
	etape_sans_pause = [nb_epoch_sans_pause for i in range(nb_epoch//nb_epoch_sans_pause)]
	if nb_epoch%nb_epoch_sans_pause: etape_sans_pause.append(nb_epoch%nb_epoch_sans_pause)
	abscisse_eval = [sum(etape_sans_pause[:i+1]) for i in range(len(etape_sans_pause))]
	etape = 1
	for i in etape_sans_pause:
		print("Apprentissage du modèle sur {} étapes ...\nEtape actuelle : {} sur {}".format(i, etape, nb_epoch))

		h = modele.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=i, verbose=1)
		acc += h.history['acc']
		loss += h.history['loss']

		print('Evaluation intermediaire du modèle ...')
		score = modele.evaluate(X_test, Y_test, verbose=0)
		eval_loss.append(score[0])
		eval_acc.append(score[1])

		print("Score intermediaire :\t\ttaux de perte : {}\t\t taux de précision : {}\n".format(score[0], score[1]))
		etape += i
	return modele, [acc, loss, eval_acc, eval_loss, abscisse_eval]

def mise_a_jour_history(history, emplacement_old_history=MODELE_HISTORY):#retourne l'historique mis à jour
	old_history = lecture_fichier(emplacement_old_history)
	len_old_history = len(old_history[0])
	for i in range(4): history[i] = old_history[i] + history[i]
	history[4] = old_history[4] + [j+len_old_history for j in history[4]]
	return history





#initialisation de keras
init_keras()





#choix des jeux de données
emplacement_train, emplacement_test = [], []
etape, nombre_test = 1, 0
for i in range(len(nom_fichiers)):
	for j in range(len(nom_fichiers[i])):
		emplacement_fichier = DOSSIER_FFT + '/' + dictionnaire[i] + '/' + nom_fichiers[i][j]
		if etape * PART_TEST >  nombre_test:
			emplacement_test.append(emplacement_fichier)
			nombre_test += 1
		else: emplacement_train.append(emplacement_fichier)
		etape += 1





print("Mélange des jeux de données et répartition en sets ...")
emplacement_train, emplacement_test = melange_liste(emplacement_train), melange_liste(emplacement_test)
if UTILISATION_TMP:
	set_train, set_test = [], []
	nb_train, nb_test = 0, 0
	nb_total_train, nb_total_test = len(emplacement_train), len(emplacement_test)
	nb_set = nb_fichiers // TAILLE_TMP
	if nb_fichiers % TAILLE_TMP: nb_set += 1
	for i in range(nb_set):
		tmp_train, tmp_test = 0, 0
		while (nb_train + tmp_train < nb_total_train) and (nb_test + tmp_test < nb_total_test) and tmp_train + tmp_test < TAILLE_TMP:
			if nb_test + tmp_test < PART_TEST * (nb_train + nb_test + tmp_train + tmp_test): tmp_test += 1
			else: tmp_train += 1
		if nb_train + tmp_train >= nb_total_train:
			while(nb_test + tmp_test < nb_total_test): tmp_test += 1
		elif nb_test + tmp_test >= nb_total_test:
			while(nb_train + tmp_train < nb_total_train): tmp_train += 1
		set_train.append(emplacement_train[nb_train:nb_train+tmp_train])
		set_test.append(emplacement_test[nb_test:nb_test+tmp_test])
		nb_train += tmp_train
		nb_test += tmp_test
else:
	set_train, set_test = [emplacement_train], [emplacement_test]
print("Mélange des jeux de données et répartition en sets terminé")
	




#definition de la structure du reseau ou chargement du reseau existant
tmp = np.loadtxt(set_train[0][0], skiprows=1)
a, b = len(tmp), len(tmp[0])
if MODELE_EXISTANT:
	try:
		modele = charge_modele_reseau_de_neurones()
		print("Modèle chargé")
	except: message("Impossible de charger le modèle existant", "erreur")
else:
	modele = creation_modele(input_shape=(1, a, b), output_shape=len_dictionnaire)
	print("Modèle crée")
#compilation du modele
for i in range(NB_INITIALISATION_KERAS):
	try: modele.compile(loss='categorical_crossentropy', optimizer='adadelta', metrics=['accuracy']); break
	except: print("Tentative infructueuse d'initialisation de Keras"); time.sleep(1)





for i in range(len(set_train)):
	print("Entraînement sur un groupe de {} échantillons sur {} - étape {} sur {}".format(len(set_train[i])+len(set_test[i]), nb_fichiers, i+1, nb_set))
	#mise en memoire des donnes
	print('Chargement des données ...')
	X_train, X_test, y_train, y_test = charge_donnee(set_train[i], set_test[i])
	print('\nChargement des données terminé')

	#caracterisation et mise en forme des donnes
	X_train, X_test, y_train, y_test = np.array(X_train), np.array(X_test), np.array(y_train), np.array(y_test)

	a = len(X_train[0])		#excursion temporelle
	b = len(X_train[0][0])	#excursion frequentielle
	c = X_train.shape[0]	#nombre d'echantillons d'apprentissage
	d = X_test.shape[0]		#nombre d'echantillons de test

	X_train = X_train.reshape(c, 1, a, b)
	X_test = X_test.reshape(d, 1, a, b)
	Y_train = np_utils.to_categorical(y_train, len_dictionnaire)
	Y_test = np_utils.to_categorical(y_test, len_dictionnaire)

	#apprentissage du modele
	date_depart = time.time()

	if APPRENTISSAGE_BOUCLE:
		while time.time() - date_depart < BOUCLE_TEMPS:
			print("Durée d'entraînement actuelle : {} sur {}".format(time.time() - date_depart, BOUCLE_TEMPS))
			modele, history = entraine_modele(modele, X_train, y_train)
	else: modele, history = entraine_modele(modele, X_train, y_train)

duree_totale_execution = datetime.timedelta(seconds=(time.time() - date_depart))
print("Durée totale d'entraînement : {}".format(duree_totale_execution))





#enregistrement du modèle et de l'historique
try: os.mkdir(DOSSIER_MODELE)
except: pass
sauvegarde_modele_reseau_de_neurones(modele)
print("Modèle sauvegardé sur le disque dur")

if MODELE_EXISTANT:#mise à jour de l'historique
	try:
		history = mise_a_jour_history(history)
		print("Historique mis à jour")
	except: message("Impossible de mettre à jour l'historique {} Seul le nouvel historique sera enregistré", "warning")
enregistre_fichier(history, MODELE_HISTORY)
print("Historique sauvegardé sur le disque dur")

if not MODE_AUTOMATIQUE:
	plot_history(history)
	plt.show()