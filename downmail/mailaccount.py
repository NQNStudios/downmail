import os
import os.path
import imaplib
import markdown
from email.header import Header
import email
import json

import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

class Message(object):
    def __init__(self, account, num, subject, sender, recipient, date, text):
        self.account = account
        self.id = num
        self.subject = subject
        self.sender = sender
        self.recipient = recipient
        self.sender_address = self.sender

        if self.sender and self.sender.count('<'):
            self.sender_address = self.sender[self.sender.find('<')+1:self.sender.find('>')]

        self.date = date
        self.text = text

    def delete(self):
        print('deleting {}'.format(self.subject))
        self.account.delete_message(self.id)

    def print_header(self):
        print(self)

    def print_full(self):
        print(self)
        print(self.text)

    def __str__(self):
        return """
----------
#{}
From: {}
To: {}
Subject: {}
Date: {}
----------
""".format(self.id, self.sender, self.recipient, self.subject, self.date)


class MailAccount(object):
    """ Connects with SSL to an IMAP and an SMTP email
    server at the given locations.  Sends and receives email from the specified
    address.
    """

    def __init__(self, imap_server, imap_port, smtp_server, smtp_port, address, password):
        # Connect to the IMAP server
        self._imap_server = imaplib.IMAP4_SSL(imap_server, imap_port)

        # Connect to the SMTP server
        self._smtp_server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        # Log in to the email account
        self._imap_server.login(address, password)
        self._smtp_server.login(address, password)

        # TODO print out all inboxes to make sure there's not one/several getting
        # missed because of Google Inbox
        self._imap_server.select('Inbox')
        # Save the email address we're logged into
        self._email_address = address

    def __del__(self):
        # Log out of the email account on the IMAP server
        self._imap_server.close()
        self._imap_server.logout()
        # Disconnect from the SMTP server
        self._smtp_server.close()

    @classmethod
    def from_config_file(cls, address, filename=''):
        """ Construct an instance of MailAccount using a configuration
        defined in environment variables
        """
        if len(filename) == 0:
            filename = os.path.join(os.path.expanduser('~'), '.config/downmail/accounts.json')

        with open(filename, 'r') as f:
            config_json = json.load(f)
            for account in config_json['accounts']:
                if account['address'] == address:
                    address = account['address']
                    password = account['pw']
                    imap_server = 'imap.gmail.com'
                    imap_port = 993
                    smtp_server = 'smtp.gmail.com'
                    smtp_port = 465
                    try:
                        imap_server = account['imap_server']
                        imap_port = account['imap_port']
                        smtp_server = account['smtp_server']
                        smtp_port = account['smtp_port']
                    except KeyError:
                        pass


                    return cls(imap_server, imap_port, smtp_server, smtp_port,
                            address, password)

    @property
    def imap(self):
        """ The bot's connected IMAP server """
        return self._imap_server

    def get_unanswered_messages(self, filtered=True):
        return self.get_messages("(UNANSWERED)",filtered)

    def flag_message_answered(self, num):
        print("flagging {} answered".format(num))
        self.add_flag(num, 'Answered')

    def delete_message(self, num):
        print("flagging {} deleted".format(num))
        self.add_flag(num, 'Deleted')

    def add_flag(self, num, flag):
        self.imap.store(num, '+FLAGS', '\\' + flag)

    def remove_flag(self, num, flag):
        self.imap.store(num, '-FLAGS', '\\' + flag)

    def set_flag(self, num, flag):
        self.imap.store(num, 'FLAGS', '\\' + flag)

    def get_messages(self, search_criteria, filtered=True):
        ''' Generator that searches the user's inbox using a set of valid email criteria
        '''
        # TODO link to a resource on what these criteria are, what their syntax is, etc.

        _, data = self.imap.search(None, search_criteria)
        for num in reversed(data[0].split()):
            _, data = self.imap.fetch(num, '(BODY.PEEK[])')
            message = email.message_from_bytes(data[0][1])
            message = Message(
                self,
                num,
                message['Subject'],
                message['From'],
                message['To'],
                message['Date'],
                all_payload_text(message),
            )
            yield message

        raise StopIteration

    def check_messages(self):
        unanswered = self.get_unanswered_messages()

        for message in unanswered:
            try:
                while True:
                    print(message)
                    input_line = input('Open/Reply/Done/Skip? ')
                    if input_line == "O" or input_line == "o":
                        message.print_full()
                    elif input_line == "R" or input_line == "r":
                        # TODO open Vim or default editor to compose a reply in
                        # markdown
                        break
                    elif input_line == "D" or input_line == "d":
                        self.flag_message_answered(message.id)
                        break
                    else:
                        break



            except StopIteration:
                break


    def compose_message(self):
        recipients = [addr.strip() for addr in input('recipients? ').split(',')]
        # TODO validate email addresses
        subject = input('subject? ')
        content = input('content? ') # TODO this should open a text editor for a markdown email
        attachments = [os.path.expanduser(path.strip()) for path in input('attachment paths? ').split(',')]
        self.send_message_plain(recipients, subject, content, attachments)

    def _send_message(self, recipients, subject, content, encoding, files=[]):
        # Construct the message as a MIMEMultipart with MIMEText

        # source of attachment code: https://stackoverflow.com/a/3363254
        message = MIMEMultipart()
        message['From'] = self._email_address
        message['To'] = COMMASPACE.join(recipients)
        message['Date'] = formatdate(localtime=True)
        message['Subject'] = Header(subject.encode('utf-8'), 'utf-8')

        message.attach(MIMEText(content.encode('utf-8'), encoding, 'utf-8'))

        for f in files:
            if f != "":
                try:
                    with open(f, 'rb') as ff:
                        part = MIMEApplication(
                            ff.read(),
                            Name=basename(f),
                        )
                    # After the file is closed
                    part['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(f))
                    message.attach(part)
                except:
                    print("Couldn't attach {}.".format(f))
                    still_send = input("Send anyway (Y/n)? ")
                    # TODO should be an option to correct the path and try again
                    if still_send.lower() == "y":
                        continue
                    else:
                        return



        self._smtp_server.sendmail(self._email_address, recipients,
                                   message.as_string())

    def send_message_plain(self, recipients, subject, body_text, files=[]):
        """ Send a plain utf8 email to the specified list of addresses
        """
        self._send_message(recipients, subject, body_text, 'plain', files)

    def send_message_markdown(self, recipients, subject, body_markdown, files=[]):
        """ Send a markdown-formatted email to the specified list of addresses
        """
        # Convert the markdown to HTML
        body_html = markdown.markdown(body_markdown)
        self._send_message(recipients, subject, body_html, 'html', files)


# TODO eventually we'll want to handle other types of payloads
def all_payload_text(email):
    text = ''

    if isinstance(email.get_payload(), str):
        text = email.get_payload()
    else:
        for part in email.get_payload():
            if part.get_content_type() == 'text/plain':
                text += part.get_payload()
            #else:
            #    print(part.get_content_type())

    return text

