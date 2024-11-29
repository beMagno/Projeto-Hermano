import time
import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv
from datetime import datetime
import re
import parsedatetime as pdt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from pytz import timezone
import datefinder

load_dotenv()

# Dicionário para mapear abreviações dos meses para seus números
meses_abreviados = {
    'jan': '01',
    'fev': '02',
    'mar': '03',
    'abr': '04',
    'mai': '05',
    'jun': '06',
    'jul': '07',
    'ago': '08',
    'set': '09',
    'out': '10',
    'nov': '11',
    'dez': '12'
}

def substituir_mes(texto):
    for mes_abrev, mes_num in meses_abreviados.items():
        texto = re.sub(r'\b' + mes_abrev + r'\b', mes_num, texto)
    return texto

def login_to_email(username, password):
    try:
        imap_server = imaplib.IMAP4_SSL("imap.gmail.com")
        imap_server.login(username, password)
        print("Login realizado com sucesso.")
        return imap_server
    except Exception as e:
        print(f"Erro ao fazer login: {e}")
        return None

def enviar_dados_agendamento(meeting_info):
    url = "http://127.0.0.1:5000/api/agendamento"
    payload = {
        "nome_cliente": meeting_info["nome"],
        "email_cliente": meeting_info["email_cliente"],
        "data_horario": meeting_info["data_horario"]
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            print("Dados enviados com sucesso!")
        else:
            print(f"Erro ao enviar dados: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer a requisição: {e}")

def save_meeting_info(meeting_info):
    with open("reunioes_agendadas.txt", "a") as file:
        file.write(f"Enviado por: {meeting_info['enviado_por']}\n")
        file.write(f"Data e horário: {meeting_info['data_horario']}\n")
        file.write(f"Nome do convidado: {meeting_info['nome']}\n")
        file.write(f"E-mail do cliente: {meeting_info['email_cliente']}\n")
        file.write("\n" + "="*40 + "\n")
    print("Informações da reunião salvas em reunioes_agendadas.txt")


def read_emails(imap_server):
    try:
        # Selecionar a caixa de entrada
        imap_server.select("inbox")
        
        # Buscar por todos os e-mails não lidos
        status, messages = imap_server.search(None, 'UNSEEN SUBJECT "Convite: Tecla T"')
        
        # Extrair os números de mensagens encontradas
        email_ids = messages[0].split()
        print(f"Número de emails encontrados: {len(email_ids)}")

        for email_id in email_ids:
            status, msg_data = imap_server.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # Decodificar o e-mail
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_header(msg["Subject"])[0][0].decode("utf-8")
                    from_ = msg.get("From")
                    body = get_email_body(msg)

                    print(f"Assunto: {subject}")
                    print(f"De: {from_}")
                    
                    # Exibir o corpo do e-mail para inspeção
                    print("Corpo do e-mail:")
                    print(body)  # Isso vai imprimir o corpo do e-mail para depuração

                    # Processar o corpo do e-mail
                    meeting_info = extract_meeting_info(body)
                    if meeting_info:
                        print(f"Informações extraídas: {meeting_info}")
                    else:
                        print("Formato do e-mail não corresponde ao esperado. Ignorado.")
    except Exception as e:
        print(f"Erro ao ler e-mails: {e}")

def get_email_body(msg):
    # Aqui estamos assumindo que o corpo do e-mail está em formato de texto simples ou HTML
    if msg.is_multipart():
        for part in msg.walk():
            # Procurar pela parte de texto
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode("utf-8")
    else:
        return msg.get_payload(decode=True).decode("utf-8")
 
emails_adicionados = set()

def extract_meeting_info(body):
    try:
        import re
        
        # Regex para extrair título, data e horário, e e-mails
        title_pattern = r"(Tecla T[\w\s]+(?=\s))"
        date_pattern = r"(\w+-feira \d{1,2} \w+\. \d{4})"  # Exemplo: "sexta-feira 29 nov. 2024"
        time_pattern = r"(\d{1,2}(:\d{2})?(am|pm) – \d{1,2}(:\d{2})?(am|pm))"
        email_pattern = r"Convidados\s*([\s\S]+?)(?=\n{2,}|$)"

        # Procurando correspondências na string
        title_match = re.search(title_pattern, body)
        date_match = re.search(date_pattern, body)
        time_match = re.search(time_pattern, body)
        bloco_convidados = re.search(email_pattern, body)

        # Lista para armazenar e-mails únicos
        emails_unicos = []
        emails_adicionados = set()
        
        if bloco_convidados:
            # Captura o bloco de texto após "Convidados"
            texto_convidados = bloco_convidados.group(1).strip()
            
            # Agora procuramos os e-mails dentro desse bloco
            email_pattern_convidados = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            emails_convidados = re.findall(email_pattern_convidados, texto_convidados)
            
            for email_cliente in emails_convidados:
                if email_cliente not in emails_adicionados:
                    emails_adicionados.add(email_cliente)
                    emails_unicos.append(email_cliente)

        # Caso não haja e-mails únicos, retorne None
        if not emails_unicos:
            return None

        # Processar horário
        meeting_times = []
        if time_match:
            # Extrair os horários da string no formato 'pm' ou 'am'
            time_str = time_match.group(1)
            time_parts = time_str.split(" – ")
            for time in time_parts:
                hour = int(time.split(":")[0]) if ":" in time else int(time[:-2])
                
                # Ajustar o horário sem conversão de fuso horário
                if "pm" in time and hour < 12:
                    hour += 12
                elif "am" in time and hour == 12:
                    hour = 0
                
                # Verifica minutos
                minutes = time.split(":")[1].replace("pm", "").replace("am", "").strip() if ":" in time else "00"
                formatted_time = f"{hour}:{minutes}"
                meeting_times.append(formatted_time)

        # Verificar se as informações foram encontradas
        if title_match and date_match and meeting_times and emails_unicos:
            meeting_info = {
                "titulo": title_match.group(1).strip(),
                "data": date_match.group(1).strip(),
                "horarios": meeting_times,  # Lista de horários
                "email_cliente": emails_unicos,
            }
            return meeting_info
        else:
            return None
    except Exception as e:
        print(f"Erro ao processar o corpo do e-mail: {e}")
        return None


if __name__ == "__main__":
    USERNAME = os.getenv("EMAIL_USER")
    PASSWORD = os.getenv("EMAIL_PASSWORD")
    
    if not USERNAME or not PASSWORD:
        print("Erro: As variáveis de ambiente não foram definidas corretamente.")
    else:
        imap_server = login_to_email(USERNAME, PASSWORD)
        if imap_server:
            while True:
                print("Procurando novos emails...")
                read_emails(imap_server)
                time.sleep(15)  # Pausa de 15 segundos entre cada verificação
