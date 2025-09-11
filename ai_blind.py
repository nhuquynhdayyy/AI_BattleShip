# FILE: ai_blind.py

import random

class BlindAI:
    def __init__(self, board_size=10):
        self.board_size = board_size
        self.shots_taken = set()

    # *** THAY ĐỔI DUY NHẤT Ở ĐÂY ***
    # Đổi tên từ 'choose_move' thành 'get_move' để khớp với gui_game.py
    def get_move(self): 
        remaining = [
            (r, c) for r in range(self.board_size)
                   for c in range(self.board_size)
                   if (r, c) not in self.shots_taken
        ]
        if not remaining:
            return None # Trả về None khi hết ô, an toàn hơn là (-1, -1)
        
        move = random.choice(remaining)
        self.shots_taken.add(move)
        return move

if __name__ == "__main__":
    ai = BlindAI()
    for t in range(10):
        # Cập nhật cả ở đây để test cho đúng
        print(f"Turn {t+1}: AI shoots at {ai.get_move()}") 