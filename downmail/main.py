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

        elif input_line == "messages":

            unanswered = mail_account.get_unanswered_messages()

            while True:
                try:
                    message = unanswered.next()
                    print(message)
                except StopIteration:
                    break

        elif input_line == "senders":
            mail_account.audit_senders()
