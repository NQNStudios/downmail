import os
from email import email
from mailaccount import MailAccount
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()

    # TODO get the user's credentials from CLI if env vars aren't set
    # (for now, assuming Gmail is the host)

    # Connect to the bot mail account
    mail_account = MailAccount.from_environment_vars()

    # Open the inbox
    mail_account.imap.select('Inbox')
    # TODO print out all inboxes to make sure there's not one/several getting
    # missed because of Google Inbox

    # Retrieve every unanswered email whose subject line includes the keyword.
    # These represent reminders that have yet to be sent
    search_criteria = '(UNANSWERED)'
    typ, data = mail_account.imap.search(None, search_criteria)

    # Retrieve the content of every reminder that's waiting to be sent
    messages = {}

    for num in data[0].split():
        typ, data = mail_account.imap.fetch(num, '(BODY.PEEK[])')
        messages[num] = email.message_from_string(data[0][1])

    # Retrieve the desired recipient from environment variable configuration
    recipient = os.environ['LB_REMINDER_RECIPIENT']

    # Process every reminder
    for num, message in messages.iteritems():
        text = ''

        if isinstance(message.get_payload(), basestring):
            text = message.get_payload()
        else:
            for part in message.get_payload():
                if part.get_content_type() == 'text/plain':
                    text = part.get_payload()

        reminder = Reminder.parse(message['Subject'], text, message['Date'])

        if reminder.is_send_time():
            reminder.send(mail_account, recipient)

            # Mark that the reminder has been sent by flagging as ANSWERED
            mail_account.imap.store(num, '+FLAGS', '\\Answered')

    # Close the inbox
    mail_account.imap.close()
