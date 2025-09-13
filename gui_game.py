# gui_game.py
import tkinter as tk
from tkinter import messagebox, simpledialog
from logic_game import GameState, CellState, Ship, Board, FLEET_CONFIG
from ai_hybrid import HybridAI


N = 10

# Dark theme + màu
COLORS = {
    CellState.EMPTY: "#1f2937",     # nền tối
    CellState.SHIP: "#1f2937",      # tàu Player: nền như trống, hiển thị ●
    CellState.HIT:  "#ef4444",      # đỏ khi bắn trúng
    CellState.MISS: "#3b82f6",      # xanh dương khi bắn trượt
    CellState.SUNK_SHIP: "#000000" # tím khi tàu chìm hẳn
}

class BattleshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚓ Battleship Player vs AI")

        self.game = None
        self.ai = None
        self.placing_ships = []     # danh sách tàu Player cần đặt
        self.current_ship = None    # tàu đang đặt

        root.configure(bg="#111827")  # dark background

        # Frames
        main_frame = tk.Frame(root, bg="#111827")
        main_frame.pack(pady=10)

        # Player board
        player_frame = tk.LabelFrame(main_frame, text="🧑 Tàu của bạn",
                                     font=("Arial", 10, "bold"), fg="white",
                                     bg="#1f2937", padx=5, pady=5)
        player_frame.grid(row=0, column=0, padx=20)
        self.player_buttons = self._create_board(player_frame, player_board=True)

        # AI board
        ai_frame = tk.LabelFrame(main_frame, text="🤖 Tàu đối thủ",
                                 font=("Arial", 10, "bold"), fg="white",
                                 bg="#1f2937", padx=5, pady=5)
        ai_frame.grid(row=0, column=1, padx=20)
        self.ai_buttons = self._create_board(ai_frame, ai_board=True)

        # Control buttons
        control_frame = tk.Frame(root, bg="#111827")
        control_frame.pack(pady=10)

        for i, (txt, cmd, color) in enumerate([
            ("▶️ Start", self.start_setup, "#10b981"),
            ("🔄 Reset", self.reset_game, "#f59e0b"),
            ("❌ Quit", root.quit, "#ef4444")
        ]):
            tk.Button(control_frame, text=txt, width=10, command=cmd,
                      bg=color, fg="white", font=("Arial", 10, "bold"),
                      relief="flat", padx=5, pady=5).grid(row=0, column=i, padx=5)

        # Status + AI Strategy
        self.status_label = tk.Label(root, text="Welcome to Battleship!",
                                     font=("Arial", 12, "bold"), bg="#1e3a8a", fg="white", width=40)
        self.status_label.pack(pady=5)

        self.ai_strategy_label = tk.Label(root, text="AI Strategy: None",
                                          font=("Arial", 10), fg="cyan", bg="#111827")
        self.ai_strategy_label.pack(pady=2)

    def _create_board(self, parent, player_board=False, ai_board=False):
        buttons = []
        for r in range(N):
            row_buttons = []
            for c in range(N):
                btn = tk.Button(
                    parent, text=" ", width=2, height=1,
                    bg=COLORS[CellState.EMPTY], fg="white",
                    font=("Arial", 10, "bold"), activebackground="#fde047",
                    relief="solid", bd=1, highlightthickness=1,
                    highlightbackground="#374151"   # viền mặc định xám
                )
                if player_board:
                    btn.config(command=lambda r=r, c=c: self.place_ship_click(r, c))
                if ai_board:
                    btn.config(command=lambda r=r, c=c: self.player_shoot(r, c))
                btn.grid(row=r, column=c, padx=0, pady=0)
                row_buttons.append(btn)
            buttons.append(row_buttons)
        return buttons

    def start_setup(self):
        """Bắt đầu giai đoạn Player đặt tàu"""
        self.game = GameState()
        self.ai = HybridAI(board_size=10, ships=[5,4,3,3,2])
        self.placing_ships = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.current_ship = self.placing_ships.pop(0)
        self.status_label.config(text=f"Đặt tàu: {self.current_ship.name} ({self.current_ship.size} ô)")

    def place_ship_click(self, r, c):
        """Player click để đặt tàu"""
        if not self.current_ship:
            return

        # Hỏi hướng
        orientation = simpledialog.askstring("Hướng", "Nhập hướng (N = Ngang, D = Dọc):")
        if not orientation: return
        orientation = orientation.strip().upper()
        if orientation == "N":
            orientation = "horizontal"
        elif orientation == "D":
            orientation = "vertical"
        else:
            messagebox.showerror("Lỗi", "Hướng không hợp lệ! Nhập N hoặc D.")
            return

        placed = self.game.player_board.place_ship(self.current_ship, r, c, orientation)
        if placed:
            self.update_boards()
            if self.placing_ships:
                self.current_ship = self.placing_ships.pop(0)
                self.status_label.config(text=f"Đặt tàu: {self.current_ship.name} ({self.current_ship.size} ô)")
            else:
                self.current_ship = None
                self.start_game()
        else:
            messagebox.showerror("Lỗi", "Không thể đặt tàu tại đây!")

    def start_game(self):
        """Khi Player đặt xong tàu → AI đặt tàu và game bắt đầu"""
        self.game.ai_board = Board()
        self.game.ai_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.game._ai_auto_place_ships()

        self.update_boards()
        self.status_label.config(text="Game started! Player turn.")

    def reset_game(self):
        """Reset GUI và game"""
        self.game = None
        self.ai = None
        self.placing_ships = []
        self.current_ship = None
        for board in [self.player_buttons, self.ai_buttons]:
            for row in board:
                for btn in row:
                    btn.config(bg=COLORS[CellState.EMPTY], text=" ", highlightbackground="#374151")
        self.status_label.config(text="Game reset. Click Start để đặt tàu mới.")
        self.ai_strategy_label.config(text="AI Strategy: None")

    def update_boards(self):
        """Cập nhật GUI theo trạng thái Board"""
        if not self.game: return

        # Player board
        for r in range(N):
            for c in range(N):
                cell = self.game.player_board.grid[r][c]
                bg, text, border = COLORS[CellState.EMPTY], " ", "#374151"
                if cell == CellState.SHIP:
                    bg = COLORS[CellState.SHIP]
                    text = "●"  # chấm trắng
                elif cell == CellState.MISS:
                    bg = COLORS[CellState.MISS]
                elif cell == CellState.HIT:
                    bg = COLORS[CellState.HIT]
                    text = "💀"
                elif cell == CellState.SUNK_SHIP:
                    bg = COLORS[CellState.SUNK_SHIP]
                    text = "💀"
                    border = "#ffffff"   # viền trắng cho tàu chìm

                self.player_buttons[r][c].config(
                    bg=bg, text=text, fg="white", highlightbackground=border
                )

        # AI tracking board
        for r in range(N):
            for c in range(N):
                cell = self.game.player_tracking_board.grid[r][c]
                bg, text, border = COLORS[CellState.EMPTY], " ", "#374151"
                if cell == CellState.MISS:
                    bg = COLORS[CellState.MISS]
                elif cell == CellState.HIT:
                    bg = COLORS[CellState.HIT]
                    text = "💀"
                elif cell == CellState.SUNK_SHIP:
                    bg = COLORS[CellState.SUNK_SHIP]
                    text = "💀"
                    border = "#ffffff"

                self.ai_buttons[r][c].config(
                    bg=bg, text=text, fg="white", highlightbackground=border
                )

    def player_shoot(self, r, c):
        """Player click vào AI board"""
        if not self.game or self.game.game_over: return
        if self.current_ship: return  # đang đặt tàu, chưa bắn
        if self.game.current_turn != "Player":
            self.status_label.config(text="Không phải lượt của bạn!")
            return

        result = self.game.player_shot(r, c)
        self.update_boards()
        if result == "Win":
            self.status_label.config(text="🎉 Player thắng!")
            return
        elif result in ["Miss", "Hit", "Sunk"]:
            self.status_label.config(text=f"Player: {result}")
            self.root.after(1000, self.ai_turn)
        elif result in ["Already_Shot", "Invalid"]:
            self.status_label.config(text="Ô này đã bắn rồi!")

    def ai_turn(self):
        """AI chọn nước đi"""
        if not self.game or self.game.game_over: return
        result = self.game.ai_shot(self.ai)
        self.update_boards()
        # Lấy chế độ hiện tại của AI
        ai_mode = getattr(self.ai, "mode", "blind").capitalize()
        if result == "Win":
            self.status_label.config(text=f"🤖 AI thắng! (Chiến lược: {ai_mode})")
        else:
            self.status_label.config(text=f"AI ({ai_mode}): {result}")
    def ai_turn(self):
        """AI chọn nước đi"""
        if not self.game or self.game.game_over:
            return

        result = self.game.ai_shot(self.ai)
        self.update_boards()

        ai_mode = getattr(self.ai, "mode", "blind").capitalize()

        if self.game.game_over and self.game.winner == "AI":
            self.status_label.config(text=f"🤖 AI thắng! (Chiến lược: {ai_mode})")
        elif result == "Win":
            self.status_label.config(text=f"🤖 AI thắng! (Chiến lược: {ai_mode})")
        else:
            self.status_label.config(text=f"AI ({ai_mode}): {result}")

            # 👉 Nếu AI bắn trúng thì tiếp tục bắn sau 1s
            if result in ["Hit", "Sunk"]:
                self.root.after(1000, self.ai_turn)


if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()
