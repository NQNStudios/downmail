import os
import imaplib
import smtplib
import markdown
from email.mime.text import MIMEText
from email.header import Header
from email import email


class Message(object):
    def __init__(self, subject, sender, text):
        self.subject = subject
        self.sender = sender
        self.text = text

    def __str__(self):
        return "----------\nFrom: {}\nSubject: {}\n----------\n{}".format(self.sender, self.subject, self.text)


class MailAccount(object):
    """ Connects with SSL to an IMAP and an SMTP email
    server at the given locations.  Sends and receives email from the specified
    address.
    """

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

    def __del__(self):
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
        print(imap_server)
        imap_port = int(os.environ['DM_IMAP_PORT'])
        print(imap_port)
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

    def get_unanswered_messages(self):
        return self.get_messages("(UNANSWERED)")

    def get_messages(self, search_criteria):
        ''' Generator that searches the user's inbox using a set of valid email criteria
        '''
        # TODO link to a resource on what these criteria are, what their syntax
        # is, etc.

        typ, data = self.imap.search(None, search_criteria)
        for num in data[0].split():
            type, data = self.imap.fetch(num, '(BODY.PEEK[])')
            message = email.message_from_string(data[0][1])
            yield Message(
                message['Subject'],
                "todo", # TODO return the sender
                all_payload_text(message),
            )

    def send_message_plain(self, recipients, subject, body_text):
        """ Send a plain utf8 email to the specified list of addresses
        """

        # Construct the message as a MIMEText
        message = MIMEText(body_text.encode('utf-8'), 'plain', 'utf-8')
        message['From'] = self._email_address
        message['To'] = recipients[0]
        message['Subject'] = Header(subject.encode('utf-8'), 'utf-8')

        self._smtp_server.sendmail(self._email_address, recipients,
                                   message.as_string())

    def send_message_markdown(self, recipients, subject, body_markdown):
        """ Send a markdown-formatted email to the specified list of addresses
        """

        # Convert the markdown to HTML
        body_html = markdown.markdown(body_markdown)

        # Construct the message as a MIMEText
        message = MIMEText(body_html.encode('utf-8'), "html", 'utf-8')
        message['From'] = self._email_address
        message['To'] = recipients[0]
        message['Subject'] = Header(subject.encode('utf-8'), 'utf-8')

        self._smtp_server.sendmail(self._email_address, recipients,
                                   message.as_string())


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
