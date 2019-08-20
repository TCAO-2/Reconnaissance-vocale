from commun import *





def plot_spectrogramme(abscisses_frequences, spectrogramme, quantum_temps=QUANTUM_TEMPS):
	len_spectrogramme = len(spectrogramme)
	etendue_affichage = [abscisses_frequences[0], abscisses_frequences[-1], len_spectrogramme*quantum_temps, 0]
	ratio_affichage = (abscisses_frequences[-1]-abscisses_frequences[0])/(len_spectrogramme*quantum_temps)
	plt.imshow(spectrogramme, cmap="nipy_spectral", origin="upper", extent=etendue_affichage, aspect=ratio_affichage)
	plt.title("Spectrogramme")
	plt.xlabel("Frequence")
	plt.ylabel("Temps")





if __name__ == '__main__':
	donnees = np.loadtxt(EMPLACEMENT_ARGUMENT)
	plot_spectrogramme(donnees[0], donnees[1:])
	plt.show()