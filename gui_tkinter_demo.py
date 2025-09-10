# gui_tkinter_demo.py
import tkinter as tk

N = 10  # kích thước bảng

class BattleshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Battleship Demo")

        # Frame chính
        main_frame = tk.Frame(root)
        main_frame.pack(pady=10)

        # Player board
        player_frame = tk.LabelFrame(main_frame, text="Player Board")
        player_frame.grid(row=0, column=0, padx=20)
        self.player_buttons = self._create_board(player_frame)

        # AI board
        ai_frame = tk.LabelFrame(main_frame, text="AI Board")
        ai_frame.grid(row=0, column=1, padx=20)
        self.ai_buttons = self._create_board(ai_frame)

        # Control buttons
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)

        btn_start = tk.Button(control_frame, text="Start", width=10, command=self.start_game)
        btn_reset = tk.Button(control_frame, text="Reset", width=10, command=self.reset_game)
        btn_quit  = tk.Button(control_frame, text="Quit",  width=10, command=root.quit)

        btn_start.grid(row=0, column=0, padx=5)
        btn_reset.grid(row=0, column=1, padx=5)
        btn_quit.grid(row=0, column=2, padx=5)

    def _create_board(self, parent):
        buttons = []
        for r in range(N):
            row_buttons = []
            for c in range(N):
                btn = tk.Button(parent, text=" ", width=2, height=1,
                                bg="lightgray", relief="raised")
                btn.grid(row=r, column=c, padx=1, pady=1)
                row_buttons.append(btn)
            buttons.append(row_buttons)
        return buttons

    def start_game(self):
        print("Game started!")
        # ví dụ: đổi màu vài ô trên Player Board
        self.player_buttons[0][0].config(bg="red", text="X")
        self.ai_buttons[2][3].config(bg="blue", text="O")

    def reset_game(self):
        print("Game reset!")
        # reset lại màu tất cả ô về xám
        for board in [self.player_buttons, self.ai_buttons]:
            for row in board:
                for btn in row:
                    btn.config(bg="lightgray", text=" ")

if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()
