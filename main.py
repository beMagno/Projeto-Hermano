from data.mock_data import mock_interviews
from services.schedule_service import check_and_send_reminders, run_reminder_service
from gui import run_gui

def main():

    print("Iniciando agendamento de entrevistas...")

    # Agendar lembretes para todas as entrevistas no mock_data
    for interview in mock_interviews:
        print(f"Agendando lembrete para {interview['name']} - {interview['interview_time']}")
        check_and_send_reminders()

    # Rodar o loop de agendamentos
    run_reminder_service()

    # Iniciar a interface gráfica -> não funciona por conta do loop de verificação
    # run_gui() 

if __name__ == "__main__":
    main()
