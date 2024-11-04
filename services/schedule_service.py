import schedule
import time
from services.email_service import send_email
from services.message_service import generate_message
from datetime import datetime, timedelta

def schedule_reminder(interview):
    """
    Agendar os lembretes para um dia antes e uma hora antes da entrevista.
    """
    interview_time_str = interview['interview_time']
    interview_time = datetime.strptime(interview_time_str, "%Y-%m-%d %H:%M")
    email = interview['email']

    # Calcular o horário de um dia antes e uma hora antes
    one_day_before = interview_time - timedelta(days=1)
    one_hour_before = interview_time - timedelta(hours=1)

    now = datetime.now()

    # Agendar o envio de lembretes nesses horários
    if one_day_before > now:
        seconds_until_day_before = (one_day_before - now).total_seconds()
        print(f"Agendando lembrete um dia antes para {interview['name']} em {seconds_until_day_before:.2f} segundos.")
        schedule.every(seconds_until_day_before).seconds.do(
            send_email, email, "Lembrete de Entrevista", generate_message(interview, 'one_day')
        )
    else:
        print(f"Não é possível agendar lembrete de um dia antes para {interview['name']}: o tempo já passou.")


    if one_hour_before > now:
        print(one_day_before)
        print(now)
        seconds_until_hour_before = (one_hour_before - now).total_seconds()
        print(f"Agendando lembrete uma hora antes para {interview['name']} em {seconds_until_hour_before:.2f} segundos.")
        schedule.every(seconds_until_hour_before).seconds.do(
            send_email, email, "Lembrete de Entrevista", generate_message(interview, 'one_hour')
        )
    else:
        print(f"Não é possível agendar lembrete de uma hora antes para {interview['name']}: o tempo já passou.")

def run_scheduled_tasks():
    """
    Roda as tarefas agendadas em um loop infinito.
    """
    while True:
        print(f"[{datetime.now()}] Verificando lembretes agendados...")
        schedule.run_pending()
        time.sleep(10)
