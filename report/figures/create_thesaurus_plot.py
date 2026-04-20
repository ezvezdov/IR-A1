import matplotlib.pyplot as plt

w_values = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
map_english = [0.2527, 0.2760, 0.2807, 0.2734, 0.2707, 0.2632, 0.2502, 0.2434, 0.2362, 0.2240, 0.2193]
map_czech = [0.3224, 0.3232, 0.3236, 0.3165, 0.3077, 0.2962, 0.2864, 0.2731, 0.2526, 0.2284, 0.2123]

plt.figure(figsize=(10, 6))
plt.plot(w_values, map_english, marker='o', label='English Collection')
plt.plot(w_values, map_czech, marker='o', label='Czech Collection')
plt.title('MAP Scores for different thesaurus scaling factors')
plt.xlabel('Scaling factor (w)')
plt.ylabel('MAP Score')
plt.xticks(w_values)
plt.grid()
plt.legend()
plt.savefig('thesaurus_plot.pdf')
plt.savefig('thesaurus_plot.png')

