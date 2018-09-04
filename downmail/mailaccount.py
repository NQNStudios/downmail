import os
import os.path
import imaplib
import markdown
from email.header import Header
from email import email
import json

import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

class Message(object):
    def __init__(self, num, subject, sender, date, text):
        self.id = num
        self.subject = subject
        self.sender = sender
        self.sender_address = self.sender

        if self.sender.count('<'):
            self.sender_address = self.sender[self.sender.find('<')+1:self.sender.find('>')]

        self.date = date
        self.text = text

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
Subject: {}
Date: {}
----------
""".format(self.id, self.sender, self.subject, self.date)


class MailAccount(object):
    """ Connects with SSL to an IMAP and an SMTP email
    server at the given locations.  Sends and receives email from the specified
    address.
    """

    config_file = os.path.expanduser("~") + '/.downmail'

    def __init__(self, imap_server, imap_port, smtp_server, smtp_port,
                 address, password):
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

        if os.path.isfile(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'accepted_senders': [],
                'rejected_senders': [],
            }

    def __del__(self):
        # Serialize JSON
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

        # Log out of the email account on the IMAP server
        self._imap_server.close()
        self._imap_server.logout()
        # Disconnect from the SMTP server
        self._smtp_server.close()

    @classmethod
    def from_environment_vars(cls):
        """ Construct an instance of MailAccount using a configuration
        defined in environment variables
        """

        imap_server = os.environ['DM_IMAP_SERVER']
        imap_port = int(os.environ['DM_IMAP_PORT'])
        smtp_server = os.environ['DM_SMTP_SERVER']
        smtp_port = int(os.environ['DM_SMTP_PORT'])
        address = os.environ['DM_ADDRESS']
        password = os.environ['DM_PASSWORD']

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

    def add_flag(self, num, flag):
        self.imap.store(num, '+FLAGS', '\\' + flag)

    def remove_flag(self, num, flag):
        self.imap.store(num, '-FLAGS', '\\' + flag)

    def set_flag(self, num, flag):
        self.imap.store(num, 'FLAGS', '\\' + flag)

    def get_messages(self, search_criteria, filtered=True):
        ''' Generator that searches the user's inbox using a set of valid email criteria
        '''
        # TODO link to a resource on what these criteria are, what their syntax
        # is, etc.

        typ, data = self.imap.search(None, search_criteria)
        for num in reversed(data[0].split()):
            type, data = self.imap.fetch(num, '(BODY.PEEK[])')
            message = email.message_from_string(data[0][1])
            message = Message(
                num,
                message['Subject'],
                message['From'],
                message['Date'],
                all_payload_text(message),
            )
            if (not filtered) or message.sender_address in self.config['accepted_senders']:
                yield message
            else:
                self.flag_message_answered(num)

        raise StopIteration

    def check_messages(self):
        unanswered = self.get_unanswered_messages()

        while True:
            try:
                message = unanswered.next()

                while True:
                    print(message)
                    input_line = raw_input('Open/Reply/Done/Skip? ')
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


    def audit_senders(self, flag='Recent'):
        recent = self.get_messages('(' + flag + ')', False)

        while True:
            try:
                message = recent.next()

                print(message)
                if message.sender_address not in self.config['rejected_senders'] and message.sender_address not in self.config['accepted_senders']:
                    input_line = raw_input('Allow messages from sender {}? (y/n/s to skip) '.format(message.sender))

                    if input_line == "y" or input_line == "Y":
                        self.config['accepted_senders'].append(message.sender_address)
                        # TODO when a new sender is allowed through, we have to search for
                        # Answered messages from that sender, and re-process them.

                    elif input_line == "n" or input_line == "N":
                        self.config['rejected_senders'].append(message.sender_address)
                        self.flag_message_answered(message.id)
                    elif input_line == "s" or True:
                        pass

            except StopIteration:
                break

    def compose_message(self):
        recipients = [addr.strip() for addr in raw_input('recipients? ').split(',')]
        # TODO validate email addresses
        subject = raw_input('subject? ')
        content = raw_input('content? ') # TODO this should open a text editor for a markdown email
        attachments = [os.path.expanduser(path.strip()) for path in raw_input('attachment paths? ').split(',')]
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
                    still_send = raw_input("Send anyway (Y/n)? ")
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

    if isinstance(email.get_payload(), basestring):
        text = email.get_payload()
    else:
        for part in email.get_payload():
            if part.get_content_type() == 'text/plain':
                text += part.get_payload()

    return text

