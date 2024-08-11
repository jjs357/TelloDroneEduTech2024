#sample student code for Image Recognition

# Made by Jacob Funston PVCC

import cv2
from djitellopy import Tello
import time
import threading
import asyncio
import tkinter as tk
import dummy_tello
import sys
from PIL import Image, ImageTk
import os
import json

import base64
import requests

USE_DUMMY_TELLO = False
USE_DEBUG_WITH_DUMMY = False
EMERGENCY_HOLD_TIME = 1000

api_key = ""
headers = {
  "Content-Type": "application/json",
  "Authorization": f"Bearer {api_key}"
}

force_out = sys.stdout


def vprint(*values, sep=" ", end="\n", file=None, flush=False):
    file = file if file else force_out
    print(*values, sep=sep, end=end, file=file, flush=flush)

move_queue = asyncio.Queue()
running_main_move = asyncio.Event()
running_main_move.set()

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

async def run_com(com, dist):
    com(dist)

async def main_move(drone: Tello):
    task: asyncio.Task = None
    if not drone:
        print("Drone passed to main_move was null!")
        running_main_move.clear()
    while running_main_move.is_set():
        if not move_queue.empty():
            if (not task) or task.done():
                if task:
                    await task
                command, dist = move_queue.get_nowait()
                targ = getattr(drone, command, lambda n, d=command : print(f"Invalid Drone Direction '{d}' - distance = {n}"))
                if not targ:
                    return
                task = asyncio.create_task(run_com(targ, (min(max(dist, 20), 500))))
            await asyncio.sleep(0.3)
        await asyncio.sleep(0.1)

class LogWindow(tk.Frame):
    def __init__(self, parent, tb_width, tb_height, **kwargs):
        tk.Frame.__init__(self, parent,**kwargs)
        ################# self configure ##########################
        #self.rowconfigure(0, weight=1)
        #self.columnconfigure(0, weight=1)
        self.text_box = tk.Text(self, wrap=None, bg="black", font="Consolas 8", width=tb_width, height=tb_height)
        self.text_box.grid(row=0, column=0, sticky="nsew")

        self.scroller = tk.Scrollbar(self, command=self.text_box.yview, orient="vertical")
        self.text_box.configure(yscrollcommand=self.scroller.set)
        self.scroller.grid(row=0, column=1, sticky="nse")

        self.text_box.tag_configure("info", foreground="gray")
        self.text_box.tag_configure("error", foreground="red")
        self.text_box.tag_configure("warning", foreground="yellow")
        self.text_box.tag_configure("message", foreground="white")

        self.mute_info = False
        self.mute_warning = False
        self.mute_error = False
        self.mute_message = False

    def write(self, text: str):
        self.write_info(text)

    def flush(self):
        pass
        
    def write_message(self, text):
        if self.mute_message: return
        self.text_box.insert("end", text + "\n", "message")
        self.text_box.see("end")
    def write_info(self, text):
        if self.mute_info: return
        self.text_box.insert("end", text + "\n", "info")
        self.text_box.see("end")
    def write_error(self, text):
        if self.mute_error: return
        self.text_box.insert("end", text + "\n", "error")
        self.text_box.see("end")
    def write_warning(self, text):
        if self.mute_warning: return
        self.text_box.insert("end", text + "\n", "warning")
        self.text_box.see("end")
        
class win:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Drone GUI")
        self.root.geometry("800x320")
        self.root.resizable(False, False)

        self.eb_enter = 0

        self.loggerWin = LogWindow(self.root, 60, 10)
        sys.stdout = self.loggerWin
        vprint("Log Window Setup. To write to terminal, please use 'vprint'")
            
        self.dummyTelloClass = dummy_tello.DummyTello

        self.control_win = tk.Frame(self.root)

        self.save_image_flag = False

        self.recording = False

        self.take_off_button = tk.Button(self.control_win, command=self.take_off, text="Take Off")
        self.land_button = tk.Button(self.control_win, command=self.land, text="Land", state="disabled")
        self.start_stream_button = tk.Button(self.control_win, command=self.start_stream, text="Start Stream", state="disabled")
        self.save_image_button = tk.Button(self.control_win, command=self.set_image_flag, text="Save Image", state="disabled")
        self.stop_stream_button = tk.Button(self.control_win, command=self.stop_stream, text="Stop Stream", state="disabled")
        self.ai_button = tk.Button(self.control_win, command=self.ai_describe_most_recent_snap, text="Sumbit Snap To AI", state="disabled")


        self.take_off_button.grid(row=0, column=0, sticky="NSEW")
        self.land_button.grid(row=1, column=0, sticky="NSEW")
        self.start_stream_button.grid(row=2, column=0, sticky="NSEW")
        self.save_image_button.grid(row=3, column=0, sticky="NSEW")
        self.stop_stream_button.grid(row=4, column=0, sticky="NSEW")
        self.ai_button.grid(row=5, column=0, sticky="NSEW")

        self.move_win = tk.Frame(self.root)

        self.horizontal_move_win = tk.Frame(self.move_win)

        self.horizontal_move_spacer = tk.Label(self.horizontal_move_win, relief="raised")

        self.move_forward_button = tk.Button(self.horizontal_move_win, text="FORW", command=lambda *_ : self.move_drone("move_forward", 60), state="disabled")
        self.move_back_button = tk.Button(self.horizontal_move_win, text="BACK", command=lambda *_ : self.move_drone("move_back", 60), state="disabled")
        self.move_left_button = tk.Button(self.horizontal_move_win, text="LEFT", command=lambda *_ : self.move_drone("rotate_counter_clockwise", 30), state="disabled")
        self.move_right_button = tk.Button(self.horizontal_move_win, text="RIGHT", command=lambda *_ : self.move_drone("rotate_clockwise", 30), state="disabled")

        self.move_forward_button.grid(row=0, column=1, sticky="NSEW")
        self.move_back_button.grid(row=2, column=1, sticky="NSEW")
        self.move_left_button.grid(row=1, column=0, sticky="NSEW")
        self.move_right_button.grid(row=1, column=2, sticky="NSEW")

        self.horizontal_move_spacer.grid(row=1, column=1, sticky="NSEW")

        self.vert_move_win = tk.Frame(self.move_win)

        self.vert_forward_spacer = tk.Label(self.vert_move_win, relief="raised")
        
        self.move_up_button = tk.Button(self.vert_move_win, text="Z+", command=lambda *_ : self.move_drone("move_up", 60), state="disabled")
        self.move_down_button = tk.Button(self.vert_move_win, text="Z-", command=lambda *_ : self.move_drone("move_down", 60), state="disabled")
        self.move_up_button.grid(row=0, column=0, sticky="NSEW")
        self.vert_forward_spacer.grid(row=1, column=0, sticky="NSEW")
        self.move_down_button.grid(row=2, column=0, sticky="NSEW")

        self.horizontal_move_win.pack(side="left")
        self.vert_move_win.pack(side="left")

        self.control_win.grid(row=0, column=0)
        self.move_win.grid(row=0, column=1)
        self.loggerWin.grid(row=1, column=0, columnspan=3)

        self.em_schedule = None

        self.emergency_stop_button_image_raw = tk.PhotoImage(file=r"emergency.png")
        self.emergency_stop_button_image = self.emergency_stop_button_image_raw.subsample(16, 16)
        self.emergency_stop_button = tk.Button(self.root, image=self.emergency_stop_button_image, width=60, height=60, state="disabled")
        self.emergency_stop_button.bind("<ButtonPress-1>", self.em_time)
        self.emergency_stop_button.bind("<ButtonRelease-1>", self.em_leave)

        self.emergency_stop_button.grid(column=2, row=0)

        self.drone: Tello = None

        self.view = None
        self.display_frame = None
        self.display = tk.Canvas(self.root, width=400, height=300, background="#FF00FF")

        self.display.grid(row=0, column=4, rowspan=3)

        self.record_wait = threading.Event()

        def safe_close(*_, **__):
            running_main_move.clear()
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", safe_close)

        self.load_drone()

        self.task = None

    def set_image_flag(self):
        self.save_image_flag = self.recording

    @property
    def move_dist(self):
        return 60
    
    @property
    def rot_dist(self):
        return 30
    
    def em_time(self, *_):
        self.eb_down = True
        self.em_schedule = self.root.after(EMERGENCY_HOLD_TIME, self.emergency)

    def em_leave(self, *_):
        if self.eb_down:
            self.loggerWin.write_info(f"Emergency must be held for {EMERGENCY_HOLD_TIME / 1000:.1f} seconds")
        self.eb_down = False
        if self.em_schedule:
            self.root.after_cancel(self.em_schedule)

    def load_drone(self):
        self.loggerWin.write_info("Initalizing Drone")

        self.loggerWin.write_info(" - Creating Handle")
        #self.drone = (self.dummyTelloClass(self.loggerWin.write_info, USE_DEBUG_WITH_DUMMY) if USE_DUMMY_TELLO else Tello())
        self.drone=Tello()
        self.loggerWin.write_info(" - Connecting to drone")
        self.drone.connect()
        
        self.loggerWin.write_message("Drone Has Been Connected")
        self.loggerWin.write_info(f"  DRONE_SN  ={self.drone.query_serial_number()}\n  DRONE_ADDR={self.drone.address}")
        if dummy_tello.isdummy(self.drone):
            self.loggerWin.write_warning("Using a Dummy Tello!")

    def take_off(self):
        if not self.drone:
            self.loggerWin.write_error("Drone not connected")
            return
        self.drone.takeoff()
        self.take_off_button.config(state="disabled")
        self.land_button.config(state="normal")
        self.ai_button.config(state="normal")
        self.move_forward_button.config(state="normal")
        self.move_back_button.config(state="normal")
        self.move_left_button.config(state="normal")
        self.move_right_button.config(state="normal")
        self.move_up_button.config(state="normal")
        self.move_down_button.config(state="normal")
        self.start_stream_button.config(state="normal")
        self.emergency_stop_button.config(state="normal")

    def land(self):
        if not self.drone:
            self.loggerWin.write_error("Drone not connected")
            return
        self.drone.land()
        self.land_button.config(state="disabled")
        self.ai_button.config(state="disabled")
        self.take_off_button.config(state="normal")
        self.move_forward_button.config(state="disabled")
        self.move_back_button.config(state="disabled")
        self.move_left_button.config(state="disabled")
        self.move_right_button.config(state="disabled")
        self.move_up_button.config(state="disabled")
        self.move_down_button.config(state="disabled")
        self.stop_stream()
        self.stop_stream_button.config(state="disabled")
        self.save_image_button.config(state="disabled")
        self.emergency_stop_button.config(state="disabled")

    def emergency(self):
        self.loggerWin.write_error("! EMERGENCY !\nShutting off motors...")
        self.drone.emergency()
        self.eb_down = False

    def ai_describe_most_recent_snap(self):
        recent_num = len(os.listdir('SavedImages')) - 1
        if recent_num < 0:
            self.loggerWin.write_error("No screenshots to submit!")
            return
        recent = f"droneSnapshot{recent_num}.jpg"
        base64_image = encode_image("SavedImages/" + recent)
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What’s in this image?"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            } 
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        response_js = response.json()

        json.dump(response_js, open("response.json", "w"), indent=4)

        self.loggerWin.write_message(str(response_js["choices"][0]["message"]["content"]))

    def start_stream(self):
        if not self.drone:
            self.loggerWin.write_error("Drone not connected")
            return
        if dummy_tello.isdummy(self.drone):
            self.loggerWin.write_warning("DumymTello Streaming is experimental")
        
        self.root.after(0, self.__stream)

    def display_update(self, frame_read, vid, loop):
        battery = self.drone.get_battery()
        if battery <= 5:
            self.recording = False
            self.loggerWin.write_warning("Low Battery, Stopping recording...")
        img = frame_read.frame
        vid.write(img)
        self.display.delete("img")
        #image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(img)
        image = image.resize((400, 300))
        if self.save_image_flag:
            self.save_image_flag = False
            img_name = f"droneSnapshot{len(os.listdir('SavedImages'))}.jpg"
            image.save("SavedImages/" + img_name)
            self.loggerWin.write_message(f"Saved image as {img_name}")
        self.display_frame = ImageTk.PhotoImage(image)
        mid = 200, 150
        self.display.create_image(*mid, image=self.display_frame, tags="img")
        if self.recording:
            self.root.after(100, self.display_update, frame_read, vid, loop + 1)
        else:
            self.stop_stream()
            vid.release()
        
    def __stream(self):
        self.stop_stream_button.config(state="normal")
        self.save_image_button.config(state="normal")
        self.start_stream_button.config(state="disabled")

        # ENGAGE TO CAMERA!!!
        self.recording = True
        self.drone.streamon()

        self.loggerWin.write_message("Starting Stream")
        frame_read = self.drone.get_frame_read()
        width, height, _ = frame_read.frame.shape
        vid = cv2.VideoWriter(
            "drone_vid.avi",
            cv2.VideoWriter_fourcc(*"MJPG"),
            30,
            (width, height)
        )

        self.root.after(0, self.display_update, frame_read, vid, 0)

    def stop_stream(self):
        self.stop_stream_button.config(state="disabled")
        self.save_image_button.config(state="disabled")
        self.start_stream_button.config(state="normal")
        self.recording = False
        cv2.destroyAllWindows()

    def move_drone(self, direct, dist):
        move_queue.put_nowait((direct, dist))

    def rotate_left(self):
        self.drone.rotate_counter_clockwise(self.rot_dist)

    def rotate_right(self):
        self.drone.rotate_clockwise(self.rot_dist)

window = win()
mainlo = threading.Thread(None, asyncio.run, args=[main_move(window.drone)])
mainlo.start()
window.root.mainloop()
mainlo.join()
