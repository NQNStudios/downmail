from downmail.mailaccount import MailAccount
from dotenv import load_dotenv
from os.path import expanduser

def main():
    env_file = expanduser("~") + '/.downmail.env'
    load_dotenv(env_file)

    # TODO get the user's credentials from CLI if env vars aren't set
    # (for now, assuming Gmail is the host)

    while True:
        try:
            # Connect to the bot mail account
            mail_account = MailAccount.from_environment_vars()
            break
        except:
            print("It seems you haven't configured Downmail with your email accounts yet. The following steps will guide you through generating a .downmail.env file.")

    while True:
        input_line = input('$ ')

        if input_line == "exit":
            print("Quitting Downmail")
            break

        elif input_line == "help":
            print('send/messages/senders/allsenders')

        elif input_line == "send":
            mail_account.compose_message()

        elif input_line == "messages":
            mail_account.check_messages()

        elif input_line == "senders":
            mail_account.audit_senders()
        elif input_line == "allsenders":
            mail_account.audit_senders('All')


if __name__ == "__main__":
    main()
