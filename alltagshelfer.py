import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
import time
import threading
import json
from datetime import datetime, timedelta

class DailyHelperApp:
    """
    Hauptklasse der Anwendung, die die GUI und Funktionalität des Alltagshelfers implementiert.
    """
    
    def __init__(self, root):
        """
        Initialisiert die Anwendung und alle GUI-Komponenten.
        
        Args:
            root (tk.Tk): Das Hauptfenster der Tkinter-Anwendung
        """
        self.root = root
        self.root.title("Alltagshelfer")
        self.root.geometry("600x600")

        # Initialisierung der Datenstrukturen
        self.tasks = {}      # Speichert Aufgaben mit Fälligkeitsdatum und Wiederholung
        self.notes = {}      # Speichert tägliche Notizen
        self.reminders = []  # Speichert aktive Erinnerungen
        self.current_date = datetime.now().strftime("%Y-%m-%d")

        # Kalender-Widget initialisieren
        self.setup_calendar()
        
        # Aufgaben-Widgets initialisieren
        self.setup_tasks()
        
        # Erinnerungs-Widgets initialisieren
        self.setup_reminders()
        
        # Notiz-Widgets initialisieren
        self.setup_notes()
        
        # Hintergrundthreads starten
        self.start_background_threads()
        
        # Vorhandene Daten laden
        self.load_data()

    def setup_calendar(self):
        """Initialisiert die Kalender-Komponenten."""
        self.calendar_label = tk.Label(self.root, text="Kalender")
        self.calendar_label.pack()

        self.calendar = Calendar(self.root, selectmode="day", date_pattern="yyyy-mm-dd")
        self.calendar.pack()
        self.calendar.bind("<<CalendarSelected>>", self.on_date_select)

    def setup_tasks(self):
        """Initialisiert die Aufgaben-bezogenen Widgets."""
        self.task_label = tk.Label(self.root, text="Aufgaben für den Tag")
        self.task_label.pack()

        self.task_entry = tk.Entry(self.root)
        self.task_entry.pack()

        self.due_date_entry = tk.Entry(self.root)
        self.due_date_entry.pack()
        self.due_date_entry.insert(0, "Fälligkeitsdatum (YYYY-MM-DD)")

        self.recurrence_entry = tk.Entry(self.root)
        self.recurrence_entry.pack()
        self.recurrence_entry.insert(0, "Wiederholung (täglich, wöchentlich)")

        self.add_task_button = tk.Button(self.root, text="Aufgabe hinzufügen", command=self.add_task)
        self.add_task_button.pack()

        self.task_listbox = tk.Listbox(self.root)
        self.task_listbox.pack()

        self.remove_task_button = tk.Button(self.root, text="Aufgabe entfernen", command=self.remove_task)
        self.remove_task_button.pack()

    def setup_reminders(self):
        """Initialisiert die Erinnerungs-Widgets."""
        self.reminder_label = tk.Label(self.root, text="Erinnerung setzen")
        self.reminder_label.pack()

        self.reminder_entry = tk.Entry(self.root)
        self.reminder_entry.pack()

        self.reminder_time_entry = tk.Entry(self.root)
        self.reminder_time_entry.pack()
        self.reminder_time_entry.insert(0, "HH:MM")

        self.add_reminder_button = tk.Button(self.root, text="Erinnerung hinzufügen", command=self.add_reminder)
        self.add_reminder_button.pack()

    def setup_notes(self):
        """Initialisiert die Notiz-Widgets."""
        self.note_label = tk.Label(self.root, text="Tägliche Notiz")
        self.note_label.pack()

        self.note_entry = tk.Entry(self.root)
        self.note_entry.pack()

        self.add_note_button = tk.Button(self.root, text="Notiz hinzufügen", command=self.add_note)
        self.add_note_button.pack()

        self.note_display = tk.Label(self.root, text="")
        self.note_display.pack()

    def start_background_threads(self):
        """
        Startet die Hintergrundthreads für:
        - Überprüfung fälliger Aufgaben
        - Überprüfung aktiver Erinnerungen
        """
        self.reminder_thread = threading.Thread(target=self.check_reminders)
        self.reminder_thread.daemon = True
        self.reminder_thread.start()

        self.task_thread = threading.Thread(target=self.check_due_tasks)
        self.task_thread.daemon = True
        self.task_thread.start()

    def on_date_select(self, event):
        """
        Wird aufgerufen, wenn ein neues Datum im Kalender ausgewählt wird.
        
        Args:
            event: Das Kalenderauswahl-Event
        """
        self.current_date = self.calendar.get_date()
        self.update_task_listbox()
        self.display_notes_for_day()

    def add_task(self):
        """Fügt eine neue Aufgabe zur Aufgabenliste hinzu."""
        task = self.task_entry.get()
        due_date = self.due_date_entry.get()
        recurrence = self.recurrence_entry.get().lower()

        if task and due_date:
            if due_date not in self.tasks:
                self.tasks[due_date] = []

            self.tasks[due_date].append({"task": task, "recurrence": recurrence})
            self.update_task_listbox()
            self.clear_task_entries()
            self.save_data()
        else:
            messagebox.showwarning("Eingabefehler", "Bitte Aufgabe und Fälligkeitsdatum eingeben.")

    def clear_task_entries(self):
        """Leert die Eingabefelder für Aufgaben."""
        self.task_entry.delete(0, tk.END)
        self.due_date_entry.delete(0, tk.END)
        self.recurrence_entry.delete(0, tk.END)

    def remove_task(self):
        """Entfernt die ausgewählte Aufgabe aus der Liste."""
        selected_task_index = self.task_listbox.curselection()
        if selected_task_index:
            task_to_remove = self.task_listbox.get(selected_task_index)
            task_date = self.current_date
            for task in self.tasks.get(task_date, []):
                if task_to_remove == task["task"]:
                    self.tasks[task_date].remove(task)
                    break
            self.update_task_listbox()
            self.save_data()
        else:
            messagebox.showwarning("Fehler", "Bitte wählen Sie eine Aufgabe zum Entfernen aus.")

    def update_task_listbox(self):
        """Aktualisiert die Listbox mit den Aufgaben für das ausgewählte Datum."""
        self.task_listbox.delete(0, tk.END)
        if self.current_date in self.tasks:
            for task in self.tasks[self.current_date]:
                self.task_listbox.insert(tk.END, task["task"])

    def check_due_tasks(self):
        """
        Hintergrundthread-Funktion, die regelmäßig auf fällige Aufgaben prüft.
        Zeigt Benachrichtigungen an und verwaltet wiederkehrende Aufgaben.
        """
        while True:
            current_time = datetime.now().strftime("%Y-%m-%d")
            if current_time in self.tasks:
                for task in self.tasks[current_time]:
                    if current_time == task.get("due_date"):
                        messagebox.showinfo("Fällige Aufgabe", f"Aufgabe fällig: {task['task']}")
                        self.handle_recurring_task(task)
            time.sleep(60)

    def handle_recurring_task(self, task):
        """
        Verarbeitet wiederkehrende Aufgaben und erstellt neue Einträge.
        
        Args:
            task (dict): Die wiederkehrende Aufgabe
        """
        if task["recurrence"] == "täglich":
            new_due_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            self.add_task(new_due_date, task["task"])
        elif task["recurrence"] == "wöchentlich":
            new_due_date = (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")
            self.add_task(new_due_date, task["task"])

    def add_reminder(self):
        """Fügt eine neue Erinnerung zur Erinnerungsliste hinzu."""
        reminder_text = self.reminder_entry.get()
        reminder_time = self.reminder_time_entry.get()

        if reminder_text and reminder_time:
            self.reminders.append({"text": reminder_text, "time": reminder_time})
            self.reminder_entry.delete(0, tk.END)
            self.reminder_time_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Eingabefehler", "Bitte Erinnerung und Zeit eingeben.")

    def check_reminders(self):
        """
        Hintergrundthread-Funktion, die regelmäßig auf aktive Erinnerungen prüft
        und Benachrichtigungen anzeigt, wenn die Zeit erreicht ist.
        """
        while True:
            current_time = time.strftime("%H:%M")
            for reminder in self.reminders:
                if reminder["time"] == current_time:
                    messagebox.showinfo("Erinnerung", reminder["text"])
                    self.reminders.remove(reminder)
            time.sleep(60)

    def add_note(self):
        """Fügt eine Notiz für das aktuelle Datum hinzu."""
        note_text = self.note_entry.get()
        if note_text:
            self.notes[self.current_date] = note_text
            self.display_notes_for_day()
            self.note_entry.delete(0, tk.END)
            self.save_data()
        else:
            messagebox.showwarning("Eingabefehler", "Bitte Notiz eingeben.")

    def display_notes_for_day(self):
        """Zeigt die Notiz für das ausgewählte Datum an."""
        if self.current_date in self.notes:
            self.note_display.config(text=f"Notiz für {self.current_date}: {self.notes[self.current_date]}")
        else:
            self.note_display.config(text="Keine Notizen für heute.")

    def load_data(self):
        """Lädt gespeicherte Daten aus der JSON-Datei."""
        try:
            with open("tasks.json", "r") as f:
                data = json.load(f)
                self.tasks = data.get("tasks", {})
                self.notes = data.get("notes", {})
        except FileNotFoundError:
            pass  # Keine Daten vorhanden - wird beim ersten Speichern erstellt

    def save_data(self):
        """Speichert die aktuellen Daten in eine JSON-Datei."""
        data = {
            "tasks": self.tasks,
            "notes": self.notes
        }
        with open("tasks.json", "w") as f:
            json.dump(data, f, indent=4)

if __name__ == "__main__":
    root = tk.Tk()
    app = DailyHelperApp(root)
    root.mainloop()