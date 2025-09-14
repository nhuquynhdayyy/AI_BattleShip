# gui_game.py
import tkinter as tk
from tkinter import messagebox
from logic_game import GameState, CellState, Ship, Board, FLEET_CONFIG
from ai_hybrid import HybridAI

N = 10

# Dark theme + màu
COLORS = {
    CellState.EMPTY: "#1f2937",
    CellState.SHIP: "#6b7280",
    CellState.HIT:  "#ef4444",
    CellState.MISS: "#3b82f6",
    CellState.SUNK_SHIP: "#000000",
    "preview_ok": "#22c55e",
    "preview_err": "#f97316",
    "border_default": "#374151",
    "border_sunk": "#ffffff",
    "btn_ready_enabled": "#4f46e5",  # Indigo
    "btn_disabled": "#a0aec0",       # Cool Gray
}

class BattleshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚓ Battleship Player vs AI")
        self.root.configure(bg="#111827")

        self.game = None
        self.ai = None
        
        self.ships_to_place = []
        self.selected_ship = None
        self.placement_orientation = "horizontal"
        self.shipyard_widgets = {}
        self.preview_coords = []

        # === Cấu trúc giao diện ===
        main_frame = tk.Frame(root, bg="#111827")
        main_frame.pack(pady=10, padx=20, fill="x", expand=True)

        player_column = tk.Frame(main_frame, bg="#111827")
        player_column.grid(row=0, column=0, sticky="ns", padx=10)

        player_frame = tk.LabelFrame(player_column, text="🧑 Tàu của bạn", font=("Arial", 10, "bold"), fg="white", bg="#1f2937", padx=5, pady=5)
        player_frame.pack()
        self.player_buttons = self._create_board(player_frame, is_player_board=True)
        
        self.shipyard_frame = tk.LabelFrame(player_column, text="Xưởng Tàu", font=("Arial", 10, "bold"), fg="white", bg="#1f2937", padx=10, pady=10)
        self.shipyard_frame.pack(pady=10, fill="x")

        ai_column = tk.Frame(main_frame, bg="#111827")
        ai_column.grid(row=0, column=1, sticky="ns", padx=10)
        
        ai_frame = tk.LabelFrame(ai_column, text="🤖 Tàu đối thủ", font=("Arial", 10, "bold"), fg="white", bg="#1f2937", padx=5, pady=5)
        ai_frame.pack()
        self.ai_buttons = self._create_board(ai_frame, is_ai_board=True)

        bottom_frame = tk.Frame(root, bg="#111827")
        bottom_frame.pack(pady=10, fill="x")

        self.status_label = tk.Label(bottom_frame, text="Welcome! Click 'Start' to begin.", font=("Arial", 12, "bold"), bg="#1e3a8a", fg="white", height=2)
        self.status_label.pack(pady=5, fill="x", padx=20)
        
        self.ai_strategy_label = tk.Label(bottom_frame, text="AI Strategy: None", font=("Arial", 10), fg="cyan", bg="#111827")
        self.ai_strategy_label.pack(pady=2)

        control_frame = tk.Frame(bottom_frame, bg="#111827")
        control_frame.pack(pady=10)
        
        # --- Bổ sung nút Ready ---
        btn_defs = [
            ("▶️ Start", self.start_setup, "#10b981"),
            ("🚀 Ready", self.start_game, COLORS["btn_disabled"]),
            ("🔄 Reset", self.reset_game, "#f59e0b"),
            ("❌ Quit", root.quit, "#ef4444")
        ]
        
        self.start_button = tk.Button(control_frame, text=btn_defs[0][0], width=10, command=btn_defs[0][1], bg=btn_defs[0][2], fg="white", font=("Arial", 10, "bold"), relief="flat", padx=5, pady=5)
        self.start_button.grid(row=0, column=0, padx=5)

        self.ready_button = tk.Button(control_frame, text=btn_defs[1][0], width=10, command=btn_defs[1][1], bg=btn_defs[1][2], fg="white", font=("Arial", 10, "bold"), relief="flat", padx=5, pady=5, state="disabled")
        self.ready_button.grid(row=0, column=1, padx=5)
        
        tk.Button(control_frame, text=btn_defs[2][0], width=10, command=btn_defs[2][1], bg=btn_defs[2][2], fg="white", font=("Arial", 10, "bold"), relief="flat", padx=5, pady=5).grid(row=0, column=2, padx=5)
        tk.Button(control_frame, text=btn_defs[3][0], width=10, command=btn_defs[3][1], bg=btn_defs[3][2], fg="white", font=("Arial", 10, "bold"), relief="flat", padx=5, pady=5).grid(row=0, column=3, padx=5)

        self.root.bind("<Button-3>", self.rotate_ship)

    def _create_board(self, parent, is_player_board=False, is_ai_board=False):
        buttons = []
        for r in range(N):
            row_buttons = []
            for c in range(N):
                btn = tk.Button(parent, text=" ", width=2, height=1, bg=COLORS[CellState.EMPTY], relief="solid", bd=1, highlightthickness=1, highlightbackground=COLORS["border_default"])
                if is_player_board:
                    btn.bind("<Enter>", lambda e, r=r, c=c: self.on_board_hover(r, c))
                    btn.bind("<Leave>", lambda e: self.clear_preview())
                    btn.config(command=lambda r=r, c=c: self.on_board_click(r, c))
                if is_ai_board:
                    btn.config(command=lambda r=r, c=c: self.player_shoot(r, c))
                btn.grid(row=r, column=c)
                row_buttons.append(btn)
            buttons.append(row_buttons)
        return buttons

    def start_setup(self):
        self.reset_game()
        self.game = GameState()
        self.ai = HybridAI(board_size=10, ships=[s['size'] for s in FLEET_CONFIG])
        self.ships_to_place = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self._populate_shipyard()
        self.status_label.config(text="Click a ship from the Dock to place it.")
        self.start_button.config(state="disabled") # Không cho nhấn Start lần nữa

    def _populate_shipyard(self):
        for widget in self.shipyard_frame.winfo_children():
            widget.destroy()
        self.shipyard_widgets.clear()
        for ship in self.ships_to_place:
            ship_text = f"{ship.name} ({'● ' * ship.size})"
            lbl = tk.Label(self.shipyard_frame, text=ship_text, fg="white", bg="#374151", padx=5, pady=5, cursor="hand2")
            lbl.pack(pady=2, fill="x")
            lbl.bind("<Button-1>", lambda e, s=ship: self.select_ship(s))
            self.shipyard_widgets[ship.name] = lbl
            
    def select_ship(self, ship):
        if self.selected_ship:
             self.shipyard_widgets[self.selected_ship.name].config(relief="flat", bg="#374151")
        self.selected_ship = ship
        widget = self.shipyard_widgets[ship.name]
        widget.config(relief="solid", bg=COLORS["btn_ready_enabled"])
        self.status_label.config(text=f"Placing {ship.name}. Right-click to rotate.")
    
    def on_board_hover(self, r, c):
        if not self.selected_ship: return
        self.clear_preview()
        size = self.selected_ship.size
        coords, valid = [], True
        for i in range(size):
            row, col = r + (i if self.placement_orientation == "vertical" else 0), c + (i if self.placement_orientation == "horizontal" else 0)
            if not (0 <= row < N and 0 <= col < N):
                valid = False; break
            coords.append((row, col))
        is_placeable = self.game.player_board._is_valid_placement(size, r, c, self.placement_orientation)
        color = COLORS["preview_ok"] if is_placeable and valid else COLORS["preview_err"]
        if valid:
            for R, C in coords: self.player_buttons[R][C].config(bg=color)
            self.preview_coords = coords

    def clear_preview(self):
        if not self.preview_coords: return
        for r, c in self.preview_coords:
            actual_cell_state = self.game.player_board.grid[r][c]
            bg_color = COLORS[CellState.SHIP] if actual_cell_state == CellState.SHIP else COLORS[CellState.EMPTY]
            self.player_buttons[r][c].config(bg=bg_color)
        self.preview_coords = []

    def on_board_click(self, r, c):
        # Không cho click nếu game đã bắt đầu
        if self.game.ai_board is not None: return

        # Trường hợp 1: Đang cầm tàu để đặt
        if self.selected_ship:
            placed = self.game.player_board.place_ship(self.selected_ship, r, c, self.placement_orientation)
            if placed:
                self.shipyard_widgets[self.selected_ship.name].destroy()
                self.ships_to_place.remove(self.selected_ship)
                self.selected_ship = None
                self.update_boards()
                
                # Nếu đặt xong tàu cuối cùng -> Kích hoạt nút Ready
                if not self.ships_to_place:
                    self.status_label.config(text="All ships placed! Rearrange or click Ready.")
                    self.ready_button.config(state="normal", bg=COLORS["btn_ready_enabled"])
                else:
                    self.status_label.config(text="Ship placed! Select the next ship.")
            else:
                messagebox.showerror("Invalid Placement", "Cannot place ship here.")
        
        # Trường hợp 2: Nhấc tàu lên để sửa
        else:
            ship_to_edit = self.game.player_board.find_ship_at(r, c)
            if ship_to_edit:
                self.game.player_board.remove_ship(ship_to_edit)
                self.ships_to_place.append(ship_to_edit)
                self._populate_shipyard()
                self.select_ship(ship_to_edit)
                self.update_boards()
                self.on_board_hover(r, c)
                
                # Vô hiệu hóa nút Ready vì có tàu bị nhấc ra
                self.ready_button.config(state="disabled", bg=COLORS["btn_disabled"])
                self.status_label.config(text=f"Editing {ship_to_edit.name}. Place it again.")

    def rotate_ship(self, event):
        if not self.selected_ship: return
        self.placement_orientation = "vertical" if self.placement_orientation == "horizontal" else "horizontal"
        x, y = self.root.winfo_pointerxy()
        widget = self.root.winfo_containing(x, y)
        if widget and hasattr(widget, 'grid_info'):
            info = widget.grid_info()
            if 'row' in info and 'column' in info:
                self.on_board_hover(info['row'], info['column'])

    def start_game(self):
        self.selected_ship = None
        self.clear_preview()
        
        # Vô hiệu hóa các nút điều khiển giai đoạn setup
        self.ready_button.config(state="disabled", bg=COLORS["btn_disabled"])
        for widget in self.shipyard_frame.winfo_children():
            widget.config(state="disabled", cursor="")

        # Bắt đầu game
        self.game.ai_board = Board() # Tạo board AI là dấu hiệu game đã bắt đầu
        self.game.ai_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.game._ai_auto_place_ships()
        self.update_boards()
        self.status_label.config(text="Battle starts! Your turn to shoot!")

    def reset_game(self):
        if self.game: self.game.ai_board = None
        self.ships_to_place = []
        self.selected_ship = None
        self.preview_coords = []
        for board in [self.player_buttons, self.ai_buttons]:
            for row in board:
                for btn in row:
                    btn.config(bg=COLORS[CellState.EMPTY], text=" ", highlightbackground=COLORS["border_default"])
        
        self._populate_shipyard()
        self.status_label.config(text="Game reset. Click Start to place ships.")
        self.ai_strategy_label.config(text="AI Strategy: None")
        
        # Reset trạng thái các nút
        self.start_button.config(state="normal")
        self.ready_button.config(state="disabled", bg=COLORS["btn_disabled"])

    # ... các hàm update_boards, player_shoot, ai_turn giữ nguyên như cũ ...
    def update_boards(self):
        if not self.game: return
        # Player board
        for r in range(N):
            for c in range(N):
                cell = self.game.player_board.grid[r][c]
                bg, text, border = COLORS[CellState.EMPTY], " ", COLORS["border_default"]
                if cell == CellState.SHIP: bg = COLORS[CellState.SHIP]
                elif cell == CellState.MISS: bg = COLORS[CellState.MISS]
                elif cell == CellState.HIT: bg, text = COLORS[CellState.HIT], "💥"
                elif cell == CellState.SUNK_SHIP: bg, text, border = COLORS[CellState.SUNK_SHIP], "💀", COLORS["border_sunk"]
                self.player_buttons[r][c].config(bg=bg, text=text, fg="white", highlightbackground=border)
        # AI tracking board
        for r in range(N):
            for c in range(N):
                cell = self.game.player_tracking_board.grid[r][c]
                bg, text, border = COLORS[CellState.EMPTY], " ", COLORS["border_default"]
                if cell == CellState.MISS: bg = COLORS[CellState.MISS]
                elif cell == CellState.HIT: bg, text = COLORS[CellState.HIT], "💥"
                elif cell == CellState.SUNK_SHIP: bg, text, border = COLORS[CellState.SUNK_SHIP], "💀", COLORS["border_sunk"]
                self.ai_buttons[r][c].config(bg=bg, text=text, fg="white", highlightbackground=border)

    def player_shoot(self, r, c):
        if not self.game or self.game.game_over or self.selected_ship or self.game.ai_board is None: return
        if self.game.current_turn != "Player":
            self.status_label.config(text="Not your turn!")
            return

        result = self.game.player_shot(r, c)
        self.update_boards()
        if result == "Win":
            self.status_label.config(text="🎉 Player wins!")
            messagebox.showinfo("Game Over", "Congratulations, you won!")
            return
        elif result in ["Miss", "Hit", "Sunk"]:
            self.status_label.config(text=f"Player: {result}")
            if result == "Miss":
                self.root.after(1000, self.ai_turn)
        elif result in ["Already_Shot", "Invalid"]:
            self.status_label.config(text="You already shot there!")

    def ai_turn(self):
        if not self.game or self.game.game_over: return
        
        result = self.game.ai_shot(self.ai)
        self.update_boards()
        ai_mode = getattr(self.ai, "mode", "blind").capitalize()
        self.ai_strategy_label.config(text=f"AI Strategy: {ai_mode}")

        if self.game.game_over and self.game.winner == "AI":
            self.status_label.config(text=f"🤖 AI wins! (Strategy: {ai_mode})")
            messagebox.showinfo("Game Over", "The AI has won.")
        elif result == "Win":
            self.status_label.config(text=f"🤖 AI wins! (Strategy: {ai_mode})")
            messagebox.showinfo("Game Over", "The AI has won.")
        else:
            self.status_label.config(text=f"AI ({ai_mode}): {result}")
            if result in ["Hit", "Sunk"]:
                self.root.after(1000, self.ai_turn)


if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()