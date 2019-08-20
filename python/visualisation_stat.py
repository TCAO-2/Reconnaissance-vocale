from commun import *





def plot_stat(stat, legende=[], quantum_temps=QUANTUM_TEMPS, dossier_fft=DOSSIER_FFT):
	for i in stat:
		plt.plot([j*quantum_temps for j in range(len(i))], i)
	plt.legend(legende)
	plt.title("Evolution de l'intensité sonore moyenne de chaque mot")
	plt.xlabel("Temps")
	plt.ylabel("intensité sonore")





if __name__ == '__main__':
	plot_stat(lecture_fichier(EMPLACEMENT_ARGUMENT))
	plt.show()