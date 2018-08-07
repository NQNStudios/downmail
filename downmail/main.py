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

    print(mail_account.get_unanswered_messages().next())
