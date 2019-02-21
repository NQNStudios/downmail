import os
import os.path
import json
import itertools
from mailaccount import MailAccount

class Filter(object):
    def __init__(self, config_json):
        with open(config_json, 'r') as f:
            self._config = json.load(f)

    def run(self):
        for filter_group in self._config:
            for account in filter_group['accounts']:
                print(account)
                dm_account = MailAccount.from_config_file(account)

                # Filter out blacklisted senders and phrases
                for message in itertools.islice(dm_account.get_unanswered_messages(), 100):
                    if 'simple_blacklist' in filter_group and message.sender_address in filter_group['simple_blacklist']:
                        message.delete()
                        continue

                    if 'blacklist' in filter_group:
                        for blacklist_rule in filter_group['blacklist']:
                            should_delete = False
                            if 'to' in blacklist_rule:
                                if message.recipient == blacklist_rule['to']:
                                    should_delete = True

                            if 'from' in blacklist_rule:
                                if message.sender_address == blacklist_rule['from']:
                                    should_delete = True

                            if should_delete and 'contains' in blacklist_rule:
                                should_delete = False
                                cant_contain = blacklist_rule['contains']
                                for badphrase in cant_contain:
                                    if (message.subject + message.text).lower().count(badphrase):
                                        should_delete = True

                            if should_delete:
                                print(message)
                                message.delete()

                    # apply replacements by copying the message  replacing all instances of the problem with {What you want instead}, and sending that to self
                    if 'replacements' in filter_group:
                        # TODO this method discards all the other payloads. Whoops!
                        new_subject = message.subject.lower()
                        new_text = message.text.lower()
                        for rule in filter_group['replacements']:
                            for target in rule['from']:
                                if new_subject.count(target.lower()) or new_text.count(target.lower()):
                                    new_subject = new_subject.replace(target.lower(), '[{}]'.format(rule['to']))
                                    new_text = new_text.replace(target.lower(), '[{}]'.format(rule['to']))

                        # If a replacement needs to be applied, do it and delete the original
                        if new_subject != message.subject.lower() or new_text != message.text.lower():
                            print('replacements applied to message')
                            print(message)
                            message.delete()
                            dm_account.send_message_html([dm_account._email_address], new_subject, new_text)




if __name__ == "__main__":
    filter = Filter(os.path.join(os.path.expanduser('~'), '.config/downmail/filters.json'))
    filter.run()