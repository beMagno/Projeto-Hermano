import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()  

def send_email(to_email, subject, message_body):
    from_email = os.getenv("EMAIL_USER")
    from_password = os.getenv("EMAIL_PASSWORD")

    print(f"[{datetime.now()}] Preparando para enviar email de {from_email} para {to_email}...")
    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(message_body, 'plain'))
    
    try:
        print(f"[{datetime.now()}] Conectando ao servidor SMTP...")

        # Conectar ao servidor SMTP do Gmail
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Iniciar TLS para criptografar a conexão
            server.login(from_email, from_password)  # Autenticar no servidor SMTP
            
            print(f"[{datetime.now()}] Enviando email...")
            server.sendmail(from_email, to_email, msg.as_string())  # Enviar o email
            
        print(f"[{datetime.now()}] Email enviado para {to_email} com sucesso!")

    # Capturar erros de autenticação
    except smtplib.SMTPAuthenticationError as e:
        print(f"[{datetime.now()}] Erro de autenticação no servidor SMTP: {e}")
    
    # Capturar erros de conexão
    except smtplib.SMTPConnectError as e:
        print(f"[{datetime.now()}] Erro de conexão no servidor SMTP: {e}")
    
    # Capturar outros erros de SMTP
    except smtplib.SMTPException as e:
        print(f"[{datetime.now()}] Erro de SMTP: {e}")
    
    # Capturar qualquer outro erro inesperado
    except Exception as e:
        print(f"[{datetime.now()}] Outro erro ocorreu: {e}")
