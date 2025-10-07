import random

class BlindAI:
    def __init__(self, board_size=10):
        self.possible_shots = [(r, c) for r in range(board_size) for c in range(board_size)]
        random.shuffle(self.possible_shots)

    def get_move(self, tracking_board, remaining_ships):
        """
        Lấy nước đi ngẫu nhiên. Hàm này bỏ qua tracking_board và remaining_ships.
        """
        if self.possible_shots:
            return self.possible_shots.pop(0)
        return None

    def report_result(self, move, result):
        """
        AI Mù không học hỏi từ kết quả, nên hàm này không làm gì cả.
        """
        pass