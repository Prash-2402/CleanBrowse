import threading
import tkinter as tk
from tkinter import messagebox

def _fire_notification(title, message):
    try:
        # Create a hidden master window
        root = tk.Tk()
        root.withdraw()
        # Force the popup window to stay on top
        root.attributes('-topmost', True)
        
        # Show an explicit graphical warning box
        messagebox.showwarning(title=title, message=message, parent=root)
        
        # Clean up the hidden master window after user clicks OK
        root.destroy()
    except Exception as e:
        print(f"[CleanBrowse] Failed to spawn alert: {e}")

def trigger_desktop_alert(title: str, message: str) -> None:
    """
    Fires a raw GUI push notification securely via Tkinter.
    This guarantees visibility, bypassing taskbar mutator software like Windhawk.
    """
    thread = threading.Thread(target=_fire_notification, args=(title, message))
    thread.start()
