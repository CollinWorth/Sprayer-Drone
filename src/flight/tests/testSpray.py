import tkinter as tk
import pyautogui
import time

SPRAY_DURATION = 2.0

print("=== SETUP ===")
print("1. Open QGC -> Actuators -> enable sliders")
print("2. Hover your mouse over the TOP of the Actuator Set 1 slider, press Enter")
input("Ready? Press Enter: ")
on_x, on_y = pyautogui.position()
print(f"ON position: {on_x}, {on_y}")

print("Now hover over the BOTTOM of that same slider, press Enter")
input("Ready? Press Enter: ")
off_x, off_y = pyautogui.position()
print(f"OFF position: {off_x}, {off_y}\n")
print("Setup done. Use the SPRAY button.\n")


saved_pos = (0, 0)


def refocus():
    # Click the spray window's own padding area (top-left corner, outside the button)
    wx = root.winfo_rootx() + 5
    wy = root.winfo_rooty() + 5
    pyautogui.moveTo(wx, wy)
    pyautogui.click()
    root.focus_force()


def do_spray(event=None):
    global saved_pos
    if btn["state"] == "disabled":
        return
    saved_pos = pyautogui.position()
    btn.config(state="disabled", bg="#888888", text="SPRAYING...")
    pyautogui.click(on_x, on_y)
    pyautogui.moveTo(*saved_pos)
    root.after(400, refocus)
    root.after(int(SPRAY_DURATION * 1000), stop_spray)


def stop_spray():
    pyautogui.click(off_x, off_y)
    pyautogui.moveTo(*saved_pos)
    btn.config(state="normal", bg="#cc0000", text="SPRAY")
    root.after(400, refocus)


root = tk.Tk()
root.title("Spray Control")
root.geometry("400x250")
root.configure(bg="#111111")
root.resizable(False, False)

btn = tk.Button(
    root, text="SPRAY",
    font=("Arial", 60, "bold"),
    bg="#cc0000", fg="white",
    activebackground="#ff3333",
    relief="flat", cursor="hand2",
    command=do_spray
)
btn.pack(expand=True, fill="both", padx=20, pady=20)

root.bind("<space>", do_spray)

root.lift()
root.attributes("-topmost", True)
root.focus_force()

root.mainloop()
