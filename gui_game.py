# gui_game.py
import tkinter as tk
from logic_game import GameState, CellState, Ship, Board, FLEET_CONFIG
from ai_blind import BlindAI

N = 10

COLORS = {
    CellState.EMPTY: "lightgray",
    CellState.SHIP: "gray",        # Chỉ hiển thị trên Player board
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

        # Frames
        main_frame = tk.Frame(root)
        main_frame.pack(pady=10)

        # Player board
        player_frame = tk.LabelFrame(main_frame, text="Player Board")
        player_frame.grid(row=0, column=0, padx=20)
        self.player_buttons = self._create_board(player_frame)

        # AI board
        ai_frame = tk.LabelFrame(main_frame, text="AI Board (Click to shoot)")
        ai_frame.grid(row=0, column=1, padx=20)
        self.ai_buttons = self._create_board(ai_frame, ai_board=True)

        # Control buttons
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)

        tk.Button(control_frame, text="Start", width=10, command=self.start_game).grid(row=0, column=0, padx=5)
        tk.Button(control_frame, text="Reset", width=10, command=self.reset_game).grid(row=0, column=1, padx=5)
        tk.Button(control_frame, text="Quit",  width=10, command=root.quit).grid(row=0, column=2, padx=5)

        self.status_label = tk.Label(root, text="Welcome to Battleship!", font=("Arial", 12))
        self.status_label.pack(pady=5)

    def _create_board(self, parent, ai_board=False):
        buttons = []
        for r in range(N):
            row_buttons = []
            for c in range(N):
                btn = tk.Button(parent, text=" ", width=2, height=1,
                                bg=COLORS[CellState.EMPTY], relief="raised")
                btn.grid(row=r, column=c, padx=1, pady=1)
                if ai_board:
                    btn.config(command=lambda r=r, c=c: self.player_shoot(r, c))
                row_buttons.append(btn)
            buttons.append(row_buttons)
        return buttons

    def start_game(self):
        """Khởi tạo game mới"""
        self.game = GameState()
        self.game.setup_game()
        self.ai = BlindAI(board_size=10)

        self.update_boards()
        self.status_label.config(text="Game started! Player turn.")

    def reset_game(self):
        """Reset GUI và game"""
        self.game = None
        self.ai = None
        for board in [self.player_buttons, self.ai_buttons]:
            for row in board:
                for btn in row:
                    btn.config(bg=COLORS[CellState.EMPTY], text=" ")
        self.status_label.config(text="Game reset. Click Start to play again.")

    def update_boards(self):
        """Cập nhật GUI theo trạng thái Board"""
        if not self.game: return

        # Player board (hiện cả tàu của Player)
        for r in range(N):
            for c in range(N):
                cell = self.game.player_board.grid[r][c]
                color = COLORS[cell]
                if cell == CellState.SHIP:
                    color = "gray"   # hiển thị tàu Player
                self.player_buttons[r][c].config(bg=color)

        # AI tracking board (chỉ hiện thông tin Player biết về AI)
        for r in range(N):
            for c in range(N):
                cell = self.game.player_tracking_board.grid[r][c]
                color = COLORS[cell]
                self.ai_buttons[r][c].config(bg=color)

    def player_shoot(self, r, c):
        """Player click vào AI board"""
        if not self.game or self.game.game_over: return
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
            self.root.after(1000, self.ai_turn)  # AI bắn sau 1s
        elif result in ["Already_Shot", "Invalid"]:
            self.status_label.config(text="Ô này đã bắn rồi!")

    def ai_turn(self):
        """AI chọn nước đi"""
        if not self.game or self.game.game_over: return
        result = self.game.ai_shot(self.ai)
        self.update_boards()
        if result == "Win":
            self.status_label.config(text="🤖 AI thắng!")
        else:
            self.status_label.config(text=f"AI: {result}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()
