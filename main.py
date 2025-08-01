#teste para acionar o cloud build#
import base64
import requests
import smtplib
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.cloud import secretmanager

def acessar_segredo(id_projeto, id_segredo):
    """Acessa um segredo armazenado no Google Secret Manager"""
    client = secretmanager.SecretManagerServiceCliente()
    nome_do_recurso = f"projects/{id_projeto}/secrets/{id_segredo}/versions/latest"
    response = client.access_secret_version(request={"name": nome_do_recurso})
    return response.payload.data.decode("UTF-8")

def enviar_email(corpo_html, destinatario):
    """Envia o e-mail com as noticias"""
    # Estes dados serão configurados no ambiente da Cloud Function ou buscados do Secret Manager
    ID_PROJETO_GCP = 'triple-name-466219-v5'
    SEU_EMAIL = "lucas.b.pj@gmail.com"

    #busca a senha de forma segura
    try:
        senha_de_app = acessar_segredo(ID_PROJETO_GCP, 'SENHA_DE_APP_GMAIL')
    except Exception as e:
        print(f"Erro ao acessar o segredo: {e}")
        return
    
    # Configuração de E-mail
    msg = MIMEMultipart()
    msg['From'] = SEU_EMAIL
    msg['To'] = destinatario
    msg['Subject'] = "Notícias de Tecnologia do Dia"
    msg.attach(MIMEText(corpo_html, 'html'))

    # Envio
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SEU_EMAIL, senha_de_app)
        server.sendmail(SEU_EMAIL, destinatario, msg.as_string())
        server.quit()
        print(f"E-mail enviado com sucesso para {destinatario}!")
    except Exception as e:
        print("Erro ao enviar o e-mail: {e}")

# Função Principal (Ponto de Entrada)

def executar_robo(event, context):
    """Função principal acionada pelo Cloud Scheduler via Pub/Sub.
    """
    print("Iniciando o robô de web scraping...")
    URL = "https://news.mit.edu/topic/artificial-intelligence2"
    EMAIL_DESTINO = "lucas.b.pj@gmail.com"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(URL, headers=headers)

    if response.status_code != 200:
        print (f'Falha ao acessar o site. Status: {response.status_code}')
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    noticias_encontradas = soup.find_all('a', class_='feed-post-link', limit=10) # limita a 10 notícias

    if not noticias_encontradas:
        print("Nenhuma notícia encontrada com os seletores definidos.")
        return
    
    # Monta o corpo do e-mail
    corpo_html = "<html><body><h1>Principais Notícias de Hoje</h1><ul>"
    for noticia in noticias_encontradas:
        titulo = noticia.get_text()
        link = noticia['href']
        corpo_html += '</ul></body></html>'

    # Envia o e-mail
    enviar_email(corpo_html, EMAIL_DESTINO)

    print("Robô finalizado.")
    return 'ok'

