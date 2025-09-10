# gui_demo.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

N = 10  # grid size

# Colors: blue=miss, gray=empty, red=hit
colors = ["#3b82f6", "#e5e7eb", "#ef4444"]
cmap = ListedColormap(colors)
bounds = [-1.5, -0.5, 0.5, 1.5]
norm = BoundaryNorm(bounds, cmap.N)

def create_state(hits, misses):
    state = np.zeros((N, N), dtype=int)
    for r, c in hits: state[r, c] = 1
    for r, c in misses: state[r, c] = -1
    return state

def draw_board(ax, state, title):
    ax.imshow(state, cmap=cmap, norm=norm, origin='upper')
    ax.set_xticks(np.arange(-.5, N, 1), minor=True)
    ax.set_yticks(np.arange(-.5, N, 1), minor=True)
    ax.grid(which="minor", color="#111827", linestyle='-', linewidth=0.8)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
    ax.set_xticks(np.arange(N)); ax.set_yticks(np.arange(N))
    ax.set_xticklabels([chr(ord('A')+i) for i in range(N)])
    ax.set_yticklabels([str(i+1) for i in range(N)])
    for t in ax.xaxis.get_major_ticks():
        t.tick1line.set_visible(False); t.tick2line.set_visible(False)
    for t in ax.yaxis.get_major_ticks():
        t.tick1line.set_visible(False); t.tick2line.set_visible(False)
    ax.set_title(title)

if __name__ == "__main__":
    player_hits, player_misses = [(2,3),(2,4)], [(0,0),(5,5)]
    ai_hits, ai_misses = [(6,7),(9,1)], [(4,5),(8,8)]

    player_state = create_state(player_hits, player_misses)
    ai_state = create_state(ai_hits, ai_misses)

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    draw_board(axes[0], player_state, "Player Board")
    draw_board(axes[1], ai_state, "AI Board")

    legend = [
        Patch(facecolor=colors[1], edgecolor='black', label='Trống'),
        Patch(facecolor=colors[2], edgecolor='black', label='Trúng'),
        Patch(facecolor=colors[0], edgecolor='black', label='Trượt'),
    ]
    fig.legend(handles=legend, loc='upper center', ncol=3, title="Ký hiệu")

    plt.tight_layout()
    plt.show()
