#! /usr/bin/env python3
import os
import os.path
import json
import itertools
from mailaccount import MailAccount


def forward(dm_account, recipients, message, raw_message, replacements=[]):
        raw_string = raw_message.as_string()
        raw_string_lower = raw_string.lower()

        for rule in replacements:
            for target in rule['from']:
                if raw_string_lower.count(target.lower()):
                    raw_string = raw_string_lower.replace(target.lower(), '[{}]'.format(rule['to']))

        # If a replacement needs to be applied, do it and delete the original
        if raw_string != raw_message.as_string():
            print('replacements applied to message')
            print(raw_string)
            message.delete()

        dm_account.send_message_raw_string(recipients, raw_string, message.sender)


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
                for message, raw_message in itertools.islice(zip(dm_account.get_unanswered_messages(),dm_account.get_unanswered_messages_raw()), 10):
                    if 'simple_blacklist' in filter_group and message.sender_address in filter_group['simple_blacklist']:
                        message.delete()
                        continue

                    # Forward whitelisted senders to the forward_to address
                    if 'simple_whitelist' in filter_group and message.sender_address in filter_group['simple_whitelist'] and 'forward_to' in filter_group:
                        if 'replacements' in filter_group:
                            forward(dm_account, filter_group['forward_to'], message, raw_message, filter_group['replacements'])
                        else:
                            forward(dm_account, filter_group['forward_to'], message, raw_message, [])

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
                        forward(dm_account, [dm_account._email_address], message, raw_message, filter_group['replacements'])
                    else:
                        forward(dm_account, [dm_account._email_address], message, raw_message, [])

if __name__ == "__main__":
    filter = Filter(os.path.join(os.path.expanduser('~'), '.config/downmail/filters.json'))
    filter.run()
