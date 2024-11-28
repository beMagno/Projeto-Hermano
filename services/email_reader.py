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
import pytz

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

    # Inicializando o parsedatetime
    cal = pdt.Calendar()
    datetime_context = datetime.now()
    br_tz = timezone('America/Sao_Paulo')

    # Tentando interpretar a data do assunto do email
    try:
        parsed_date, status = cal.parse(subject, sourceTime=datetime_context)
        if status > 0:  # Se foi possível interpretar uma data
            data_horario = datetime(*parsed_date[:6])  # Converte para objeto datetime

            # Supondo que o horário já esteja no fuso UTC:
            data_horario = pytz.utc.localize(data_horario).astimezone(br_tz)

        
        # Formatar a data e hora para exibição
            data_horario_formatada = data_horario.strftime("%Y-%m-%d %H:%M:%S")
            print("Primeiro horário encontrado:", data_horario_formatada)
    except Exception as e:
        print(f"Erro ao processar a data e horário com parsedatetime: {e}")

    if data_horario is None:
        print("Não foi possível encontrar a data e horário no assunto.")

    # Extração do nome do convidado
    nome_match = re.search(r'Convite: .*? (.+?) \b(?:ter|seg|qua|qui|sex|sáb|dom)\b', subject, re.IGNORECASE)
    nome = nome_match.group(1) if nome_match else "Nome não encontrado"

    # Extração do email do cliente
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

def extract_meeting_info(body):
    try:
        # Regex para extrair título, data/hora e e-mail
        title_pattern = r"(Tecla T[\w\s]+)"
        # Expressão regular ajustada para capturar o horário com pm
        date_time_pattern = r"(\w{3,9} \d{1,2} \w{3,9}\. \d{4} ⋅ \d{1,2}(:\d{2})?pm – \d{1,2}(:\d{2})?pm)"
    
        # Usando re.DOTALL para garantir que o ponto combine com novas linhas
        date_time_match = re.search(date_time_pattern, body, re.DOTALL)

        email_pattern = r"Convidados\s*([\s\S]+?)(?=\n{2,}|$)"

        # Procurando o bloco de texto após "Convidados"
        bloco_convidados = re.search(email_pattern, body)

        if bloco_convidados:
            # Captura o bloco de texto após "Convidados"
            texto_convidados = bloco_convidados.group(1).strip()

            # Agora procuramos os e-mails dentro desse bloco
            email_pattern_convidados = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            # Variável que guarda os emails em lista
            emails_convidados = re.findall(email_pattern_convidados, texto_convidados)

        title_match = re.search(title_pattern, body)
        
        # Processar horário, caso tenha sido encontrado
        meeting_times = []
        if date_time_match:
            # Extrair os horários da string no formato 'pm' ou 'am'
            time_str = date_time_match.group(1)
            time_pattern = r"(\d{1,2}(:\d{2})?pm|\d{1,2}(:\d{2})?am)"
            times = re.findall(time_pattern, time_str)
            
            for time in times:
                time_str = time[0]
                
                # Ajustar o horário sem conversão de fuso horário
                if "pm" in time_str:
                    hour = int(time_str.split(":")[0].replace("pm", "").strip())
                    # Ajuste para garantir que 12pm seja 12 e horários PM sejam somados corretamente
                    if hour < 12:  # Para 1pm até 11pm, adicionar 12 horas
                        hour += 12
                elif "am" in time_str:
                    hour = int(time_str.split(":")[0].replace("am", "").strip())
                    # Ajustar para garantir que 12am seja 0
                    if hour == 12:  # 12am se torna 0 (meia-noite)
                        hour = 0
                else:
                    continue
                
                # Verifica se há minutos e os mantém no formato correto
                if ":" in time_str:
                    minutes = time_str.split(":")[1].replace("pm", "").replace("am", "").strip()
                    formatted_time = f"{hour}:{minutes}"
                else:
                    formatted_time = f"{hour}:00"
                
                # Adicionar o horário formatado na lista
                meeting_times.append(formatted_time)

        # Verificar se as informações foram encontradas
        if title_match and meeting_times and emails_convidados:
            meeting_info = {
                "nome": title_match.group(1).strip(),
                "data_horario": " – ".join(meeting_times),  # Assumindo que você quer juntar os horários
                "email_cliente": emails_convidados,
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
