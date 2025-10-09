# FILE: gui_game.py
# PHIÊN BẢN HOÀN CHỈNH - TÍCH HỢP ÂM THANH VÀ ĐỒ HỌA NÂNG CAO (V3 - Khắc phục layout)

import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import os 

# *** THÊM IMPORT PYGAME ***
from attr import s
import pygame

from logic_game import GameState, CellState, Ship, Board, FLEET_CONFIG
from ai_blind import BlindAI
from ai_heuristic import HeuristicAI
from ai_hybrid import HybridAI

N = 10
CELL_SIZE = 40 

# --- Global constants for asset paths ---
ASSET_DIR = "assets"
IMAGE_DIR = os.path.join(ASSET_DIR, "images")
ICON_DIR = os.path.join(ASSET_DIR, "icons")
SHIP_IMG_DIR = os.path.join(ASSET_DIR, "ships")

# --- Updated COLORS and FONTS ---
COLORS = {
    "water_base": "#284A6E",  # Darker blue, more oceanic
    "ship_deck_base": "#5A6B7C", # Muted gray for ship body (for unplaced state)
    "ship_deck_placed": "#404C5A", # Darker gray for placed ship in shipyard
    "ship_gun_base": "#3C4955",  # Darker gray for guns/details
    "hit_base": "#E04F5F",    # Brighter red for hit
    "miss_base": "#5EC4FF",   # Lighter blue for miss splash
    "sunk_base": "#1A222B",   # Almost black for sunk background
    "preview_ok": "#58D683",  # Green for valid placement
    "preview_err": "#FF7A6A", # Orange-red for invalid placement
    "border_grid": "#4A5568", # Darker gray for grid lines
    "text_light": "#E0E7EB",  # Light text color
    "text_dark": "#1A222B",   # Dark text color
    "button_normal": "#4A5568", # Button base
    "button_hover": "#718096",  # Button hover
    "button_active": "#2D3748", # Button active state (e.g., status label background)
    "selection_highlight": "#FFD700", # Gold-like for selected ship
    "shipyard_bg": "#1E3A8A", # Slightly lighter blue for shipyard frame
}

# Fonts (Using Arial for wider compatibility)
FONTS = {
    "title": ("Arial Black", 36, "bold"),
    "subtitle": ("Arial", 18, "bold"),
    "button": ("Arial", 14, "bold"),
    "label": ("Arial", 10),
    "status": ("Arial", 12, "bold")
}

class BattleshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚓ Battleship - Canvas Edition")
        self.root.withdraw()
        
        # --- CÁC BIẾN TRẠNG THÁI ---
        self.game, self.ai = None, None
        self.selected_ship, self.placement_orientation = None, "horizontal"
        self.shipyard_widgets, self.preview_coords = {}, []
        
        # *** KHỞI TẠO HỆ THỐNG ÂM THANH VÀ TẢI TÀI NGUYÊN ĐỒ HỌA ***
        self._load_assets() 
        
        self.show_difficulty_selection()
        
    def _load_assets(self):
        """Tải tất cả các file âm thanh và hình ảnh vào bộ nhớ."""
        self.images = {}
        self.assets_loaded = False 
        try:
            # --- Load Sounds ---
            pygame.mixer.init()
            self.sounds = {
                'click': pygame.mixer.Sound(os.path.join(ASSET_DIR, "click.wav")),
                'shot': pygame.mixer.Sound(os.path.join(ASSET_DIR, "shot.wav")),
                'hit': pygame.mixer.Sound(os.path.join(ASSET_DIR, "hit.wav")),
                'miss': pygame.mixer.Sound(os.path.join(ASSET_DIR, "miss.wav")),
                'sunk': pygame.mixer.Sound(os.path.join(ASSET_DIR, "sunk.wav")),
                'win': pygame.mixer.Sound(os.path.join(ASSET_DIR, "win.wav")),
                'lose': pygame.mixer.Sound(os.path.join(ASSET_DIR, "lose.wav"))
            }
            pygame.mixer.music.load(os.path.join(ASSET_DIR, "background_music.mp3"))
            pygame.mixer.music.play(loops=-1)
            pygame.mixer.music.set_volume(0.3)
        except pygame.error as e:
            print(f"Cảnh báo: Không thể tải file âm thanh. Game sẽ không có tiếng. Lỗi: {e}")
            self.sounds = None
        
        try:
            # --- Load Images ---
            self.images['bg_difficulty'] = ImageTk.PhotoImage(Image.open(os.path.join(IMAGE_DIR, "background_difficulty.png")).resize((800, 600), Image.LANCZOS))
            
            # Board elements
            self.images['water_tile'] = ImageTk.PhotoImage(Image.open(os.path.join(ICON_DIR, "water_tile.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS))
            self.images['hit_marker'] = ImageTk.PhotoImage(Image.open(os.path.join(ICON_DIR, "hit_marker.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS))
            self.images['miss_marker'] = ImageTk.PhotoImage(Image.open(os.path.join(ICON_DIR, "miss_marker.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS))
            self.images['sunk_marker'] = ImageTk.PhotoImage(Image.open(os.path.join(ICON_DIR, "sunk_marker.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS))

            # Ship segments
            self.ship_segment_images = {
                'deck_h': ImageTk.PhotoImage(Image.open(os.path.join(SHIP_IMG_DIR, "ship_deck_h.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)),
                'deck_v': ImageTk.PhotoImage(Image.open(os.path.join(SHIP_IMG_DIR, "ship_deck_v.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)),
                'gun_h': ImageTk.PhotoImage(Image.open(os.path.join(SHIP_IMG_DIR, "ship_gun_h.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)), 
                'gun_v': ImageTk.PhotoImage(Image.open(os.path.join(SHIP_IMG_DIR, "ship_gun_v.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)),
            }
            
            print("Đã tải tài nguyên đồ họa thành công.")
            self.assets_loaded = True
        except FileNotFoundError as e:
            print(f"Cảnh báo: Không thể tải một số file hình ảnh. Đảm bảo thư mục '{ASSET_DIR}' và các file cần thiết tồn tại. Lỗi: {e}")
            self.assets_loaded = False
            print("Sử dụng màu sắc mặc định thay thế.")


    def play_sound(self, name):
        """Hàm tiện ích để phát một hiệu ứng âm thanh."""
        if self.sounds and name in self.sounds:
            self.sounds[name].play()
        
    def show_difficulty_selection(self):
        self.difficulty_window = tk.Toplevel(self.root)
        self.difficulty_window.title("Chọn Độ Khó")
        self.difficulty_window.geometry("800x600")
        self.difficulty_window.resizable(False, False)

        if self.assets_loaded and 'bg_difficulty' in self.images:
            bg_label = tk.Label(self.difficulty_window, image=self.images['bg_difficulty'])
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.difficulty_window.configure(bg="#1f2937") 

        title_frame = tk.Frame(self.difficulty_window, bg="black", bd=0) 
        title_frame.pack(pady=(80, 40))
        title_label = tk.Label(title_frame, text="CHỌN ĐỘ KHÓ", font=FONTS["title"], fg="white", bg="black", padx=20, pady=5)
        title_label.pack()

        btn_font = FONTS["button"]
        btn_width = 20
        btn_bg_normal = COLORS["button_normal"]
        btn_fg_normal = COLORS["text_light"]
        btn_bg_hover = COLORS["button_hover"]

        def on_enter_btn(e): e.widget['background'] = btn_bg_hover
        def on_leave_btn(e): e.widget['background'] = btn_bg_normal 

        def select_difficulty(level):
            self.play_sound('click')
            self.start_setup(level)

        easy_btn = tk.Button(self.difficulty_window, text="DỄ", font=btn_font, width=btn_width,
                             bg=btn_bg_normal, fg=btn_fg_normal, relief="flat", command=lambda: select_difficulty("1"))
        easy_btn.pack(pady=15)
        easy_btn.bind("<Enter>", on_enter_btn)
        easy_btn.bind("<Leave>", on_leave_btn)

        medium_btn = tk.Button(self.difficulty_window, text="TRUNG BÌNH", font=btn_font, width=btn_width,
                               bg=btn_bg_normal, fg=btn_fg_normal, relief="flat", command=lambda: select_difficulty("2"))
        medium_btn.pack(pady=15)
        medium_btn.bind("<Enter>", on_enter_btn)
        medium_btn.bind("<Leave>", on_leave_btn)

        hard_btn = tk.Button(self.difficulty_window, text="KHÓ", font=btn_font, width=btn_width,
                             bg=btn_bg_normal, fg=btn_fg_normal, relief="flat", command=lambda: select_difficulty("3"))
        hard_btn.pack(pady=15)
        hard_btn.bind("<Enter>", on_enter_btn)
        hard_btn.bind("<Leave>", on_leave_btn)
        
        self.difficulty_window.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def on_board_click(self, r, c):
        self.play_sound('click')
        if not self.game or self.game.ai_board is not None: return 

        if self.selected_ship:
            if self.game.player_board.place_ship(self.selected_ship, r, c, self.placement_orientation):
                ship_lbl = self.shipyard_widgets[self.selected_ship.name]
                ship_lbl.config(bg=COLORS["ship_deck_placed"], fg=COLORS["text_dark"], cursor="arrow")
                ship_lbl.unbind("<Button-1>") 
                ship_lbl.unbind("<Enter>") # Also unbind hover effects for placed ships
                ship_lbl.unbind("<Leave>")
                
                self.selected_ship = None
                self.update_boards()
                
                if all(s.coordinates for s in self.game.player_fleet):
                    self.status_label.config(text="Đã đặt xong! Nhấn Ready để bắt đầu.")
                    self.ready_button.config(state="normal", bg=COLORS["button_hover"])
                else: 
                    self.status_label.config(text="Đặt tàu thành công! Chọn tàu tiếp theo.")
            else: 
                messagebox.showerror("Lỗi", "Không thể đặt tàu tại đây. Đảm bảo không chồng chéo hoặc ra ngoài biên.", parent=self.root)
        else: 
            ship_to_edit = self.game.player_board.find_ship_at(r, c)
            if ship_to_edit and not ship_to_edit.is_sunk:
                self.game.player_board.remove_ship(ship_to_edit)
                ship_lbl = self.shipyard_widgets[ship_to_edit.name]
                ship_lbl.config(bg=COLORS["ship_deck_base"], fg=COLORS["text_light"], cursor="hand2")
                ship_lbl.bind("<Button-1>", lambda e, s=ship_to_edit: self.select_ship(s))
                # Rebind hover effects
                def on_enter_ship_lbl(e): e.widget['background'] = COLORS["button_hover"] if self.selected_ship != s else COLORS["selection_highlight"]
                def on_leave_ship_lbl(e): e.widget['background'] = COLORS["ship_deck_base"] if self.selected_ship != s else COLORS["selection_highlight"]
                ship_lbl.bind("<Enter>", on_enter_ship_lbl)
                ship_lbl.bind("<Leave>", on_leave_ship_lbl)


                self.select_ship(ship_to_edit) 
                self.update_boards()
                self.ready_button.config(state="disabled", bg=COLORS["button_normal"])
                self.status_label.config(text=f"Đang sửa {ship_to_edit.name}. Hãy đặt lại.")

    def select_ship(self, ship):
        self.play_sound('click')
        if self.selected_ship and self.selected_ship.name in self.shipyard_widgets:
            prev_ship_lbl = self.shipyard_widgets[self.selected_ship.name]
            # Reset old selected ship's style only if it's not already placed (to keep the "placed" color)
            if not self.selected_ship.coordinates: 
                prev_ship_lbl.config(relief="flat", bg=COLORS["ship_deck_base"], bd=0)
        
        self.selected_ship = ship
        if ship.name in self.shipyard_widgets:
            self.shipyard_widgets[ship.name].config(relief="solid", bg=COLORS["selection_highlight"], bd=2, highlightbackground=COLORS["text_light"])
        self.status_label.config(text=f"Đang đặt {ship.name}. Chuột phải để xoay.")
    
    def player_shoot(self, r, c):
        if not self.game or self.game.game_over or self.selected_ship or \
           self.game.ai_board is None or self.game.current_turn != "Player" or \
           self.game.player_tracking_board.grid[r][c] in [CellState.HIT, CellState.MISS, CellState.SUNK_SHIP]: 
            self.status_label.config(text="Không thể bắn tại đây lúc này.")
            return
        
        self.play_sound('shot')
        result, ship = self.game.player_shot(r, c)
        
        if result == "Hit": self.play_sound('hit')
        elif result == "Sunk": self.play_sound('sunk')
        elif result == "Miss": self.play_sound('miss')
        
        self.update_boards()
        
        if self.game.game_over: 
            if self.game.winner == "Player":
                self.play_sound('win')
                self.status_label.config(text="🎉 Bạn thắng!"); messagebox.showinfo("Game Over", "Bạn đã thắng!", parent=self.root)
            else: 
                pass 
        elif result == "Sunk":
            self.status_label.config(text=f"Bạn: {ship.name} bị chìm! Bắn tiếp.")
        elif result == "Hit":
            self.status_label.config(text=f"Bạn: Trúng! Bắn tiếp.")
        elif result == "Miss":
            self.status_label.config(text="Bạn: Trượt! Lượt của AI..."); self.root.after(500, self.ai_turn)
        elif result == "Already_Shot": 
            self.status_label.config(text="Ô này đã bắn rồi!")

    def ai_turn(self):
        if not self.game or self.game.game_over: return
        
        self.play_sound('shot')
        result, ship, move = self.game.ai_shot(self.ai)
        
        if result == "Hit": self.play_sound('hit')
        elif result == "Sunk": self.play_sound('sunk')
        elif result == "Miss": self.play_sound('miss')
        
        ai_mode = getattr(self.ai, "mode", "blind").capitalize() 
        if not ai_mode: ai_mode = "N/A" 
        self.ai_strategy_label.config(text=f"AI Strategy: {ai_mode} Mode")
        self.update_boards()
        
        if self.game.game_over: 
            if self.game.winner == "AI":
                self.play_sound('lose')
                self.status_label.config(text=f"🤖 AI thắng!"); messagebox.showinfo("Game Over", "AI đã thắng.", parent=self.root)
            else: 
                pass
        elif result == "Sunk":
            self.play_sound('sunk')
            self.status_label.config(text=f"AI ({ai_mode}): {ship.name} bị chìm! AI bắn tiếp."); self.root.after(500, self.ai_turn)
        elif result == "Hit":
            self.status_label.config(text=f"AI ({ai_mode}): Trúng! AI bắn tiếp."); self.root.after(500, self.ai_turn)
        elif result == "Miss":
            self.status_label.config(text=f"AI ({ai_mode}): Trượt! Lượt của bạn.")
        elif result == "AI_Error" or result == "No_Move":
             self.status_label.config(text=f"AI lỗi hoặc không có nước đi, chuyển lượt.")
             if result == "AI_Error" : self.game.switch_turn() 

    def setup_main_window(self):
        for widget in self.root.winfo_children(): widget.destroy()

        if self.assets_loaded:
            self.root.update_idletasks() 
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            try:
                self.images['bg_main'] = ImageTk.PhotoImage(Image.open(os.path.join(IMAGE_DIR, "background_main.png")).resize((screen_width, screen_height), Image.LANCZOS))
            except FileNotFoundError as e:
                print(f"Cảnh báo: Không tải được background_main.png. Lỗi: {e}. Sử dụng màu nền thay thế.")
                self.images['bg_main'] = None

        self.main_bg_canvas = tk.Canvas(self.root, highlightthickness=0)
        self.main_bg_canvas.pack(fill="both", expand=True)
        
        if self.assets_loaded and self.images.get('bg_main'):
            self.main_bg_canvas.create_image(0, 0, image=self.images['bg_main'], anchor="nw")
        else:
            self.main_bg_canvas.configure(bg=COLORS["water_base"]) 

        # Main game content frame to hold everything
        game_content_frame = tk.Frame(self.main_bg_canvas, bg=COLORS["water_base"], bd=0, relief="flat")
        game_content_frame.grid_rowconfigure(0, weight=1) # Allow top row to expand vertically
        game_content_frame.grid_columnconfigure((0, 1, 2), weight=1) # Allow columns to expand horizontally

        # Top area frame for 3 columns (shipyard, player board, AI board)
        top_game_area_frame = tk.Frame(game_content_frame, bg=COLORS["water_base"])
        top_game_area_frame.grid(row=0, column=0, columnspan=3, pady=10, sticky="nsew") # Place it in row 0 of game_content_frame

        # Configure columns within top_game_area_frame
        top_game_area_frame.grid_columnconfigure(0, weight=1, minsize=200) # Shipyard column
        top_game_area_frame.grid_columnconfigure(1, weight=1, minsize=N * CELL_SIZE) # Player board column
        top_game_area_frame.grid_columnconfigure(2, weight=1, minsize=N * CELL_SIZE) # AI board column
        top_game_area_frame.grid_rowconfigure(0, weight=1) # Allow the single row to expand

        # --- Shipyard Column (New) ---
        shipyard_column = tk.Frame(top_game_area_frame, bg=COLORS["water_base"])
        shipyard_column.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.shipyard_outer_frame = tk.Frame(shipyard_column, bg=COLORS["shipyard_bg"], padx=10, pady=10, bd=2, relief="groove")
        self.shipyard_outer_frame.pack(fill="both", expand=True) # Occupy all available space in its column
        tk.Label(self.shipyard_outer_frame, text="XƯỞNG TÀU", font=FONTS["subtitle"], fg=COLORS["text_light"], bg=COLORS["shipyard_bg"]).pack(pady=(0,10))
        self.shipyard_frame = tk.Frame(self.shipyard_outer_frame, bg=COLORS["shipyard_bg"]) # Inner frame for ship labels
        self.shipyard_frame.pack(fill="x") # Ship labels go here

        # --- Player Board Column ---
        player_column = tk.Frame(top_game_area_frame, bg=COLORS["water_base"])
        player_column.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        player_board_title_frame = tk.Frame(player_column, bg=COLORS["water_base"])
        player_board_title_frame.pack(pady=(0, 5))
        tk.Label(player_board_title_frame, text="🧑 BẢNG CỦA BẠN", font=FONTS["subtitle"], fg=COLORS["text_light"], bg=COLORS["water_base"]).pack()
        self.player_canvas = self._create_board(player_column, is_player_board=True) 

        # --- AI Board Column ---
        ai_column = tk.Frame(top_game_area_frame, bg=COLORS["water_base"])
        ai_column.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

        ai_board_title_frame = tk.Frame(ai_column, bg=COLORS["water_base"])
        ai_board_title_frame.pack(pady=(0, 5))
        tk.Label(ai_board_title_frame, text="🤖 BẢNG ĐỐI THỦ", font=FONTS["subtitle"], fg=COLORS["text_light"], bg=COLORS["water_base"]).pack()
        self.ai_canvas = self._create_board(ai_column, is_ai_board=True)

        # --- Bottom Controls Frame (Spanning all columns) ---
        bottom_controls_frame = tk.Frame(game_content_frame, bg=COLORS["water_base"], bd=0)
        bottom_controls_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky="ew") # Place it in row 1 of game_content_frame, spanning 3 columns

        self.status_label = tk.Label(bottom_controls_frame, text="...", font=FONTS["status"], bg=COLORS["button_active"], fg=COLORS["text_light"], height=2, wraplength=400); self.status_label.pack(pady=5, fill="x", padx=20)
        self.ai_strategy_label = tk.Label(bottom_controls_frame, text="AI Strategy: None", font=FONTS["label"], fg=COLORS["text_light"], bg=COLORS["water_base"]); self.ai_strategy_label.pack(pady=2)

        control_frame = tk.Frame(bottom_controls_frame, bg=COLORS["water_base"]); control_frame.pack(pady=10)
        
        btn_font = FONTS["button"]
        btn_bg_normal = COLORS["button_normal"]
        btn_fg_normal = COLORS["text_light"]
        btn_bg_hover = COLORS["button_hover"]

        def on_enter_ctrl_btn(e): e.widget['background'] = btn_bg_hover
        def on_leave_ctrl_btn(e): e.widget['background'] = btn_bg_normal

        reset_btn = tk.Button(control_frame, text="🔄 Reset", width=10, command=self.reset_game, 
                              bg=btn_bg_normal, fg=btn_fg_normal, font=btn_font, relief="flat", padx=5, pady=5)
        reset_btn.grid(row=0, column=0, padx=5)
        reset_btn.bind("<Enter>", on_enter_ctrl_btn)
        reset_btn.bind("<Leave>", on_leave_ctrl_btn)

        quit_btn = tk.Button(control_frame, text="❌ Quit", width=10, command=self.root.quit, 
                             bg=btn_bg_normal, fg=btn_fg_normal, font=btn_font, relief="flat", padx=5, pady=5)
        quit_btn.grid(row=0, column=1, padx=5)
        quit_btn.bind("<Enter>", on_enter_ctrl_btn)
        quit_btn.bind("<Leave>", on_leave_ctrl_btn)
        
        self.root.bind("<Button-3>", self.rotate_ship)
        
        # Adjust window size for 3 columns more dynamically
        # Min width for shipyard to accommodate labels/buttons
        shipyard_content_width = 200 # Estimate required width for shipyard labels
        board_display_width = N * CELL_SIZE 
        # Total content width: shipyard + player board + AI board + padding
        total_content_width = shipyard_content_width + board_display_width * 2 + 60 # 2x padx=10 for shipyard_column, 2x padx=10 for player_column, 2x padx=10 for ai_column (total 60)
        
        # Max height for boards (10*40 = 400px), plus titles, status, controls
        total_content_height = board_display_width + 150 # Board height + space for titles/status/controls
        
        self.root.geometry(f"{total_content_width}x{total_content_height}")
        self.main_bg_canvas.create_window(total_content_width / 2, total_content_height / 2, window=game_content_frame, anchor="center") 
        self.root.update_idletasks() 

    def start_setup(self, difficulty):
        self.difficulty_window.destroy()
        self.setup_main_window()
        self.root.deiconify()
        
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")

        self.game = GameState()
        if difficulty == "1": self.ai = BlindAI(board_size=N); self.ai_strategy_label.config(text="AI Strategy: Dễ (Mù)")
        elif difficulty == "2": self.ai = HeuristicAI(board_size=N); self.ai_strategy_label.config(text="AI Strategy: Trung bình (Heuristic)")
        elif difficulty == "3": self.ai = HybridAI(board_size=N); self.ai_strategy_label.config(text="AI Strategy: Khó (Hybrid)")
        
        self._initialize_shipyard_widgets() # Call new function to init all shipyard widgets
        self.status_label.config(text="Click một tàu từ Xưởng Tàu để đặt.")
    
    def reset_game(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        self.root.withdraw()
        self.show_difficulty_selection()
    
    def _create_board(self, parent, is_player_board=False, is_ai_board=False):
        canvases = []
        board_frame = tk.Frame(parent, bg=COLORS["water_base"]) 
        board_frame.pack() # Pack the board_frame into its parent column

        for r_idx in range(N):
            row_canvases = [] # Temporarily store canvases for current row
            for c_idx in range(N):
                canvas = tk.Canvas(board_frame, width=CELL_SIZE, height=CELL_SIZE, bg=COLORS['water_base'], highlightthickness=1, highlightbackground=COLORS['border_grid'])
                if self.assets_loaded and 'water_tile' in self.images:
                    canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=self.images['water_tile'], anchor='center', tags="water")
                else:
                    canvas.create_rectangle(0, 0, CELL_SIZE, CELL_SIZE, fill=COLORS['water_base'], outline=COLORS['border_grid'], tags="water")

                if is_player_board:
                    canvas.bind("<Enter>", lambda e, r=r_idx, c=c_idx: self.on_board_hover(r, c)); 
                    canvas.bind("<Leave>", lambda e: self.clear_preview())
                    canvas.bind("<Button-1>", lambda e, r=r_idx, c=c_idx: self.on_board_click(r, c))
                if is_ai_board: 
                    canvas.bind("<Button-1>", lambda e, r=r_idx, c=c_idx: self.player_shoot(r, c))
                canvas.grid(row=r_idx, column=c_idx)
                row_canvases.append(canvas)
            canvases.append(row_canvases)
        return canvases
    
    def update_boards(self):
        if not self.game: return
        self._draw_board(self.player_canvas, self.game.player_board, show_ships=True)
        if self.game.ai_board: self._draw_board(self.ai_canvas, self.game.player_tracking_board, show_ships=False)
    
    def _draw_board(self, canvases, board, show_ships):
        for r in range(N):
            for c in range(N):
                canvas = canvases[r][c]
                canvas.delete("all") 

                if self.assets_loaded and 'water_tile' in self.images:
                     canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=self.images['water_tile'], anchor='center', tags="water")
                else:
                    canvas.create_rectangle(0, 0, CELL_SIZE, CELL_SIZE, fill=COLORS['water_base'], outline=COLORS['border_grid'], tags="water")
                
                cell_state = board.grid[r][c]
                
                if show_ships and cell_state in [CellState.SHIP, CellState.HIT, CellState.SUNK_SHIP]: 
                    ship = board.find_ship_at(r, c)
                    if ship:
                        if not ship.is_sunk: 
                            self._draw_ship_part(canvas, ship, ship.coordinates.index((r, c)))
                        else: 
                            pass 
                
                if cell_state == CellState.MISS:
                    if self.assets_loaded and 'miss_marker' in self.images:
                        canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=self.images['miss_marker'], anchor='center')
                    else: 
                        canvas.create_oval(10, 10, CELL_SIZE-10, CELL_SIZE-10, fill=COLORS['miss_base'], outline='white')
                elif cell_state == CellState.HIT:
                    if self.assets_loaded and 'hit_marker' in self.images:
                        canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=self.images['hit_marker'], anchor='center')
                    else: 
                        canvas.create_oval(5, 5, CELL_SIZE-5, CELL_SIZE-5, fill=COLORS['hit_base'], outline='orange')
                elif cell_state == CellState.SUNK_SHIP:
                    if self.assets_loaded and 'sunk_marker' in self.images:
                        canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=self.images['sunk_marker'], anchor='center')
                    else: 
                        canvas.create_rectangle(0, 0, CELL_SIZE, CELL_SIZE, fill=COLORS['sunk_base'], outline=COLORS['border_grid'])
                        canvas.create_text(CELL_SIZE/2, CELL_SIZE/2, text="💀", font=("Arial", 15), fill="white")

    def _draw_ship_part(self, canvas, ship, part_index):
        if not self.assets_loaded or not self.ship_segment_images:
            if ship.orientation == 'horizontal':
                canvas.create_rectangle(0, 5, CELL_SIZE, CELL_SIZE-5, fill=COLORS['ship_deck_base'], outline=COLORS['ship_gun_base'])
                if part_index % 2 == 1: canvas.create_rectangle(10, 12, CELL_SIZE-10, CELL_SIZE-12, fill=COLORS['ship_gun_base'])
            else:
                canvas.create_rectangle(5, 0, CELL_SIZE-5, CELL_SIZE, fill=COLORS['ship_deck_base'], outline=COLORS['ship_gun_base'])
                if part_index % 2 == 1: canvas.create_rectangle(12, 10, CELL_SIZE-12, CELL_SIZE-10, fill=COLORS['ship_gun_base'])
            return

        if ship.orientation == 'horizontal':
            deck_img = self.ship_segment_images['deck_h']
            gun_img = self.ship_segment_images['gun_h']
            canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=deck_img, anchor='center', tags="ship_part")
            if part_index % 2 == 1: 
                canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=gun_img, anchor='center', tags="ship_gun")
        else: # Vertical
            deck_img = self.ship_segment_images['deck_v']
            gun_img = self.ship_segment_images['gun_v']
            canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=deck_img, anchor='center', tags="ship_part")
            if part_index % 2 == 1:
                canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=gun_img, anchor='center', tags="ship_gun")

    def _initialize_shipyard_widgets(self):
        for widget in self.shipyard_frame.winfo_children(): 
            widget.destroy()
        self.shipyard_widgets.clear()
        
        # Helper for shipyard button hover
        def on_enter_ship_lbl(event, ship):
            if not ship.coordinates: # Only show hover effect if not yet placed
                event.widget['background'] = COLORS["button_hover"]
        def on_leave_ship_lbl(event, ship):
            if not ship.coordinates: # Only reset hover effect if not yet placed
                event.widget['background'] = COLORS["ship_deck_base"]
            elif self.selected_ship == ship: # If placed but currently selected, keep highlight
                 event.widget['background'] = COLORS["selection_highlight"]
            else: # If placed and not selected
                 event.widget['background'] = COLORS["ship_deck_placed"]

        for ship in self.game.player_fleet:
            ship_text = f"{ship.name} ({ship.size} ô)" 
            lbl = tk.Label(self.shipyard_frame, text=ship_text, fg=COLORS["text_light"], bg=COLORS["ship_deck_base"], 
                           padx=10, pady=8, cursor="hand2", font=FONTS["label"], relief="flat", bd=0)
            lbl.pack(pady=4, fill="x")
            lbl.bind("<Button-1>", lambda e, s=ship: self.select_ship(s))
            lbl.bind("<Enter>", lambda e, s=ship: on_enter_ship_lbl(e, s))
            lbl.bind("<Leave>", lambda e, s=ship: on_leave_ship_lbl(e, s))
            self.shipyard_widgets[ship.name] = lbl
            
            # If ship was already placed (e.g., during a reset and re-setup), update its initial look
            if ship.coordinates:
                lbl.config(bg=COLORS["ship_deck_placed"], fg=COLORS["text_dark"], cursor="arrow")
                lbl.unbind("<Button-1>")
                lbl.unbind("<Enter>")
                lbl.unbind("<Leave>")
            
        self.ready_button = tk.Button(self.shipyard_outer_frame, text="🚀 SẴN SÀNG", width=15, command=self.start_game, 
                                       bg=COLORS["button_normal"], fg=COLORS["text_light"], font=FONTS["button"], 
                                       relief="flat", padx=5, pady=8, state="disabled")
        self.ready_button.pack(pady=15)
        
        def on_enter_ready_btn(e): 
            if e.widget['state'] == 'normal': e.widget['background'] = COLORS["button_hover"]
        def on_leave_ready_btn(e): 
            if e.widget['state'] == 'normal': e.widget['background'] = COLORS["button_normal"]
            elif e.widget['state'] == 'disabled': e.widget['background'] = COLORS["button_normal"]
        self.ready_button.bind("<Enter>", on_enter_ready_btn)
        self.ready_button.bind("<Leave>", on_leave_ready_btn)

        if all(s.coordinates for s in self.game.player_fleet):
            self.ready_button.config(state="normal", bg=COLORS["button_normal"])
        else:
            self.ready_button.config(state="disabled", bg=COLORS["button_normal"])

    def on_board_hover(self, r, c):
        if not self.selected_ship: return
        self.clear_preview()
        is_placeable = self.game.player_board._is_valid_placement(self.selected_ship.size, r, c, self.placement_orientation)
        color = COLORS["preview_ok"] if is_placeable else COLORS["preview_err"]
        
        preview_segment_img = None
        if self.assets_loaded and self.ship_segment_images:
            if self.placement_orientation == "horizontal":
                preview_segment_img = self.ship_segment_images['deck_h']
            else: 
                preview_segment_img = self.ship_segment_images['deck_v']

        for i in range(self.selected_ship.size):
            row, col = r + (i if self.placement_orientation == "vertical" else 0), c + (i if self.placement_orientation == "horizontal" else 0)
            if 0 <= row < N and 0 <= col < N:
                canvas = self.player_canvas[row][col]
                if preview_segment_img:
                    img_pil = ImageTk.getimage(preview_segment_img) 
                    img_pil_alpha = img_pil.copy()
                    alpha_val = 128 if is_placeable else 80 
                    img_pil_alpha.putalpha(alpha_val) 
                    trans_img = ImageTk.PhotoImage(img_pil_alpha)
                    
                    rect = canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=trans_img, anchor='center', tags="preview_ship")
                    self.preview_coords.append((canvas, rect, trans_img)) 
                else: 
                    rect = canvas.create_rectangle(0,0,CELL_SIZE,CELL_SIZE, fill=color, outline=color, stipple="gray50") 
                    self.preview_coords.append((canvas, rect))
    
    def clear_preview(self):
        for item in self.preview_coords:
            canvas = item[0]
            canvas.delete(item[1]) 
        self.preview_coords = []

    def rotate_ship(self, event):
        if not self.selected_ship: return
        self.placement_orientation = "vertical" if self.placement_orientation == "horizontal" else "horizontal"
        
        x, y = event.x_root, event.y_root 
        
        for r_board in range(N):
            for c_board in range(N):
                canvas = self.player_canvas[r_board][c_board]
                canvas_x, canvas_y = canvas.winfo_rootx(), canvas.winfo_rooty()
                
                if (canvas_x <= x < canvas_x + CELL_SIZE) and \
                   (canvas_y <= y < canvas_y + CELL_SIZE):
                    self.on_board_hover(r_board, c_board)
                    return
        self.clear_preview() 

    def start_game(self):
        self.play_sound('click')
        if self.selected_ship and self.selected_ship.name in self.shipyard_widgets:
            prev_ship_lbl = self.shipyard_widgets[self.selected_ship.name]
            if not self.selected_ship.coordinates: # If it was selected but not placed
                prev_ship_lbl.config(relief="flat", bg=COLORS["ship_deck_base"], bd=0)
            # If it was selected AND placed, its color is already ship_deck_placed
        self.selected_ship = None
        self.clear_preview()
        
        self.ready_button.config(state="disabled", bg=COLORS["button_normal"])
        self.shipyard_outer_frame.destroy() 
        
        self.game.start_battle() 
        self.update_boards()
        self.status_label.config(text="Trận chiến bắt đầu! Đến lượt bạn bắn!")

if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()