import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
from modules import database
import threading

class AnalyticsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        self.title_label = ctk.CTkLabel(self, text="Analytics Dashboard", font=("Arial", 20, "bold"))
        self.title_label.pack(pady=10)

        # Scrollable frame for charts
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Task Completion Chart
        self.task_chart_frame = ctk.CTkFrame(self.scrollable_frame)
        self.task_chart_frame.pack(fill="x", pady=10)

        self.task_chart_label = ctk.CTkLabel(self.task_chart_frame, text="Task Completion Over Time", font=("Arial", 16))
        self.task_chart_label.pack(pady=5)

        self.task_canvas = None
        self.load_task_chart()

        # Other charts can be added here, e.g., productivity trends, etc.

    def load_task_chart(self):
        """Load and display task completion chart."""
        def create_chart():
            # Fetch data from database
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT date_completed, COUNT(*) FROM todos WHERE completed = 1 GROUP BY date_completed ORDER BY date_completed")
            data = cursor.fetchall()
            conn.close()

            if not data:
                # No data, show message
                no_data_label = ctk.CTkLabel(self.task_chart_frame, text="No completed tasks to display.")
                no_data_label.pack(pady=20)
                return

            dates = [row[0] for row in data]
            counts = [row[1] for row in data]

            # Convert dates to datetime
            dates = [datetime.datetime.strptime(d, '%Y-%m-%d').date() for d in dates]

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(dates, counts, color='skyblue')
            ax.set_title('Tasks Completed per Day')
            ax.set_xlabel('Date')
            ax.set_ylabel('Number of Tasks')
            plt.xticks(rotation=45)

            # Embed in tkinter
            if self.task_canvas:
                self.task_canvas.get_tk_widget().destroy()
            self.task_canvas = FigureCanvasTkAgg(fig, master=self.task_chart_frame)
            self.task_canvas.get_tk_widget().pack(fill="both", expand=True)
            self.task_canvas.draw()

        threading.Thread(target=create_chart, daemon=True).start()