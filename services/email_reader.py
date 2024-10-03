import imaplib
import email
from email.header import decode_header
import webbrowser
import os
import re 
from dotenv import load_dotenv

load_dotenv() 

# Função para fazer login no servidor de email via IMAP
def login_to_email(username, password):
    imap_server = imaplib.IMAP4_SSL("imap.gmail.com")
    imap_server.login(username, password)
    
    return imap_server

# Função para salvar as informações em um arquivo de texto
def save_meeting_info(meeting_info):
    with open("reunioes_agendadas.txt", "a") as file:
        file.write(f"Gestor: {meeting_info['gestor']}\n")
        file.write(f"Data: {meeting_info['data']}\n")
        file.write(f"Horário: {meeting_info['horario']}\n")
        file.write("\n" + "="*40 + "\n")

# Função para buscar informações no corpo do email
def extract_meeting_info(body):
    gestor = re.search(r"Gestor:\s*(.*)", body)
    data = re.search(r"Data:\s*(.*)", body)
    horario = re.search(r"Horário:\s*(.*)", body)
    
    if gestor and data and horario:
        return {
            "gestor": gestor.group(1),
            "data": data.group(1),
            "horario": horario.group(1)
        }
    return None

# Função para ler os emails da caixa de entrada e extrair reuniões agendadas
def read_emails(imap_server):
    imap_server.select("inbox")
    
    # Buscar emails não lidos com o assunto "Agendamento de Reuniao - Dev" -> trocar filtro depois
    status, messages = imap_server.search(None, '(UNSEEN SUBJECT "Agendamento de Reuniao - Dev")')
    
    email_ids = messages[0].split()

    for email_id in email_ids:
        res, msg = imap_server.fetch(email_id, "(RFC822)")
        
        for response_part in msg:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8')

                from_, encoding = decode_header(msg.get("From"))[0]
                if isinstance(from_, bytes):
                    from_ = from_.decode(encoding if encoding else 'utf-8')

                print(f"Assunto: {subject}")
                print(f"De: {from_}")

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            print(f"Corpo do email:\n{body}")
                            
                            meeting_info = extract_meeting_info(body)
                            if meeting_info:
                                print("Informações extraídas da reunião:", meeting_info)
                                save_meeting_info(meeting_info)
                else:
                    body = msg.get_payload(decode=True).decode()
                    print(f"Corpo do email:\n{body}")
                    
                    meeting_info = extract_meeting_info(body)
                    if meeting_info:
                        print("Informações extraídas da reunião:", meeting_info)
                        save_meeting_info(meeting_info)

    imap_server.close()
    imap_server.logout()

# Executar o script
if __name__ == "__main__":
    USERNAME = os.getenv("EMAIL_USER")
    PASSWORD = os.getenv("EMAIL_PASSWORD")
    
    if not USERNAME or not PASSWORD:
        print("Erro: As variáveis de ambiente não foram definidas corretamente.")
    else:
        # Fazer login e ler emails
        imap_server = login_to_email(USERNAME, PASSWORD)
        read_emails(imap_server)
