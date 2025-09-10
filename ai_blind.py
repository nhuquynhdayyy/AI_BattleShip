# ai_blind.py
import random

class BlindAI:
    def __init__(self, board_size=10):
        self.board_size = board_size
        self.shots_taken = set()

    def choose_move(self):
        remaining = [
            (r,c) for r in range(self.board_size)
                  for c in range(self.board_size)
                  if (r,c) not in self.shots_taken
        ]
        if not remaining:
            return -1, -1  # hết ô
        move = random.choice(remaining)
        self.shots_taken.add(move)
        return move

if __name__ == "__main__":
    ai = BlindAI()
    for t in range(10):
        print(f"Turn {t+1}: AI shoots at {ai.choose_move()}")
