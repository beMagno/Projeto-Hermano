import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv
from datetime import datetime
import re

load_dotenv()

# Lista de abreviações dos meses na ordem
meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

# Função para fazer login no servidor de email via IMAP
def login_to_email(username, password):
    try:
        imap_server = imaplib.IMAP4_SSL("imap.gmail.com")
        imap_server.login(username, password)
        print("Login realizado com sucesso.")
        return imap_server
    except Exception as e:
        print(f"Erro ao fazer login: {e}")
        return None

# Função para salvar as informações em um arquivo de texto
def save_meeting_info(meeting_info):
    with open("reunioes_agendadas.txt", "a") as file:
        file.write(f"Enviado por: {meeting_info['enviado_por']}\n")
        file.write(f"Data e horário: {meeting_info['data_horario']}\n")
        file.write(f"Nome do convidado: {meeting_info['nome']}\n")
        file.write(f"E-mail do cliente: {meeting_info['email_cliente']}\n")
        file.write("\n" + "="*40 + "\n")
    print("Informações da reunião salvas em reunioes_agendadas.txt")

# Função para buscar informações no corpo do email
def extract_meeting_info(from_, subject, body):
    print("Extraindo informações da reunião...")

    data_horario = "Data e horário não encontrados"

    # Extrair o remetente
    enviado_por = from_
    # Extrair data e horário do assunto usando regex
    # Regex para o formato "ter. 29 out. 2024 17:00"
    subject = "Fwd: Convite: Hapvida & Tecla - Mateus - Product Owner - ter. 29 out. 2024 17:00 - 17:45 (BRT) (Hermano Souza)"

    # Ajuste do regex para combinar mais amplamente com a estrutura da data e horário
    data_horario_match = re.search(r'\b\w{3,5}\. \d{1,2} \w{3,5}\.? \d{4} \d{2}:\d{2}\b', subject)

    if data_horario_match:
        data_horario_str = data_horario_match.group(0)
        print("String de data e hora extraída:", data_horario_str)
    
    # Tenta converter para datetime com substituições de abreviações em português
        try:
        # Substituir abreviações para fazer o datetime reconhecer corretamente
            data_horario_str = data_horario_str.replace("ter.", "Tue").replace("out.", "Oct")
        
        # Converte para objeto datetime usando o formato esperado
            data_horario = datetime.strptime(data_horario_str, "%a %d %b %Y %H:%M")
            print("Data e horário convertidos:", data_horario)
        except ValueError as e:
            print("Erro ao converter data e hora:", e)
            data_horario = "Data e horário não encontrados"
    else:
        data_horario = "Data e horário não encontrados"
        print("Não foi possível encontrar a data e horário no assunto.")


    # Extrair o nome do convidado do assunto
    nome_match = re.search(r'Convite: (.*?) -', subject)
    nome = nome_match.group(1) if nome_match else "Nome não encontrado"

    # Extrair apenas o email do cliente (aquele que não contém "@teclat")
    emails_para = re.findall(r'[\w\.-]+@[\w\.-]+', body)
    email_cliente = next((email for email in emails_para if "@teclat" not in email), "Email do cliente não encontrado")

    print(f"Enviado por: {enviado_por}")
    print(f"Data e horário: {data_horario}")
    print(f"Nome do convidado: {nome}")
    print(f"E-mail do cliente: {email_cliente}")

    return {
        "enviado_por": enviado_por,
        "data_horario": data_horario,
        "nome": nome,
        "email_cliente": email_cliente
    }

# Função para ler os emails da caixa de entrada e extrair reuniões agendadas
def read_emails(imap_server):
    imap_server.select("inbox")
    
    # Definindo o padrão regex para o assunto do email
    subject_pattern = (
        r'Fwd: Convite: (.+?) & (.+?) - (.+?) - (.+?) - (.+?)'
    )

    # Buscar emails não lidos
    status, messages = imap_server.search(None, 'UNSEEN', f'SUBJECT "{subject_pattern}"')
    if status != "OK":
        print("Erro ao buscar emails.")
        return
    
    email_ids = messages[0].split()
    print(f"Número de emails encontrados: {len(email_ids)}")

    for email_id in email_ids:
        res, msg = imap_server.fetch(email_id, "(RFC822)")
        
        for response_part in msg:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # Decodificar o assunto e o remetente
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8')

                from_, encoding = decode_header(msg.get("From"))[0]
                if isinstance(from_, bytes):
                    from_ = from_.decode(encoding if encoding else 'utf-8')

                # Verificar se o assunto corresponde ao padrão
                if re.match(subject_pattern, subject):  # <== Aplicação do subject_pattern aqui
                    print(f"Assunto: {subject}")
                    print(f"De: {from_}")

                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                print(f"Corpo do email:\n{body}")
                                
                                meeting_info = extract_meeting_info(from_, subject, body)
                                if meeting_info:
                                    print("Informações extraídas da reunião:", meeting_info)
                                    save_meeting_info(meeting_info)
                    else:
                        body = msg.get_payload(decode=True).decode()
                        print(f"Corpo do email:\n{body}")
                        
                        meeting_info = extract_meeting_info(from_, subject, body)
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
        if imap_server:
            read_emails(imap_server)
