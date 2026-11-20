import random
import tkinter as tk


class HangmanV1:

    def __init__(self, root):
        self.root = root
        self.root.title("HANGMAN v0.1 - 기본 GUI 버전")
        self.root.geometry("540x560")
        self.root.resizable(False, False)
        self.root.configure(bg="#0F172A")

        # 1단계에서는 코드 내부 리스트에 기본 단어만 넣어 테스트합니다.
        self.word_pool = ["PYTHON", "KEYBOARD", "ALGORITHM", "DATABASE", "NETWORK"]
        self.secret_word = ""
        self.guessed_letters = set()
        self.wrong_count = 0
        self.max_attempts = 6
        self.is_game_over = False
        self.letter_buttons = {}

        # UI 화면 구성
        self.info_label = tk.Label(
            root, text="", font=("맑은 고딕", 12, "bold"), bg="#0F172A", fg="white"
        )
        self.info_label.pack(pady=(20, 10))

        self.canvas = tk.Canvas(
            root, width=250, height=185, bg="#1E293B", highlightthickness=0
        )
        self.canvas.pack(pady=5)

        self.word_label = tk.Label(
            root, text="", font=("Consolas", 26, "bold"), bg="#0F172A", fg="white"
        )
        self.word_label.pack(pady=15)

        # 알파벳 A~Z 버튼 배치
        kb_frame = tk.Frame(root, bg="#0F172A")
        kb_frame.pack(pady=10)
        for idx, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            btn = tk.Button(
                kb_frame, text=ch, width=4, font=("Consolas", 11, "bold"),
                bg="#334155", fg="white", relief="flat",
                command=lambda c=ch: self.guess_letter(c),
            )
            btn.grid(row=idx // 9, column=idx % 9, padx=3, pady=3)
            self.letter_buttons[ch] = btn

        self.restart_btn = tk.Button(
            root, text="🔄 새 단어 시작", font=("맑은 고딕", 10, "bold"),
            bg="#38BDF8", fg="#0F172A", relief="flat", width=20, pady=6,
            command=self.start_round,
        )
        self.restart_btn.pack(pady=15)

        self.root.bind("<Key>", self.handle_keypress)
        self.start_round()

    def start_round(self):
        self.secret_word = random.choice(self.word_pool)
        self.guessed_letters.clear()
        self.wrong_count = 0
        self.is_game_over = False

        self.info_label.config(
            text=f"영단어를 추리하세요! ({len(self.secret_word)}글자)", fg="white"
        )
        self.word_label.config(fg="white")
        self.draw_gallows()
        self.update_word_display()
        for btn in self.letter_buttons.values():
            btn.config(state="normal", bg="#334155")

    def guess_letter(self, letter):
        if self.is_game_over:
            return
        self.letter_buttons[letter].config(state="disabled", bg="#1E293B")
        self.guessed_letters.add(letter)

        if letter in self.secret_word:
            self.update_word_display()
            if set(self.secret_word).issubset(self.guessed_letters):
                self.is_game_over = True
                self.word_label.config(fg="#10B981")
                self.info_label.config(text="🎉 정답입니다! 클리어!", fg="#10B981")
        else:
            self.wrong_count += 1
            self.draw_hangman_part(self.wrong_count)
            rem = self.max_attempts - self.wrong_count
            self.info_label.config(text=f"❌ '{letter}' 없음! 남은 기회: {rem}번", fg="#F43F5E")
            if self.wrong_count >= self.max_attempts:
                self.is_game_over = True
                self.word_label.config(text=" ".join(self.secret_word), fg="#F43F5E")
                self.info_label.config(text=f"💀 실패! 정답: {self.secret_word}", fg="#F43F5E")

    def handle_keypress(self, event):
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
    HangmanV1(root)
    root.mainloop()