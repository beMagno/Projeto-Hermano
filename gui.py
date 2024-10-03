import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import schedule
import time
import threading

# Lista global para armazenar lembretes agendados
scheduled_reminders = []
entry_nome = None  # Variável global para o campo de entrada do nome
entry_data = None  # Variável global para o campo de entrada da data
listbox_reminders = None  # Variável global para a listbox

def schedule_reminder(meeting_name, meeting_date):
    try:
        meeting_time = datetime.strptime(meeting_date, "%Y-%m-%d %H:%M")
        now = datetime.now()
        
        # Verifica se a reunião é no futuro
        if meeting_time <= now:
            print(f"[WARNING] Tentativa de agendar reunião no passado: {meeting_date}")
            raise ValueError("A data/hora da reunião deve ser no futuro.")

        print(f"[INFO] Agendando lembrete para {meeting_name} em {meeting_date}.")
        schedule.every().day.at(meeting_time.strftime("%H:%M")).do(send_reminder, meeting_name)
        scheduled_reminders.append((meeting_name, meeting_date))
        return True
    except Exception as e:
        print(f"[ERROR] Erro ao agendar lembrete: {e}")
        return False

def send_reminder(meeting_name):
    print(f"[INFO] Lembrete: Você tem uma reunião agendada: {meeting_name}")

def agendar_reuniao():
    # Obter dados do usuário
    meeting_name = entry_nome.get()
    meeting_date = entry_data.get()
    print(f"[DEBUG] Recebendo dados do usuário: {meeting_name}, {meeting_date}")

    # Agendar lembrete
    if schedule_reminder(meeting_name, meeting_date):
        messagebox.showinfo("Sucesso", f"Lembrete agendado para {meeting_name} em {meeting_date}.")
        update_reminder_list()
    else:
        messagebox.showerror("Erro", "Falha ao agendar lembrete.")

def update_reminder_list():
    # Limpar a lista atual
    listbox_reminders.delete(0, tk.END)
    for name, date in scheduled_reminders:
        listbox_reminders.insert(tk.END, f"{name} - {date}")

def run_scheduled_tasks():
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_gui():
    global entry_nome, entry_data, listbox_reminders  # Tornar as variáveis globais
    # Criar a janela principal
    root = tk.Tk()
    root.title("Agendador de Reuniões")

    # Campo de nome da reunião
    tk.Label(root, text="Nome da Reunião:").grid(row=0)
    entry_nome = tk.Entry(root)
    entry_nome.grid(row=0, column=1)

    # Campo de data e hora
    tk.Label(root, text="Data e Hora (YYYY-MM-DD HH:MM):").grid(row=1)
    entry_data = tk.Entry(root)
    entry_data.grid(row=1, column=1)

    # Botão de agendar
    botao_agendar = tk.Button(root, text="Agendar Lembrete", command=agendar_reuniao)
    botao_agendar.grid(row=2, columnspan=2)

    # Listbox para exibir lembretes agendados
    listbox_reminders = tk.Listbox(root, width=50)
    listbox_reminders.grid(row=3, columnspan=2)

    # Iniciar thread para tarefas agendadas
    threading.Thread(target=run_scheduled_tasks, daemon=True).start()

    print("[INFO] Iniciando a GUI")
    # Iniciar a GUI
    root.mainloop()

if __name__ == "__main__":
    run_gui()
