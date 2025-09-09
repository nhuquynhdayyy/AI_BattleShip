# Battleship 10x10 grid demo with colored cells for empty / hit / miss.
# empty=0, hit=1, miss=-1


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch


N = 10  # grid size


# Màu: blue=miss, gray=empty, red=hit
colors = ["#3b82f6", "#e5e7eb", "#ef4444"]
cmap = ListedColormap(colors)
bounds = [-1.5, -0.5, 0.5, 1.5]
norm = BoundaryNorm(bounds, cmap.N)


# ---- Trạng thái bảng (thay bằng dữ liệu thật của bạn) ----
state = np.zeros((N, N), dtype=int)
hits   = [(2, 3), (2, 4), (6, 7), (9, 1)]   # các ô trúng
misses = [(0, 0), (4, 5), (7, 2), (8, 8)]   # các ô trượt
for r, c in hits:   state[r, c] = 1
for r, c in misses: state[r, c] = -1
# -----------------------------------------------------------


fig, ax = plt.subplots(figsize=(6, 6))
ax.imshow(state, cmap=cmap, norm=norm, origin='upper')


# Kẻ lưới
ax.set_xticks(np.arange(-.5, N, 1), minor=True)
ax.set_yticks(np.arange(-.5, N, 1), minor=True)
ax.grid(which="minor", color="#111827", linestyle='-', linewidth=0.8)
ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)


# Nhãn A–J, 1–10 (có thể bỏ nếu không cần)
ax.set_xticks(np.arange(N)); ax.set_yticks(np.arange(N))
ax.set_xticklabels([chr(ord('A') + i) for i in range(N)])
ax.set_yticklabels([str(i + 1) for i in range(N)])
for t in ax.xaxis.get_major_ticks():
    t.tick1line.set_visible(False); t.tick2line.set_visible(False)
for t in ax.yaxis.get_major_ticks():
    t.tick1line.set_visible(False); t.tick2line.set_visible(False)


# Chú giải
legend = [
    Patch(facecolor=colors[1], edgecolor='black', label='Trống'),
    Patch(facecolor=colors[2], edgecolor='black', label='Trúng'),
    Patch(facecolor=colors[0], edgecolor='black', label='Trượt'),
]
ax.legend(handles=legend, loc='upper right', frameon=True, title='Ký hiệu')


ax.set_title("Battleship Board 10x10")
plt.tight_layout()
plt.show()




