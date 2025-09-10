# main.py
from logic_game import GameState, Board, Ship, FLEET_CONFIG
from ai_blind import BlindAI

def parse_input(user_input):
    """Chuyển 'A1' -> (0,0), 'J10' -> (9,9)."""
    user_input = user_input.strip().upper()
    if len(user_input) < 2 or len(user_input) > 3:
        return None
    col_char = user_input[0]
    if not ('A' <= col_char <= 'J'):
        return None
    try:
        row_num = int(user_input[1:])
    except ValueError:
        return None
    if not (1 <= row_num <= 10):
        return None
    row = row_num - 1
    col = ord(col_char) - ord('A')
    return row, col

def manual_setup(board):
    """Cho Player đặt tàu thủ công qua console."""
    print("===== GIAI ĐOẠN ĐẶT TÀU =====")
    print("Quy tắc: tàu không chồng chéo, không chạm nhau (kể cả chéo).")

    for ship_cfg in FLEET_CONFIG:
        ship = Ship(ship_cfg["name"], ship_cfg["size"])
        placed = False
        while not placed:
            board.print_board(show_ships=True)
            print(f"\n--- Đang đặt {ship.name} ({ship.size} ô) ---")

            coord_input = input("Nhập tọa độ bắt đầu (vd: A1, B5, J10): ")
            coords = parse_input(coord_input)
            if not coords:
                print(">> Lỗi: Tọa độ không hợp lệ!")
                continue
            row, col = coords

            orientation_input = input("Nhập hướng (N = Ngang, D = Dọc): ").strip().upper()
            if orientation_input == 'N':
                orientation = "horizontal"
            elif orientation_input == 'D':
                orientation = "vertical"
            else:
                print(">> Lỗi: Hướng không hợp lệ (chọn N hoặc D)!")
                continue

            placed = board.place_ship(ship, row, col, orientation)
            if not placed:
                print(">> Lỗi: Không thể đặt tàu tại đây. Thử lại!")

    print("\n===== HOÀN TẤT ĐẶT TÀU =====")
    board.print_board(show_ships=True)

def run_game():
    game = GameState()
    ai = BlindAI(board_size=10)

    # Player đặt tàu manual
    game.player_board = Board()
    game.player_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
    manual_setup(game.player_board)

    # AI đặt tàu random
    game.ai_board = Board()
    game.ai_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
    game._ai_auto_place_ships()

    print("\n===== GAME BẮT ĐẦU =====")
    while not game.game_over:
        if game.current_turn == "Player":
            print("\n--- Player Tracking Board ---")
            game.player_tracking_board.print_board(show_ships=False)

            move_input = input("Nhập tọa độ để bắn (vd: A1, B5, J10): ")
            coords = parse_input(move_input)
            if not coords:
                print(">> Lỗi: Tọa độ không hợp lệ!")
                continue
            r, c = coords
            result = game.player_shot(r, c)
            print(f"Player bắn {move_input}: {result}")

            if result == "Win":
                print("🎉 Player thắng!")
                break

        else:  # AI turn
            r, c = ai.choose_move()
            print(f"\nAI bắn tại ({r},{c})")
            result = game.ai_shot(ai)
            print(f"AI: {result}")

            if result == "Win":
                print("🤖 AI thắng!")
                break

if __name__ == "__main__":
    run_game()
