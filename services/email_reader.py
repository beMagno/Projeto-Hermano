import time
import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv
from datetime import datetime
import re
import datefinder
from message_service import generate_message
import openai
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

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

def extract_meeting_info(from_, subject):
    print("Extraindo informações da reunião...")
    enviado_por = from_
    data_horario = None
    data_horario_formatada = "Data e horário não encontrados"
    
    subject = substituir_mes(subject)
    matches = list(datefinder.find_dates(subject, index=True))
    if matches:
        data_horario = matches[0][0]
        data_horario_formatada = data_horario.strftime("%Y-%m-%d %H:%M:%S")
        print("Primeiro horário encontrado:", data_horario_formatada)
        
    if data_horario is None:
        print("Não foi possível encontrar a data e horário no assunto.")
    
    nome_match = re.search(r'Convite: .*? (.+?) \b(?:ter|seg|qua|qui|sex|sáb|dom)\b', subject, re.IGNORECASE)
    nome = nome_match.group(1) if nome_match else "Nome não encontrado"
    email_cliente_match = re.search(r'([\w\.-]+@[\w\.-]+)', subject)
    email_cliente = email_cliente_match.group(1) if email_cliente_match else "Email do cliente não encontrado"

    print(f"Enviado por: {enviado_por}")
    print(f"Data e horário: {data_horario_formatada}")
    print(f"Nome do convidado: {nome}")
    print(f"E-mail do cliente: {email_cliente}")

    return {
        "enviado_por": enviado_por,
        "data_horario": data_horario_formatada,
        "nome": nome,
        "email_cliente": email_cliente
    }

def read_emails(imap_server):
    imap_server.select("inbox")
    subject_pattern = r'Fwd: Convite: (.+?) (.+?) (.+?) (.+?)'
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

                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8')

                from_, encoding = decode_header(msg.get("From"))[0]
                if isinstance(from_, bytes):
                    from_ = from_.decode(encoding if encoding else 'utf-8')

                if re.match(subject_pattern, subject):
                    print(f"Assunto: {subject}")
                    print(f"De: {from_}")

                    meeting_info = extract_meeting_info(from_, subject)
                    if meeting_info:
                        print("Informações extraídas da reunião:", meeting_info)
                        save_meeting_info(meeting_info)
                        enviar_dados_agendamento(meeting_info)
                        
                        # Removido o envio de email para o cliente diretamente
                        # message_body = generate_humanized_message(meeting_info['nome'], meeting_info['data_horario'])
                        # send_email(meeting_info['email_cliente'], "Entrevista Agendada", message_body)

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
