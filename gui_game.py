# gui_game.py
import tkinter as tk
from tkinter import messagebox, simpledialog
from logic_game import GameState, CellState, Ship, Board, FLEET_CONFIG
from ai_hybrid import HybridAI

N = 10

COLORS = {
    CellState.EMPTY: "lightgray",
    CellState.SHIP: "gray",        # Player ship
    CellState.HIT: "red",
    CellState.MISS: "blue",
    CellState.SUNK_SHIP: "black"
}

class BattleshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Battleship Player vs AI (Blind Search)")

        self.game = None
        self.ai = None
        self.placing_ships = []     # danh sách tàu Player cần đặt
        self.current_ship = None    # tàu đang đặt

        # Frames
        main_frame = tk.Frame(root)
        main_frame.pack(pady=10)

        # Player board
        player_frame = tk.LabelFrame(main_frame, text="Player Board (Click để đặt tàu)")
        player_frame.grid(row=0, column=0, padx=20)
        self.player_buttons = self._create_board(player_frame, player_board=True)

        # AI board
        ai_frame = tk.LabelFrame(main_frame, text="AI Board (Click để bắn)")
        ai_frame.grid(row=0, column=1, padx=20)
        self.ai_buttons = self._create_board(ai_frame, ai_board=True)

        # Control buttons
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)

        tk.Button(control_frame, text="Start", width=10, command=self.start_setup).grid(row=0, column=0, padx=5)
        tk.Button(control_frame, text="Reset", width=10, command=self.reset_game).grid(row=0, column=1, padx=5)
        tk.Button(control_frame, text="Quit",  width=10, command=root.quit).grid(row=0, column=2, padx=5)

        self.status_label = tk.Label(root, text="Welcome to Battleship!", font=("Arial", 12))
        self.status_label.pack(pady=5)

    def _create_board(self, parent, player_board=False, ai_board=False):
        buttons = []
        for r in range(N):
            row_buttons = []
            for c in range(N):
                btn = tk.Button(parent, text=" ", width=2, height=1,
                                bg=COLORS[CellState.EMPTY], relief="raised")
                btn.grid(row=r, column=c, padx=1, pady=1)
                if player_board:
                    btn.config(command=lambda r=r, c=c: self.place_ship_click(r, c))
                if ai_board:
                    btn.config(command=lambda r=r, c=c: self.player_shoot(r, c))
                row_buttons.append(btn)
            buttons.append(row_buttons)
        return buttons

    def start_setup(self):
        """Bắt đầu giai đoạn Player đặt tàu"""
        self.game = GameState()
        # self.ai = BlindAI(board_size=10)
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
                    btn.config(bg=COLORS[CellState.EMPTY], text=" ")
        self.status_label.config(text="Game reset. Click Start để đặt tàu mới.")

    def update_boards(self):
        """Cập nhật GUI theo trạng thái Board"""
        if not self.game: return

        # Player board
        for r in range(N):
            for c in range(N):
                cell = self.game.player_board.grid[r][c]
                color = COLORS[cell]
                if cell == CellState.SHIP:
                    color = "gray"
                self.player_buttons[r][c].config(bg=color)

        # AI tracking board
        for r in range(N):
            for c in range(N):
                cell = self.game.player_tracking_board.grid[r][c]
                color = COLORS[cell]
                self.ai_buttons[r][c].config(bg=color)

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

if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()
