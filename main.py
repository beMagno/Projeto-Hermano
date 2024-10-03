from data.mock_data import mock_interviews
from services.schedule_service import schedule_reminder, run_scheduled_tasks
from gui import run_gui

def main():

    print("Iniciando agendamento de entrevistas...")

    # Agendar lembretes para todas as entrevistas no mock_data
    for interview in mock_interviews:
        print(f"Agendando lembrete para {interview['name']} - {interview['interview_time']}")
        schedule_reminder(interview)

    # Rodar o loop de agendamentos
    run_scheduled_tasks()

    # Iniciar a interface gráfica -> não funciona por conta do loop de verificação
    # run_gui() 

if __name__ == "__main__":
    main()
