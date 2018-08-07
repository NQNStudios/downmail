from mailaccount import MailAccount
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()

    # TODO get the user's credentials from CLI if env vars aren't set
    # (for now, assuming Gmail is the host)

    # Connect to the bot mail account
    mail_account = MailAccount.from_environment_vars()


    unanswered = mail_account.get_unanswered_messages()
    for i in range(50):
        message = unanswered.next()
        print(message)

    # mail_account.flag_message_answered(message.id)
