# FILE: gui_game.py
# PHIÊN BẢN HOÀN CHỈNH - TÍCH HỢP ÂM THANH

import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk

# *** THÊM IMPORT PYGAME ***
import pygame

from logic_game import GameState, CellState, Ship, Board, FLEET_CONFIG
from ai_blind import BlindAI
from ai_heuristic import HeuristicAI
from ai_hybrid import HybridAI

N = 10
CELL_SIZE = 40 
COLORS = {
    "water": "#1e40af", "ship_deck": "#6b7280", "ship_gun": "#374151",
    "hit": "#ef4444", "miss": "#3b82f6", "sunk": "#111827",
    "preview_ok": "#22c55e", "preview_err": "#f97316",
    "border": "#9ca3af"
}

class BattleshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚓ Battleship - Canvas Edition")
        self.root.configure(bg="#0c4a6e")
        self.root.withdraw()
        
        # --- CÁC BIẾN TRẠNG THÁI ---
        self.game, self.ai = None, None
        self.selected_ship, self.placement_orientation = None, "horizontal"
        self.shipyard_widgets, self.preview_coords = {}, []
        
        # *** KHỞI TẠO HỆ THỐNG ÂM THANH ***
        self._init_sounds()
        
        self.show_difficulty_selection()
        
    def _init_sounds(self):
        """Tải tất cả các file âm thanh vào bộ nhớ."""
        try:
            pygame.mixer.init()
            # Tải hiệu ứng âm thanh
            self.sounds = {
                'click': pygame.mixer.Sound("assets/click.wav"),
                'shot': pygame.mixer.Sound("assets/shot.wav"),
                'hit': pygame.mixer.Sound("assets/hit.wav"),
                'miss': pygame.mixer.Sound("assets/miss.wav"),
                'sunk': pygame.mixer.Sound("assets/sunk.wav"),
                'win': pygame.mixer.Sound("assets/win.wav"), # Âm thanh chiến thắng
                'lose': pygame.mixer.Sound("assets/lose.wav") # Âm thanh thua cuộc
            }
            # Tải và phát nhạc nền (lặp lại vô tận)
            pygame.mixer.music.load("assets/background_music.mp3")
            pygame.mixer.music.play(loops=-1) # loops=-1 nghĩa là lặp lại mãi mãi
            pygame.mixer.music.set_volume(0.3) # Giảm âm lượng nhạc nền
        except pygame.error as e:
            print(f"Cảnh báo: Không thể tải file âm thanh. Game sẽ không có tiếng. Lỗi: {e}")
            self.sounds = None

    def play_sound(self, name):
        """Hàm tiện ích để phát một hiệu ứng âm thanh."""
        if self.sounds and name in self.sounds:
            self.sounds[name].play()
        
    def show_difficulty_selection(self):
        # ... (Hàm này giữ nguyên như cũ, chỉ thêm âm thanh cho nút)
        self.difficulty_window = tk.Toplevel(self.root)
        self.difficulty_window.title("Chọn Độ Khó")
        self.difficulty_window.geometry("800x600")
        self.difficulty_window.resizable(False, False)

        try:
            bg_image_pil = Image.open("images/tai.jpg")
            bg_image_pil = bg_image_pil.resize((800, 600), Image.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(bg_image_pil)
            bg_label = tk.Label(self.difficulty_window, image=self.bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except FileNotFoundError:
            self.difficulty_window.configure(bg="#1f2937")

        title_frame = tk.Frame(self.difficulty_window, bg="black")
        title_frame.pack(pady=(80, 40))
        title_label = tk.Label(title_frame, text="CHỌN ĐỘ KHÓ", font=("Arial Black", 36, "bold"), fg="white", bg="black", padx=20, pady=5)
        title_label.pack()

        btn_font = ("Arial", 16, "bold"); btn_width = 20
        
        def on_enter(e): e.widget['background'] = '#fde047'
        def on_leave_easy(e): e.widget['background'] = '#facc15'
        def on_leave_other(e): e.widget['background'] = '#f3f4f6'
        
        # Hàm chọn cấp độ có kèm âm thanh
        def select_difficulty(level):
            self.play_sound('click')
            self.start_setup(level)

        easy_btn = tk.Button(self.difficulty_window, text="DỄ", font=btn_font, width=btn_width, bg="#facc15", fg="black", relief="flat", command=lambda: select_difficulty("1"))
        easy_btn.pack(pady=15); easy_btn.bind("<Enter>", on_enter); easy_btn.bind("<Leave>", on_leave_easy)

        medium_btn = tk.Button(self.difficulty_window, text="TRUNG BÌNH", font=btn_font, width=btn_width, bg="#f3f4f6", fg="black", relief="flat", command=lambda: select_difficulty("2"))
        medium_btn.pack(pady=15); medium_btn.bind("<Enter>", on_enter); medium_btn.bind("<Leave>", on_leave_other)

        hard_btn = tk.Button(self.difficulty_window, text="KHÓ", font=btn_font, width=btn_width, bg="#f3f4f6", fg="black", relief="flat", command=lambda: select_difficulty("3"))
        hard_btn.pack(pady=15); hard_btn.bind("<Enter>", on_enter); hard_btn.bind("<Leave>", on_leave_other)
        
        self.difficulty_window.protocol("WM_DELETE_WINDOW", self.root.destroy)

    # --- Các hàm logic khác được thêm âm thanh ---
    def on_board_click(self, r, c):
        self.play_sound('click') # Âm thanh khi click lên bản đồ
        # ... (phần code còn lại của hàm giữ nguyên)
        if not self.game or self.game.ai_board is not None: return
        if self.selected_ship:
            if self.game.player_board.place_ship(self.selected_ship, r, c, self.placement_orientation):
                self.shipyard_widgets[self.selected_ship.name].destroy()
                self.selected_ship = None
                self.update_boards()
                if all(s.coordinates for s in self.game.player_fleet):
                    self.status_label.config(text="Đã đặt xong! Nhấn Ready để bắt đầu.")
                    self.ready_button.config(state="normal", bg="#4f46e5")
                else: self.status_label.config(text="Đặt tàu thành công! Chọn tàu tiếp theo.")
            else: messagebox.showerror("Lỗi", "Không thể đặt tàu tại đây.")
        else:
            ship_to_edit = self.game.player_board.find_ship_at(r, c)
            if ship_to_edit:
                self.game.player_board.remove_ship(ship_to_edit)
                self._populate_shipyard()
                self.select_ship(ship_to_edit)
                self.update_boards()
                self.ready_button.config(state="disabled", bg="#4b5563")
                self.status_label.config(text=f"Đang sửa {ship_to_edit.name}. Hãy đặt lại.")

    def select_ship(self, ship):
        self.play_sound('click') # Âm thanh khi chọn tàu
        # ... (phần code còn lại của hàm giữ nguyên)
        if self.selected_ship and self.selected_ship.name in self.shipyard_widgets:
             self.shipyard_widgets[self.selected_ship.name].config(relief="flat", bg="#374151")
        self.selected_ship = ship
        self.shipyard_widgets[ship.name].config(relief="solid", bg="#4f46e5")
        self.status_label.config(text=f"Đang đặt {ship.name}. Chuột phải để xoay.")
    
    def player_shoot(self, r, c):
        if not self.game or self.game.game_over or self.selected_ship or self.game.ai_board is None or self.game.current_turn != "Player": return
        
        self.play_sound('shot') # Âm thanh bắn
        result, ship = self.game.player_shot(r, c)
        
        # Phát âm thanh kết quả
        if result in ["Hit", "Sunk"]: self.play_sound('hit')
        elif result == "Miss": self.play_sound('miss')
        
        self.update_boards()
        
        if result == "Win":
            self.play_sound('win')
            self.status_label.config(text="🎉 Bạn thắng!"); messagebox.showinfo("Game Over", "Bạn đã thắng!")
        elif result == "Sunk":
            self.play_sound('sunk') # Âm thanh chìm tàu
            self.status_label.config(text=f"Bạn: {result}! Bắn tiếp.")
        elif result == "Hit":
            self.status_label.config(text=f"Bạn: {result}! Bắn tiếp.")
        elif result == "Miss":
            self.status_label.config(text="Bạn: Miss! Lượt của AI..."); self.root.after(500, self.ai_turn)
        elif result == "Already_Shot":
            self.status_label.config(text="Ô này đã bắn rồi!")

    def ai_turn(self):
        if not self.game or self.game.game_over: return
        
        self.play_sound('shot') # AI cũng có âm thanh bắn
        result, ship, move = self.game.ai_shot(self.ai)
        
        # Phát âm thanh kết quả
        if result in ["Hit", "Sunk"]: self.play_sound('hit')
        elif result == "Miss": self.play_sound('miss')
        
        ai_mode = getattr(self.ai, "mode", "blind").capitalize()
        self.ai_strategy_label.config(text=f"AI Strategy: {ai_mode} Mode")
        self.update_boards()
        
        if result == "Win":
            self.play_sound('lose')
            self.status_label.config(text=f"🤖 AI thắng!"); messagebox.showinfo("Game Over", "AI đã thắng.")
        elif result == "Sunk":
            self.play_sound('sunk')
            self.status_label.config(text=f"AI ({ai_mode}): {result}! AI bắn tiếp."); self.root.after(500, self.ai_turn)
        elif result == "Hit":
            self.status_label.config(text=f"AI ({ai_mode}): {result}! AI bắn tiếp."); self.root.after(500, self.ai_turn)
        elif result == "Miss":
            self.status_label.config(text=f"AI ({ai_mode}): Miss! Lượt của bạn.")
        elif result == "AI_Error":
             self.status_label.config(text=f"AI lỗi, chuyển lượt.")

    # ... (Các hàm còn lại không cần sửa)
    def setup_main_window(self):
        for widget in self.root.winfo_children(): widget.destroy()
        main_frame = tk.Frame(self.root, bg="#0c4a6e"); main_frame.pack(pady=10, padx=20, fill="x", expand=True)
        player_column = tk.Frame(main_frame, bg="#0c4a6e"); player_column.grid(row=0, column=0, sticky="ns", padx=10)
        player_frame = tk.LabelFrame(player_column, text="🧑 Tàu của bạn", font=("Arial", 10, "bold"), fg="white", bg="#0c4a6e", bd=0); player_frame.pack()
        self.player_canvas = self._create_board(player_frame, is_player_board=True)
        self.shipyard_frame = tk.LabelFrame(player_column, text="Xưởng Tàu", font=("Arial", 10, "bold"), fg="white", bg="#1e3a8a", padx=10, pady=10); self.shipyard_frame.pack(pady=10, fill="x")
        ai_column = tk.Frame(main_frame, bg="#0c4a6e"); ai_column.grid(row=0, column=1, sticky="ns", padx=10)
        ai_frame = tk.LabelFrame(ai_column, text="🤖 Tàu đối thủ", font=("Arial", 10, "bold"), fg="white", bg="#0c4a6e", bd=0); ai_frame.pack()
        self.ai_canvas = self._create_board(ai_frame, is_ai_board=True)
        bottom_frame = tk.Frame(self.root, bg="#0c4a6e"); bottom_frame.pack(pady=10, fill="x")
        self.status_label = tk.Label(bottom_frame, text="...", font=("Arial", 12, "bold"), bg="#1e3a8a", fg="white", height=2); self.status_label.pack(pady=5, fill="x", padx=20)
        self.ai_strategy_label = tk.Label(bottom_frame, text="AI Strategy: None", font=("Arial", 10), fg="cyan", bg="#0c4a6e"); self.ai_strategy_label.pack(pady=2)
        control_frame = tk.Frame(bottom_frame, bg="#0c4a6e"); control_frame.pack(pady=10)
        tk.Button(control_frame, text="🔄 Reset", width=10, command=self.reset_game, bg="#f59e0b", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=5, pady=5).grid(row=0, column=0, padx=5)
        tk.Button(control_frame, text="❌ Quit", width=10, command=self.root.quit, bg="#ef4444", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=5, pady=5).grid(row=0, column=1, padx=5)
        self.root.bind("<Button-3>", self.rotate_ship)
    def start_setup(self, difficulty):
        self.difficulty_window.destroy()
        self.setup_main_window()
        self.root.deiconify()
        self.game = GameState()
        if difficulty == "1": self.ai = BlindAI(board_size=10); self.ai_strategy_label.config(text="AI Strategy: Easy (Blind)")
        elif difficulty == "2": self.ai = HeuristicAI(board_size=10); self.ai_strategy_label.config(text="AI Strategy: Medium (Heuristic)")
        elif difficulty == "3": self.ai = HybridAI(board_size=10); self.ai_strategy_label.config(text="AI Strategy: Hard (Hybrid)")
        self._populate_shipyard(); self.status_label.config(text="Click một tàu từ Xưởng Tàu để đặt.")
    def reset_game(self):
        pygame.mixer.music.stop()
        self.root.withdraw()
        self.show_difficulty_selection()
    def _create_board(self, parent, is_player_board=False, is_ai_board=False):
        canvases = []
        for r in range(N):
            row_canvases = []
            for c in range(N):
                canvas = tk.Canvas(parent, width=CELL_SIZE, height=CELL_SIZE, bg=COLORS['water'], highlightthickness=1, highlightbackground=COLORS['border'])
                if is_player_board:
                    canvas.bind("<Enter>", lambda e, r=r, c=c: self.on_board_hover(r, c)); canvas.bind("<Leave>", lambda e: self.clear_preview())
                    canvas.bind("<Button-1>", lambda e, r=r, c=c: self.on_board_click(r, c))
                if is_ai_board: canvas.bind("<Button-1>", lambda e, r=r, c=c: self.player_shoot(r, c))
                canvas.grid(row=r, column=c); row_canvases.append(canvas)
            canvases.append(row_canvases)
        return canvases
    def update_boards(self):
        if not self.game: return
        self._draw_board(self.player_canvas, self.game.player_board, show_ships=True)
        if self.game.ai_board: self._draw_board(self.ai_canvas, self.game.player_tracking_board, show_ships=False)
    def _draw_board(self, canvases, board, show_ships):
        for r in range(N):
            for c in range(N):
                canvas = canvases[r][c]
                canvas.delete("all")
                canvas.create_rectangle(0, 0, CELL_SIZE, CELL_SIZE, fill=COLORS['water'], outline=COLORS['border'])
                cell_state = board.grid[r][c]
                if show_ships and cell_state == CellState.SHIP:
                    ship = board.find_ship_at(r, c)
                    if ship: self._draw_ship_part(canvas, ship, ship.coordinates.index((r, c)))
                if cell_state == CellState.MISS: canvas.create_oval(10, 10, CELL_SIZE-10, CELL_SIZE-10, fill=COLORS['miss'], outline='white')
                elif cell_state == CellState.HIT: canvas.create_oval(5, 5, CELL_SIZE-5, CELL_SIZE-5, fill=COLORS['hit'], outline='orange')
                elif cell_state == CellState.SUNK_SHIP:
                    canvas.create_rectangle(0, 0, CELL_SIZE, CELL_SIZE, fill=COLORS['sunk'], outline=COLORS['border'])
                    canvas.create_text(CELL_SIZE/2, CELL_SIZE/2, text="💀", font=("Arial", 15), fill="white")
    def _draw_ship_part(self, canvas, ship, part_index):
        if ship.orientation == 'horizontal':
            canvas.create_rectangle(0, 5, CELL_SIZE, CELL_SIZE-5, fill=COLORS['ship_deck'], outline=COLORS['ship_gun'])
            if part_index % 2 == 1: canvas.create_rectangle(10, 12, CELL_SIZE-10, CELL_SIZE-12, fill=COLORS['ship_gun'])
        else:
            canvas.create_rectangle(5, 0, CELL_SIZE-5, CELL_SIZE, fill=COLORS['ship_deck'], outline=COLORS['ship_gun'])
            if part_index % 2 == 1: canvas.create_rectangle(12, 10, CELL_SIZE-12, CELL_SIZE-10, fill=COLORS['ship_gun'])
    def _populate_shipyard(self):
        for widget in self.shipyard_frame.winfo_children(): widget.destroy()
        self.shipyard_widgets.clear()
        ships_to_show = [s for s in self.game.player_fleet if not s.coordinates]
        for ship in ships_to_show:
            ship_text = f"{ship.name} ({'● ' * ship.size})"
            lbl = tk.Label(self.shipyard_frame, text=ship_text, fg="white", bg="#374151", padx=5, pady=5, cursor="hand2")
            lbl.pack(pady=2, fill="x"); lbl.bind("<Button-1>", lambda e, s=ship: self.select_ship(s))
            self.shipyard_widgets[ship.name] = lbl
        self.ready_button = tk.Button(self.shipyard_frame, text="🚀 Ready", width=10, command=self.start_game, bg="#4b5563", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=5, pady=5, state="disabled")
        self.ready_button.pack(pady=10)
    def on_board_hover(self, r, c):
        if not self.selected_ship: return
        self.clear_preview()
        is_placeable = self.game.player_board._is_valid_placement(self.selected_ship.size, r, c, self.placement_orientation)
        color = COLORS["preview_ok"] if is_placeable else COLORS["preview_err"]
        for i in range(self.selected_ship.size):
            row, col = r + (i if self.placement_orientation == "vertical" else 0), c + (i if self.placement_orientation == "horizontal" else 0)
            if 0 <= row < N and 0 <= col < N:
                canvas = self.player_canvas[row][col]
                rect = canvas.create_rectangle(0,0,CELL_SIZE,CELL_SIZE, fill=color, outline=color)
                self.preview_coords.append((canvas, rect))
    def clear_preview(self):
        for canvas, rect in self.preview_coords: canvas.delete(rect)
        self.preview_coords = []
    def rotate_ship(self, event):
        if not self.selected_ship: return
        self.placement_orientation = "vertical" if self.placement_orientation == "horizontal" else "horizontal"
        x, y = self.root.winfo_pointerxy(); widget = self.root.winfo_containing(x, y)
        if widget and hasattr(widget, 'grid_info'):
            info = widget.grid_info()
            if 'row' in info and 'column' in info: self.on_board_hover(info['row'], info['column'])
    def start_game(self):
        self.play_sound('click')
        self.selected_ship = None; self.clear_preview()
        self.ready_button.config(state="disabled", bg="#4b5563")
        self.shipyard_frame.destroy()
        self.game.start_battle()
        self.update_boards()
        self.status_label.config(text="Trận chiến bắt đầu! Đến lượt bạn bắn!")

if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()