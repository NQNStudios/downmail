from mailaccount import MailAccount
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()


    # TODO get the user's credentials from CLI if env vars aren't set
    # (for now, assuming Gmail is the host)

    # Connect to the bot mail account
    mail_account = MailAccount.from_environment_vars()


    while True:
        input_line = raw_input('$ ')

        if input_line == "exit":
            print("Quitting Downmail")
            break

        elif input_line == "send":
            mail_account.compose_message()

        elif input_line == "messages":
            mail_account.check_messages()

        elif input_line == "senders":
            mail_account.audit_senders()
        elif input_line == "allsenders":
            mail_account.audit_senders('All')
