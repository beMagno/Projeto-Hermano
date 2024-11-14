from datetime import datetime, timedelta
from services.email_service import send_email
from services.message_service import generate_message
import time
from data.mock_data import mock_interviews  # Importando dados mocados

def check_and_send_reminders():
    """
    Verifica cada entrevista e envia lembretes quando necessário.
    """
    now = datetime.now()
    
    for interview in mock_interviews:
        interview_time = datetime.strptime(interview['interview_time'], "%Y-%m-%d %H:%M")
        one_day_before = interview_time - timedelta(days=1)
        one_hour_before = interview_time - timedelta(hours=1)
        
        # Envio de lembrete de 1 dia antes, caso ainda não tenha sido enviado
        if now == one_day_before and not interview['one_day_sent']:
            send_email(interview['email'], "Lembrete de Entrevista", generate_message(interview, 'one_day'))
            print(f"Lembrete de 1 dia enviado para {interview['name']} em {now}")
            interview['one_day_sent'] = True  # Marca como enviado
            
        # Envio de lembrete de 1 hora antes, caso ainda não tenha sido enviado
        if now == one_hour_before and not interview['one_hour_sent']:
            send_email(interview['email'], "Lembrete de Entrevista", generate_message(interview, 'one_hour'))
            print(f"Lembrete de 1 hora enviado para {interview['name']} em {now}")
            interview['one_hour_sent'] = True  # Marca como enviado

def run_reminder_service():
    """
    Roda o serviço de lembretes em um loop infinito para verificar e enviar os lembretes no tempo correto.
    """
    while True:
        print("verificando agendamentos...")
        check_and_send_reminders()
        time.sleep(10)  # Verifica a cada 60 segundos
