from customtkinter import *
from PIL import Image
import threading, socket, base64, io
from tkinter import filedialog


class MainWindow(CTk):
    def __init__(self, username, server, port):
        super().__init__()
        self.geometry("500x400")
        self.label = None
        self.username = username
        self.chat_field = CTkScrollableFrame(self)
        self.chat_field.place(x=0, y=0)
        self.mesasge_entry = CTkEntry(
            self, placeholder_text="введіть ваше повідомлення", height=40
        )
        self.mesasge_entry.place(x=0, y=0)
        self.send_message = CTkButton(
            self, text=">", width=50, height=40, command=self.send_msg
        )
        self.send_message.place(x=0, y=0)
        self.send_image = CTkButton(
            self, text="📁", width=50, height=40, command=self.open_img
        )
        self.send_image.place(x=0, y=0)

        self.raw = None
        self.file_name = None
        self.image_to_send = CTkLabel(self, text="")
        self.image_to_send.bind("<Button-1>", self.remove_image)
        self.adaptive_ui()

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((str(server), int(port)))
            hello = (
                f"TEXT@{self.username}@[SYSTEM] {self.username} підключився до чату!\n"
            )
            self.socket.sendall(hello.encode("utf-8"))
            threading.Thread(target=self.recieve_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"Не вдалось підключитися до сервера: {e}")

    def remove_image(self, e=None):
        self.image_to_send.place_forget()
        self.raw = None
        self.file_name = None

    def adaptive_ui(self):
        self.send_message.place(
            x=self.winfo_width() - 50, y=self.winfo_height() - 40
        )
        self.send_image.place(
            x=self.winfo_width()  - 105, y=self.winfo_height() - 40
        )
        self.mesasge_entry.place(x=0, y=self.winfo_height()   - 40)
        self.mesasge_entry.configure(width=self.winfo_width()  - 110)
        self.chat_field.configure(
            width=self.winfo_width()  - 20,
            height=self.winfo_height()  - 55,
        )
        if self.raw:
            self.image_to_send.configure(
                image=CTkImage(Image.open(self.file_name), size=(100, 100))
            )
            self.image_to_send.place(x=20, y=self.mesasge_entry.winfo_y()  - 100)
        self.after(100, self.adaptive_ui)

    def add_message(self, message, img=None):
        message_frame = CTkFrame(self.chat_field, fg_color="#636363")
        message_frame.pack(pady=5, anchor="w")
        wrap = self.winfo_width() - 40
        if not img:
            CTkLabel(
                message_frame,
                text=message,
                wraplength=wrap,
                justify="left",
                text_color="white",
            ).pack(padx=10, pady=5)
        else:
            CTkLabel(
                message_frame,
                text=message,
                wraplength=wrap,
                justify="left",
                image=img,
                compound="top",
                text_color="white",
            ).pack(padx=10, pady=5)

    def send_msg(self):
        message = self.mesasge_entry.get()
        if message and not self.raw:
            self.add_message(f"{self.username}: {message}")
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.socket.sendall(data.encode())
            except:
                pass
        elif self.raw:
            b64_data = base64.b64encode(self.raw).decode()
            data = f"IMAGE@{self.username}@{message}@{b64_data}\n"
            try:
                self.socket.sendall(data.encode())
            except:
                pass
            self.add_message(
                f"{self.username}: {message}",
                img=self.resize_img(Image.open(self.file_name)),
            )
            self.remove_image()
        self.mesasge_entry.delete(0, "end")

    def resize_img(self, image):
        width, height = image.size
        max_width = 400
        max_height = 400
        if width < max_width:
            if height < max_height:
                return CTkImage(image, size=(width, height))
            else:
                max_width = int((max_height * width) / height)
        max_height = int((max_width * height) / width)
        resized_img = image.resize((max_width, max_height), Image.Resampling.LANCZOS)
        return CTkImage(resized_img, size=(max_width, max_height))

    def open_img(self):
        self.file_name = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if not self.file_name:
            return
        try:
            with open(self.file_name, "rb") as f:
                self.raw = f.read()
            return self.raw
        except Exception as e:
            self.add_message(f"Помилка: {e}")

    def recieve_message(self):
        buffer = ""
        while True:
            try:
                message = self.socket.recv(16384)
                buffer += message.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    print(f"LINE: {line}")
                    self.handle_line(line.strip())
            except:
                break
        self.socket.close()

    def handle_line(self, line):
        print(1)
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]
        if msg_type == "TEXT":
            self.add_message(f"{parts[1]}: {parts[2]}")
        elif msg_type == "IMAGE":
            try:
                image_data = base64.b64decode(parts[3])
                img = Image.open(io.BytesIO(image_data))
                img = self.resize_img(img)
                self.add_message(f"{parts[1]}: {parts[2]}", img=img)
            except Exception as e:
                self.add_message(f"Помилка: {e}")