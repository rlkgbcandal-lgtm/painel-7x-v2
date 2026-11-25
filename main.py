
import tkinter as tk
from tkinter import ttk, messagebox
from pynput import keyboard, mouse
import pydirectinput
import threading
import time
import json
import os

CONFIG = "config.json"

DEFAULT = {
    "mode": "soltar",
    "steps": [
        {"key": "scroll down", "ms": 120},
        {"key": "e", "ms": 120},
        {"key": "q", "ms": 120},
        {"key": "mouse1", "ms": 120}
    ],
    "correr_ms": 300
}

def load_config():
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            data = json.load(f)
        if len(data["steps"]) != 4:
            return DEFAULT.copy()
        return data
    except Exception:
        return DEFAULT.copy()

class MacroMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("7X MACRO MENU")
        self.root.geometry("550x590")
        self.root.resizable(False, False)
        self.root.configure(bg="#101114")

        self.config = load_config()
        self.lite_on = False
        self.lite_busy = False
        self.correr_on = False
        self.pressed_keys = set()
        self.capture_index = None
        self.lock = threading.Lock()

        self.mode = tk.StringVar(value=self.config["mode"])
        self.keys = [tk.StringVar(value=s["key"]) for s in self.config["steps"]]
        self.times = [tk.StringVar(value=str(s["ms"])) for s in self.config["steps"]]
        self.correr_ms = tk.StringVar(value=str(self.config["correr_ms"]))

        self.build()
        self.start_listeners()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build(self):
        tk.Label(
            self.root, text="7X MACRO MENU",
            bg="#101114", fg="#f5c542",
            font=("Segoe UI", 23, "bold")
        ).pack(pady=(18, 2))

        tk.Label(
            self.root, text="PAINEL DE MACROS • MTA",
            bg="#101114", fg="#888888",
            font=("Segoe UI", 8, "bold")
        ).pack(pady=(0, 15))

        panel = tk.Frame(self.root, bg="#1b1d22", padx=16, pady=13)
        panel.pack(fill="x", padx=20)

        tk.Label(panel, text="LITE FOOT", bg="#1b1d22",
                 fg="#f5c542", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        tk.Label(panel, text="Ativação pelo Mouse 2",
                 bg="#1b1d22", fg="#aaaaaa").pack(anchor="w", pady=(2, 8))

        row = tk.Frame(panel, bg="#1b1d22")
        row.pack(anchor="w", pady=4)

        tk.Label(row, text="Ativar ao:", bg="#1b1d22",
                 fg="white").pack(side="left")

        ttk.Combobox(
            row, textvariable=self.mode,
            values=["pressionar", "soltar"],
            state="readonly", width=14
        ).pack(side="left", padx=8)

        tk.Label(panel, text="SEQUÊNCIA DE 4 ETAPAS",
                 bg="#1b1d22", fg="white",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(12, 5))

        for i in range(4):
            row = tk.Frame(panel, bg="#1b1d22")
            row.pack(fill="x", pady=4)

            tk.Label(row, text=f"ETAPA {i+1}",
                     bg="#1b1d22", fg="#f5c542",
                     width=9, anchor="w").pack(side="left")

            entry = tk.Entry(
                row, textvariable=self.keys[i],
                width=18, justify="center",
                bg="#292c33", fg="white",
                insertbackground="white", relief="flat"
            )
            entry.pack(side="left", padx=5, ipady=5)
            entry.bind("<Button-1>",
                       lambda event, index=i: self.capture(index))
            entry.bind("<Key>", lambda event: "break")

            tk.Label(row, text="MS", bg="#1b1d22",
                     fg="#aaaaaa").pack(side="left", padx=3)

            tk.Entry(
                row, textvariable=self.times[i],
                width=7, justify="center",
                bg="#292c33", fg="white",
                insertbackground="white", relief="flat"
            ).pack(side="left", ipady=5)

        buttons = tk.Frame(panel, bg="#1b1d22")
        buttons.pack(anchor="w", pady=(12, 0))

        self.lite_button = tk.Button(
            buttons, text="LIGAR LITE FOOT",
            command=self.toggle_lite,
            bg="#f5c542", fg="#111111",
            relief="flat", padx=14, pady=8
        )
        self.lite_button.pack(side="left", padx=(0, 8))

        tk.Button(
            buttons, text="SALVAR",
            command=self.save,
            bg="#343740", fg="white",
            relief="flat", padx=14, pady=8
        ).pack(side="left")

        correr = tk.Frame(self.root, bg="#1b1d22", padx=16, pady=13)
        correr.pack(fill="x", padx=20, pady=13)

        tk.Label(correr, text="CORRER",
                 bg="#1b1d22", fg="#f5c542",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")

        tk.Label(correr, text="Ativa enquanto W, A, S ou D estiver pressionada.",
                 bg="#1b1d22", fg="#aaaaaa").pack(anchor="w", pady=4)

        row = tk.Frame(correr, bg="#1b1d22")
        row.pack(anchor="w", pady=5)

        tk.Label(row, text="INTERVALO MS",
                 bg="#1b1d22", fg="white").pack(side="left")

        tk.Entry(row, textvariable=self.correr_ms,
                 width=8, bg="#292c33", fg="white",
                 insertbackground="white", relief="flat",
                 justify="center").pack(side="left", padx=8, ipady=5)

        self.correr_button = tk.Button(
            row, text="LIGAR CORRER",
            command=self.toggle_correr,
            bg="#343740", fg="white",
            relief="flat", padx=14, pady=8
        )
        self.correr_button.pack(side="left")

        self.status = tk.StringVar(value="Pronto para usar")
        tk.Label(self.root, textvariable=self.status,
                 bg="#101114", fg="#cccccc").pack(anchor="w", padx=23)

        tk.Label(self.root,
                 text="Uma sequência por ativação • Ajuste os MS conforme seu FPS",
                 bg="#101114", fg="#777777",
                 font=("Segoe UI", 8)).pack(pady=10)

    def capture(self, index):
        self.capture_index = index
        self.status.set("Pressione a tecla que deseja configurar.")

    def start_listeners(self):
        self.k_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.m_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.k_listener.start()
        self.m_listener.start()

    def on_key_press(self, key):
        if self.capture_index is not None:
            name = self.key_name(key)
            index = self.capture_index
            self.capture_index = None
            self.root.after(0, lambda: self.keys[index].set(name))
            self.root.after(0, lambda: self.status.set("Tecla configurada: " + name))
            return

        name = self.key_name(key).lower()
        if name in ("w", "a", "s", "d"):
            with self.lock:
                self.pressed_keys.add(name)

    def on_key_release(self, key):
        name = self.key_name(key).lower()
        with self.lock:
            self.pressed_keys.discard(name)

    @staticmethod
    def key_name(key):
        if isinstance(key, keyboard.KeyCode):
            return key.char if key.char else str(key)
        return str(key).replace("Key.", "")

    def on_mouse_click(self, x, y, button, pressed):
        if button != mouse.Button.right or not self.lite_on:
            return

        mode = self.mode.get()
        if (mode == "pressionar" and pressed) or (mode == "soltar" and not pressed):
            self.start_sequence()

    def start_sequence(self):
        if self.lite_busy:
            return
        self.lite_busy = True
        steps = []
        try:
            for i in range(4):
                steps.append((
                    self.keys[i].get().strip().lower(),
                    int(self.times[i].get())
                ))
        except ValueError:
            self.lite_busy = False
            self.root.after(0, lambda: self.status.set("Confira os valores de MS."))
            return

        threading.Thread(
            target=self.run_sequence,
            args=(steps,),
            daemon=True
        ).start()

    def run_sequence(self, steps):
        try:
            for key, ms in steps:
                if ms < 0 or ms > 5000:
                    raise ValueError("MS deve estar entre 0 e 5000.")

                if key in ("scroll down", "scrolldown"):
                    pydirectinput.scroll(-1)
                elif key in ("scroll up", "scrollup"):
                    pydirectinput.scroll(1)
                elif key in ("mouse1", "soco"):
                    pydirectinput.click(button="left")
                elif key in ("mouse2",):
                    pydirectinput.click(button="right")
                else:
                    pydirectinput.press(key)

                time.sleep(ms / 1000)

        except Exception as error:
            self.root.after(0, lambda: self.status.set("Erro: " + str(error)))
        finally:
            self.lite_busy = False

    def toggle_lite(self):
        self.lite_on = not self.lite_on
        self.lite_button.config(
            text="DESLIGAR LITE FOOT" if self.lite_on else "LIGAR LITE FOOT",
            bg="#2c9b62" if self.lite_on else "#f5c542",
            fg="white" if self.lite_on else "#111111"
        )
        self.status.set("Lite Foot ligado" if self.lite_on else "Lite Foot desligado")

    def toggle_correr(self):
        self.correr_on = not self.correr_on
        if self.correr_on:
            self.correr_button.config(text="DESLIGAR CORRER", bg="#2c9b62")
            threading.Thread(target=self.correr_loop, daemon=True).start()
            self.status.set("Correr ligado")
        else:
            self.correr_button.config(text="LIGAR CORRER", bg="#343740")
            self.status.set("Correr desligado")

    def correr_loop(self):
        while self.correr_on:
            with self.lock:
                moving = bool(self.pressed_keys)
            if moving:
                try:
                    delay = max(10, min(5000, int(self.correr_ms.get())))
                    pydirectinput.scroll(1)
                    time.sleep(delay / 1000)
                except Exception:
                    self.root.after(0, lambda: self.status.set("Intervalo inválido."))
                    self.correr_on = False
            else:
                time.sleep(0.01)

    def save(self):
        try:
            steps = []
            for i in range(4):
                key = self.keys[i].get().strip().lower()
                ms = int(self.times[i].get())
                if not key or ms < 0 or ms > 5000:
                    raise ValueError("Confira as teclas e os MS.")
                steps.append({"key": key, "ms": ms})

            correr_ms = int(self.correr_ms.get())
            if correr_ms < 10 or correr_ms > 5000:
                raise ValueError("Correr: use de 10 a 5000 MS.")

            data = {
                "mode": self.mode.get(),
                "steps": steps,
                "correr_ms": correr_ms
            }

            with open(CONFIG, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            self.status.set("Configurações salvas!")
        except Exception as error:
            messagebox.showerror("7X MACRO MENU", str(error))

    def close(self):
        self.lite_on = False
        self.correr_on = False
        self.k_listener.stop()
        self.m_listener.stop()
        self.root.destroy()


if __name__ == "__main__":
    pydirectinput.PAUSE = 0
    root = tk.Tk()
    MacroMenu(root)
    root.mainloop()
