# FILE: gui_game.py
# PHIÊN BẢN GIAO DIỆN THÂN THIỆN

import tkinter as tk
from tkinter import messagebox, simpledialog, font as tkFont
import pygame  # Thư viện dùng cho âm thanh

from logic_game import (GameState, CellState, Ship, Board, FLEET_CONFIG, 
                        ai_auto_place_ships, display_fleet_status, GameLogger)
from ai_blind import BlindAI

# --- CÁC HẰNG SỐ GIAO DIỆN ---
N = 10
COLORS = {
    CellState.EMPTY: "lightblue",
    CellState.SHIP: "#607D8B",  # Xám xanh
    CellState.HIT: "#E53935",   # Đỏ đậm
    CellState.MISS: "#00BFFF",  # Xanh dương sáng
    CellState.SUNK_SHIP: "#212121" # Đen
}
FONT_TITLE = ("Segoe UI", 10, "bold")
FONT_STATUS = ("Segoe UI", 13, "bold")
FONT_FLEET = ("Consolas", 10) # Dùng font mono-space để căn chỉnh đẹp


class BattleshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Battleship - Trận Chiến Biển Khơi")
        self.root.configure(bg="#ECEFF1") # Màu nền chính

        self.game = None
        self.ai = None
        self.placing_ships = []
        self.current_ship = None
        self.player_tracking_board = Board()
        self.logger = None

        # --- KHỞI TẠO HỆ THỐNG ÂM THANH ---
        pygame.mixer.init()
        # try:
        #     self.sound_shot = pygame.mixer.Sound("assets/shot.wav")
        #     self.sound_hit = pygame.mixer.Sound("assets/hit.wav")
        #     self.sound_miss = pygame.mixer.Sound("assets/miss.wav")
        #     self.sound_sunk = pygame.mixer.Sound("assets/sunk.wav")
        # except pygame.error as e:
        #     print(f"Cảnh báo: Không thể tải file âm thanh. Game sẽ không có tiếng. Lỗi: {e}")
        self.sound_shot = self.sound_hit = self.sound_miss = self.sound_sunk = None

        # --- BỐ CỤC GIAO DIỆN ---
        main_frame = tk.Frame(root, bg="#ECEFF1")
        main_frame.pack(pady=10, padx=10)

        # Cột 0: Player
        player_column = tk.Frame(main_frame, bg="#ECEFF1")
        player_column.grid(row=0, column=0, padx=10)
        player_frame = tk.LabelFrame(player_column, text="Bản Đồ Của Bạn", font=FONT_TITLE, padx=10, pady=10)
        player_frame.pack()
        self.player_buttons = self._create_board(player_frame, is_player_board=True)
        
        # Lựa chọn hướng đặt tàu (thân thiện hơn)
        orientation_frame = tk.LabelFrame(player_column, text="Chọn Hướng Đặt Tàu", font=FONT_TITLE, padx=10, pady=5)
        orientation_frame.pack(pady=10, fill="x")
        self.orientation_var = tk.StringVar(value="horizontal")
        tk.Radiobutton(orientation_frame, text="Ngang", variable=self.orientation_var, value="horizontal", font=("Segoe UI", 10)).pack(side="left", expand=True)
        tk.Radiobutton(orientation_frame, text="Dọc", variable=self.orientation_var, value="vertical", font=("Segoe UI", 10)).pack(side="left", expand=True)

        # Cột 1: AI
        ai_frame = tk.LabelFrame(main_frame, text="Bản Đồ Đối Phương", font=FONT_TITLE, padx=10, pady=10)
        ai_frame.grid(row=0, column=1, padx=10)
        self.ai_buttons = self._create_board(ai_frame, is_ai_board=True)

        # Cột 2: Trạng thái
        status_frame = tk.LabelFrame(main_frame, text="Trạng Thái Hạm Đội", font=FONT_TITLE, padx=10, pady=10)
        status_frame.grid(row=0, column=2, padx=10, sticky="ns")
        self.player_fleet_label = tk.Label(status_frame, text="-- Hạm đội của bạn --", justify=tk.LEFT, font=FONT_FLEET)
        self.player_fleet_label.pack(anchor="w", padx=5, pady=2)
        self.ai_fleet_label = tk.Label(status_frame, text="\n-- Hạm đội đối phương --", justify=tk.LEFT, font=FONT_FLEET)
        self.ai_fleet_label.pack(anchor="w", padx=5, pady=2)

        # Các nút điều khiển
        control_frame = tk.Frame(root, bg="#ECEFF1")
        control_frame.pack(pady=10)
        self.start_button = tk.Button(control_frame, text="Start", width=10, command=self.start_setup, font=("Segoe UI", 10, "bold"))
        self.start_button.grid(row=0, column=0, padx=5)
        tk.Button(control_frame, text="Reset", width=10, command=self.reset_game, font=("Segoe UI", 10)).grid(row=0, column=1, padx=5)
        tk.Button(control_frame, text="Quit",  width=10, command=root.quit, font=("Segoe UI", 10)).grid(row=0, column=2, padx=5)

        # Nhãn trạng thái chính
        self.status_label = tk.Label(root, text="Chào mừng! Nhấn Start để bắt đầu.", font=FONT_STATUS, bg="#ECEFF1")
        self.status_label.pack(pady=10, fill="x")

    def _create_board(self, parent, is_player_board=False, is_ai_board=False):
        buttons = []
        for r in range(N):
            row_buttons = []
            for c in range(N):
                btn = tk.Button(parent, text=" ", width=2, height=1, bg=COLORS[CellState.EMPTY], relief="raised", state="disabled")
                btn.grid(row=r, column=c)
                if is_player_board: btn.config(command=lambda r=r, c=c: self.place_ship_click(r, c))
                if is_ai_board: btn.config(command=lambda r=r, c=c: self.player_shoot(r, c))
                row_buttons.append(btn)
            buttons.append(row_buttons)
        return buttons

    def start_setup(self):
        self.reset_game()
        self.game = GameState()
        self.ai = BlindAI(board_size=10)
        self.logger = GameLogger()
        self.logger.log_event("Trò chơi bắt đầu. Người chơi đang đặt tàu.")
        
        self.placing_ships = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.current_ship = self.placing_ships.pop(0)
        self.status_label.config(text=f"Hãy đặt tàu: {self.current_ship.name} ({self.current_ship.size} ô)", fg="black")
        self.start_button.config(state="disabled")
        
        for r in range(N):
            for c in range(N):
                self.player_buttons[r][c].config(state="normal")

    def place_ship_click(self, r, c):
        if not self.current_ship: return
        orientation = self.orientation_var.get()
        ship_to_place = next(s for s in self.game.player_fleet if s.name == self.current_ship.name and not s.coordinates)
        
        if self.game.player_board.place_ship(ship_to_place, r, c, orientation):
            self.update_boards()
            if self.placing_ships:
                self.current_ship = self.placing_ships.pop(0)
                self.status_label.config(text=f"Hãy đặt tàu: {self.current_ship.name} ({self.current_ship.size} ô)")
            else:
                self.current_ship = None
                self.start_game()
        else:
            messagebox.showerror("Lỗi", "Vị trí không hợp lệ! Vui lòng chọn vị trí khác.")

    def start_game(self):
        self.status_label.config(text="AI đang đặt tàu...", fg="black")
        ai_auto_place_ships(self.game.ai_board, self.game.ai_fleet)
        self.logger.log_placements("Player", self.game.player_board)
        self.logger.log_placements("AI", self.game.ai_board)
        
        for r in range(N):
            for c in range(N):
                self.player_buttons[r][c].config(state="disabled")
                self.ai_buttons[r][c].config(state="normal")
        
        self.update_boards()
        self.update_status_display()
        self.status_label.config(text="Game đã bắt đầu! Đến lượt bạn.", fg="blue")

    def reset_game(self):
        self.game = None; self.ai = None; self.placing_ships = []; self.current_ship = None
        self.player_tracking_board = Board(); self.logger = None
        for board in [self.player_buttons, self.ai_buttons]:
            for row in board:
                for btn in row:
                    btn.config(bg=COLORS[CellState.EMPTY], text=" ", state="disabled")
        self.status_label.config(text="Game đã được reset. Nhấn Start để chơi lại.", fg="black")
        self.player_fleet_label.config(text="-- Hạm đội của bạn --")
        self.ai_fleet_label.config(text="\n-- Hạm đội đối phương --")
        self.start_button.config(state="normal")

    def update_boards(self):
        if not self.game: return
        for r in range(N):
            for c in range(N):
                self.player_buttons[r][c].config(bg=COLORS[self.game.player_board.grid[r][c]])
        for r in range(N):
            for c in range(N):
                self.ai_buttons[r][c].config(bg=COLORS[self.player_tracking_board.grid[r][c]])

    def update_status_display(self):
        if not self.game: return
        self.player_fleet_label.config(text="-- Hạm đội của bạn --\n" + display_fleet_status(self.game.player_fleet))
        self.ai_fleet_label.config(text="\n-- Hạm đội đối phương --\n" + display_fleet_status(self.game.ai_fleet))

    def play_sound(self, sound_object):
        if sound_object:
            sound_object.play()

    def player_shoot(self, r, c):
        if not self.game or self.game.winner or self.current_ship or self.game.current_turn != "Player":
            return
        
        self.play_sound(self.sound_shot)
        result, affected_ship = self.game.ai_board.receive_shot(r, c)
        if self.logger: self.logger.log_shot("Player", (r, c), result, affected_ship)

        if result == "Already_Shot":
            self.status_label.config(text="Bạn đã bắn vào ô này rồi! Chọn ô khác.", fg="#FF6F00") # Cam
            return

        if result == "Sunk": self.play_sound(self.sound_sunk)
        elif result == "Hit": self.play_sound(self.sound_hit)
        elif result == "Miss": self.play_sound(self.sound_miss)

        if result == "Sunk":
            for r_s, c_s in affected_ship.coordinates:
                self.player_tracking_board.grid[r_s][c_s] = CellState.SUNK_SHIP
        elif result == "Hit": self.player_tracking_board.grid[r][c] = CellState.HIT
        elif result == "Miss": self.player_tracking_board.grid[r][c] = CellState.MISS
        
        self.update_boards()
        self.update_status_display()

        if result in ["Sunk", "Hit"]:
            if result == "Sunk": self.status_label.config(text=f"BẮN CHÌM! Tàu {affected_ship.name} của địch đã bị hạ! Bạn được bắn tiếp.", fg="#4CAF50") # Xanh lá
            else: self.status_label.config(text="Bắn trúng! Bạn được bắn tiếp.", fg="#8BC34A") # Xanh lá nhạt
        elif result == "Miss":
            self.status_label.config(text="Bắn trượt! Đến lượt AI...", fg="black")
            self.game.switch_turn()
            self.root.after(1000, self.ai_turn)

        if self.game.check_game_over():
            self.end_game()

    def ai_turn(self):
        if not self.game or self.game.winner: return
        move = self.ai.get_move()
        if not move: return
        r, c = move
        result, affected_ship = self.game.player_board.receive_shot(r, c)
        if self.logger: self.logger.log_shot("AI", (r, c), result, affected_ship)
        
        if result == "Sunk": self.play_sound(self.sound_sunk)
        elif result == "Hit": self.play_sound(self.sound_hit)
        elif result == "Miss": self.play_sound(self.sound_miss)

        self.update_boards()
        self.update_status_display()

        if result in ["Sunk", "Hit"]:
            if result == "Sunk": self.status_label.config(text=f"BỊ BẮN CHÌM! Tàu {affected_ship.name} của bạn đã bị hạ! AI được bắn tiếp.", fg="#D32F2F") # Đỏ đậm
            else: self.status_label.config(text=f"AI bắn trúng tọa độ {chr(ord('A')+c)}{r+1}! AI được bắn tiếp.", fg="#F4511E") # Cam đậm
            self.root.after(1000, self.ai_turn)
        elif result == "Miss":
            self.status_label.config(text=f"AI bắn trượt! Đến lượt bạn.", fg="blue")
            self.game.switch_turn()

        if self.game.check_game_over():
            self.end_game()

    def end_game(self):
        for r in range(N):
            for c in range(N):
                self.player_buttons[r][c].config(state="disabled")
                self.ai_buttons[r][c].config(state="disabled")

        winner = self.game.winner
        if self.logger: self.logger.log_winner(winner)

        if winner == "Player":
            messagebox.showinfo("Kết thúc", "Chúc mừng! Bạn đã chiến thắng!")
            self.status_label.config(text="🎉 BẠN THẮNG! 🎉", fg="#1976D2") # Xanh đậm
        else:
            messagebox.showinfo("Kết thúc", "Bạn đã thua. Chúc may mắn lần sau!")
            self.status_label.config(text="🤖 BẠN THUA! 🤖", fg="#D32F2F") # Đỏ đậm

if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()