import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

msg = MIMEMultipart()

msg['From'] = 'testing.rigaud@gmail.com'
msg['To'] = 'tristan.rigaud@nrmi.fr'
msg['Subject'] = 'Le sujet de mon mail'
message = 'Bonjour !'
msg.attach(MIMEText(message))
mailserver = smtplib.SMTP('smtp.gmail.com', 587)
mailserver.ehlo()
mailserver.starttls()
mailserver.ehlo()
mailserver.login('testing.rigaud@gmail.com', 'zdwl rysn hear awqq')
mailserver.sendmail('testing.rigaud@gmail.com', 'tristan.rigaud@nrmi.fr', msg.as_string())
mailserver.quit()