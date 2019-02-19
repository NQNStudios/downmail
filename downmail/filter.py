import os
import os.path
import json
from mailaccount import MailAccount

class Filter(object):
    def __init__(self, config_json):
        with open(config_json, 'r') as f:
            self._config = json.load(f)

    def run(self):
        for filter_group in self._config:
            for account in filter_group['accounts']:
                dm_account = MailAccount.from_config_file(account)

                for message in dm_account.get_unanswered_messages():
                    # TODO filter out blacklisted emails and bodies
                    for blacklist_rule in filter_group['blacklist']:
                        should_delete = False
                        if 'to' in blacklist_rule:
                            if message.recipient == blacklist_rule['to']:
                                should_delete = True

                        if 'from' in blacklist_rule:
                            if message.recipient == blacklist_rule['from']:
                                should_delete = True

                        if should_delete and 'contains' in blacklist_rule:
                            should_delete = False
                            cant_contain = blacklist_rule['contains']
                            for badphrase in cant_contain:
                                if message.text.lower().contains(badphrase):
                                    should_delete = True

                        if should_delete:
                            print(message)
                            message.delete()


                    # TODO apply replacements by copying the message with all of its payloads, replacing all instances of the problem with {What you want instead}, and sending that to self
                    for replacement_rule in filter_group['replacements']:
                        pass



if __name__ == "__main__":
    filter = Filter(os.path.join(os.path.expanduser('~'), '.config/downmail/filters.json'))
    filter.run()