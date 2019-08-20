from commun import *





def plot_history(history, len_old_history_0=0):
	abscisses_estim = [i+1 for i in range(len(history[0]))]
	abscisses_eval = history[4]
	plt.plot(abscisses_estim, history[0], color='#0165fc', linestyle='--')
	plt.plot(abscisses_estim, history[1], color='orangered', linestyle='--')
	plt.plot(abscisses_eval, history[2], color='blue')
	plt.plot(abscisses_eval, history[3], color='red')
	plt.plot([1, abscisses_estim[-1]], [1, 1], color='grey', linestyle='--')
	if len_old_history_0: plt.plot([len(history[0])-len_old_history_0, len(history[0])-len_old_history_0], [0, np.max(history)], color='grey', linestyle='--')
	plt.title("Historique d'évolution du modèle")
	plt.legend(["Précision éstimée", "Pertes éstimées", "Précision évaluée", "Pertes évaluées"])
	plt.xlabel("Etape")
	plt.ylabel("Précision, Taux de pertes")





if __name__ == '__main__':
	plot_history(lecture_fichier(EMPLACEMENT_ARGUMENT))
	plt.show()