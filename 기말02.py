import os
import random
import tkinter as tk


class HangmanV2:

    def __init__(self, root):
        self.root = root
        self.root.title("HANGMAN v0.2 - 단어장 & 정답 입력창 추가")
        self.root.geometry("560x640")
        self.root.resizable(False, False)
        self.root.configure(bg="#0F172A")

        # [2단계 추가] 외부 파일(words.txt)에서 단어장 불러오기
        self.word_file = "words.txt"
        self.word_pool = self.load_words()

        self.secret_word = ""
        self.guessed_letters = set()
        self.wrong_count = 0
        self.max_attempts = 6
        self.score = 0
        self.combo = 0
        self.is_game_over = False
        self.letter_buttons = {}

        # 상단 점수 및 콤보 전광판
        board = tk.Frame(root, bg="#1E293B", padx=15, pady=10)
        board.pack(fill="x", padx=20, pady=(15, 5))
        self.score_label = tk.Label(
            board, text="SCORE: 0", font=("Consolas", 12, "bold"), bg="#1E293B", fg="#10B981"
        )
        self.score_label.pack(side=tk.LEFT)
        self.combo_label = tk.Label(
            board, text="0 COMBO", font=("Consolas", 12, "bold"), bg="#1E293B", fg="#FACC15"
        )
        self.combo_label.pack(side=tk.RIGHT)

        self.info_label = tk.Label(
            root, text="", font=("맑은 고딕", 11, "bold"), bg="#0F172A", fg="white"
        )
        self.info_label.pack(pady=8)

        self.canvas = tk.Canvas(
            root, width=250, height=185, bg="#1E293B", highlightthickness=0
        )
        self.canvas.pack(pady=5)

        self.word_label = tk.Label(
            root, text="", font=("Consolas", 26, "bold"), bg="#0F172A", fg="white"
        )
        self.word_label.pack(pady=6)

        # [2단계 추가] 정답 직접 입력창 및 자유 탈출(Esc/취소/외부클릭) 구현
        direct_frame = tk.Frame(root, bg="#1E293B", padx=10, pady=6)
        direct_frame.pack(pady=(2, 8))
        tk.Label(
            direct_frame, text="✍️ 정답 입력:", font=("맑은 고딕", 9, "bold"),
            bg="#1E293B", fg="#FACC15"
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.answer_entry = tk.Entry(
            direct_frame, width=15, font=("Consolas", 12, "bold"),
            bg="#334155", fg="white", insertbackground="white", relief="flat"
        )
        self.answer_entry.pack(side=tk.LEFT, padx=(0, 6), ipady=2)
        self.answer_entry.bind("<Return>", lambda e: self.submit_full_word())
        self.answer_entry.bind("<Escape>", self.release_entry_focus)

        self.submit_btn = tk.Button(
            direct_frame, text="제출", font=("맑은 고딕", 9, "bold"),
            bg="#10B981", fg="#0F172A", relief="flat", padx=8, pady=2,
            command=self.submit_full_word
        )
        self.submit_btn.pack(side=tk.LEFT, padx=(0, 4))

        tk.Button(
            direct_frame, text="취소(Esc)", font=("맑은 고딕", 8),
            bg="#334155", fg="#94A3B8", relief="flat", padx=6, pady=2,
            command=self.release_entry_focus
        ).pack(side=tk.LEFT)

        # 알파벳 버튼 키보드
        kb_frame = tk.Frame(root, bg="#0F172A")
        kb_frame.pack(pady=6)
        for idx, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            btn = tk.Button(
                kb_frame, text=ch, width=4, font=("Consolas", 11, "bold"),
                bg="#334155", fg="white", relief="flat",
                command=lambda c=ch: self.on_letter_click(c),
            )
            btn.grid(row=idx // 9, column=idx % 9, padx=3, pady=3)
            self.letter_buttons[ch] = btn

        self.next_btn = tk.Button(
            root, text="▶ 다음 스테이지", font=("맑은 고딕", 10, "bold"),
            bg="#38BDF8", fg="#0F172A", relief="flat", width=24, pady=6,
            command=self.start_round,
        )
        self.next_btn.pack(pady=10)

        self.root.bind("<Key>", self.handle_keypress)
        self.root.bind("<Button-1>", self.handle_global_click)
        self.start_round()

    def load_words(self):
        default_words = ["PYTHON", "KEYBOARD", "ALGORITHM", "DATABASE", "NETWORK"]
        if not os.path.exists(self.word_file):
            with open(self.word_file, "w", encoding="utf-8") as f:
                f.write("\n".join(default_words))
            return default_words
        with open(self.word_file, "r", encoding="utf-8") as f:
            words = [line.strip().upper() for line in f if line.strip().isalpha()]
        return words if words else default_words

    def handle_global_click(self, event):
        if not isinstance(event.widget, tk.Entry):
            self.root.focus_set()

    def release_entry_focus(self, event=None):
        self.answer_entry.delete(0, tk.END)
        self.root.focus_set()

    def start_round(self):
        self.secret_word = random.choice(self.word_pool)
        self.guessed_letters.clear()
        self.wrong_count = 0
        self.is_game_over = False

        self.info_label.config(text=f"단어를 추리하세요! (총 {len(self.secret_word)}글자)", fg="white")
        self.word_label.config(fg="white")
        self.draw_gallows()
        self.update_word_display()
        self.set_inputs("normal")
        self.root.focus_set()

    def on_letter_click(self, ch):
        self.root.focus_set()
        self.guess_letter(ch)

    def guess_letter(self, letter):
        if self.is_game_over:
            return
        self.letter_buttons[letter].config(state="disabled", bg="#1E293B")
        self.guessed_letters.add(letter)

        if letter in self.secret_word:
            self.update_word_display()
            self.combo += 1
            self.score += 100 * self.combo
            self.update_scoreboard()
            if set(self.secret_word).issubset(self.guessed_letters):
                self.finish_round(True, "🎉 스테이지 클리어!")
        else:
            self.apply_wrong(f"'{letter}' 없음!")

    def submit_full_word(self):
        if self.is_game_over:
            return
        typed = self.answer_entry.get().strip().upper()
        self.release_entry_focus()
        if not typed:
            return
        if typed == self.secret_word:
            self.score += 500
            self.update_scoreboard()
            self.finish_round(True, "🎯 한 번에 정답 적중! (+500점)")
        else:
            self.apply_wrong(f"'{typed}' 오답!")

    def apply_wrong(self, msg):
        self.wrong_count += 1
        self.combo = 0
        self.update_scoreboard()
        self.draw_hangman_part(self.wrong_count)
        rem = self.max_attempts - self.wrong_count
        self.info_label.config(text=f"❌ {msg} 남은 기회: {rem}번", fg="#F43F5E")
        if self.wrong_count >= self.max_attempts:
            self.finish_round(False, f"💀 게임 오버! 정답: {self.secret_word}")

    def finish_round(self, is_win, msg):
        self.is_game_over = True
        self.set_inputs("disabled")
        color = "#10B981" if is_win else "#F43F5E"
        self.word_label.config(text=" ".join(self.secret_word), fg=color)
        self.info_label.config(text=msg, fg=color)
        if not is_win:
            self.score = 0
            self.combo = 0
            self.update_scoreboard()

    def update_scoreboard(self):
        self.score_label.config(text=f"SCORE: {self.score}")
        self.combo_label.config(text=f"{self.combo} COMBO")

    def set_inputs(self, state):
        bg = "#334155" if state == "normal" else "#1E293B"
        for btn in self.letter_buttons.values():
            btn.config(state=state, bg=bg)
        self.answer_entry.config(state=state)
        self.submit_btn.config(state=state)

    def handle_keypress(self, event):
        if isinstance(event.widget, tk.Entry) or self.is_game_over:
            return
        ch = event.char.upper()
        if ch in self.letter_buttons and ch not in self.guessed_letters:
            self.guess_letter(ch)

    def update_word_display(self):
        self.word_label.config(
            text=" ".join(c if c in self.guessed_letters else "_" for c in self.secret_word)
        )

    def draw_gallows(self):
        self.canvas.delete("all")
        self.canvas.create_line(45, 168, 140, 168, width=4, fill="#64748B")
        self.canvas.create_line(92, 168, 92, 18, width=4, fill="#64748B")
        self.canvas.create_line(92, 18, 180, 18, width=4, fill="#64748B")
        self.canvas.create_line(180, 18, 180, 40, width=3, fill="#94A3B8")

    def draw_hangman_part(self, step):
        c = "#F43F5E"
        if step == 1: self.canvas.create_oval(162, 40, 198, 76, width=3, outline=c)
        elif step == 2: self.canvas.create_line(180, 76, 180, 124, width=3, fill=c)
        elif step == 3: self.canvas.create_line(180, 90, 155, 114, width=3, fill=c)
        elif step == 4: self.canvas.create_line(180, 90, 205, 114, width=3, fill=c)
        elif step == 5: self.canvas.create_line(180, 124, 160, 156, width=3, fill=c)
        elif step == 6: self.canvas.create_line(180, 124, 200, 156, width=3, fill=c)


if __name__ == "__main__":
    root = tk.Tk()
    HangmanV2(root)
    root.mainloop()