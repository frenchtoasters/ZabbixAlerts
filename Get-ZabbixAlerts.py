"""
Name
    Get-ZabbixAlerts

Synopsis
    Gets Zabbix alerts and returns them in aggregated JSON format

Usage
    Get-ZabbixAlerts.py [-h] [--active]

    Optional arguments:
        -h, --help  show this help message and exit
        --active    Query DB for current active alerts

Description
    The Get-ZabbixAlerts class gathers alerts for a given Zabbix environment and packages them up into
    a JSON object, which can then be inserted into an Alerts Database. Using the --active flag will first
    query the specified Alerts Database for alerts that were active after the previous run of Get-ZabbixAlerts.

Author
    Tyler French

Email
    tylerfrench2@gmail.com

Links
    github.com/frenchtoasters
    zabbix.com/documentation/3.4/manual/api

"""
import json
import time

import requests
import argparse
import _mysql


class Alerts(object):
    """
    Class for Zabbix Alerts
    """

    @staticmethod
    def login(url):
        """
        API Login function for zabbix
        :param url: url to your zabbix instance
        :return: api auth token
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": "Admin",
                "password": "zabbix"
            },
            "id": 1,
            "auth": None
        }
        payload = json.dumps(payload)

        headers = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache",
        }

        response = requests.request("POST", url, data=payload, headers=headers)

        auth = response.json()
        return auth['result']

    @staticmethod
    def trigger_get(url, token):
        """
        Query for triggers that are:
         Active
         Average or < severity
         Not in maintenance
         Recently in problem state
        :param url: url to your zabbix instance
        :param token: api auth token for current session
        :return: JSON object of triggers and associated information
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "trigger.get",
            "params": {
                "output": "extend",
                "filter": {
                    "value": 1
                },
                "only_true": 1,
                "min_severity": 3,
                "maintenance": False,
                "active": 1,
                "sortfield": "priority",
                "sortorder": "DESC"
            },
            "id": 1,
            "auth": token
        }
        payload = json.dumps(payload)

        headers = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache",
        }

        response = requests.request("POST", url, data=payload, headers=headers)

        triggers = response.json()
        return triggers['result']

    @staticmethod
    def trigger_getlist(url, token, ids):
        """
        Query for specific triggers passed in ids value
        :param url: url to your zabbix instance
        :param token: api auth token for current session
        :param ids: list of trigger ids to query for
        :return: JSON object of triggers and associated information
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "trigger.get",
            "params": {
                "triggerids": ids,
                "output": "extend",
                "only_true": 1,
                "min_severity": 3,
                "maintenance": False,
                "active": 1,
                "sortfield": "priority",
                "sortorder": "DESC"
            },
            "id": 1,
            "auth": token
        }
        payload = json.dumps(payload)

        headers = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache",
        }

        response = requests.request("POST", url, data=payload, headers=headers)

        triggers = response.json()
        return triggers['result']

    @staticmethod
    def host_get(url, token, triggerid):
        """
        Query for host of given triggerid
        :param url: url to your zabbix instance
        :param token: api auth token for current session
        :param triggerid: id of trigger to query for
        :return: JSON object of host information
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "triggerids": [
                    triggerid
                ],
                "output": [
                    "host"
                ],
                "selectParentTemplates": [
                    "templateid",
                    "name"
                ]
            },
            "id": 1,
            "auth": token
        }
        payload = json.dumps(payload)

        headers = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache",
        }

        response = requests.request("POST", url, data=payload, headers=headers)

        host = response.json()
        return host['result']

    @staticmethod
    def event_get(url, token, triggerid):
        """
        Query for past five minutes of events of a given trigger id
        :param url: url to your zabbix instance
        :param token: api auth token for current session
        :param triggerid: id of trigger to gather events for
        :return: JSON object of events for trigger id
        """
        past = int(time.time()) - 5 * 60 * 1000

        payload = {
            "jsonrpc": "2.0",
            "method": "event.get",
            "params": {
                "output": "extend",
                "objectids": [triggerid],
                "time_from": past,
                "sortfield": ["clock"],
                "sortorder": "DESC"
            },
            "id": 1,
            "auth": token
        }
        payload = json.dumps(payload)

        headers = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache",
        }

        response = requests.request("POST", url, data=payload, headers=headers)

        events = response.json()
        return events['result']

    @staticmethod
    def event_get_limited(url, token, triggerid):
        """
        Query for events of a given trigger id
        :param url: url to your zabbix instance
        :param token: api auth token for current session
        :param triggerid: id of trigger to gather events for
        :return: JSON object of events for trigger id
        """

        payload = {
            "jsonrpc": "2.0",
            "method": "event.get",
            "params": {
                "output": "extend",
                "objectids": [triggerid],
                "sortfield": ["clock"],
                "sortorder": "DESC",
                "limit": 89998
            },
            "id": 1,
            "auth": token
        }
        payload = json.dumps(payload)

        headers = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache",
        }

        response = requests.request("POST", url, data=payload, headers=headers)

        events = response.json()
        return events['result']

    @staticmethod
    def find_status(events):
        """
        Find the alert status of current alert
        :param events: past five minutes of events for alert
        :return: Status of alert
        """
        for event in events:
            if event['value'] == "1" and event['r_eventid'] == "0":
                return "Active"
            else:
                return "Cancelled"

    @staticmethod
    def find_start_time(events):
        """
        Find the clock value of a triggered alert
        :param events: events for an alert
        :return: Start time of alert
        """
        for event in events:
            if event['value'] == "1":
                return event['clock']
        return False

    @staticmethod
    def find_cancel_time(events):
        """
        Find the clock value of a resolved alert
        :param events: past five minutes of events for alert
        :return: Cancel time of alert
        """
        for event in events:
            if event['value'] == "0" and event['r_eventid'] != "0":
                return event['clock']
        return "0"

    @staticmethod
    def find_last_event(events):
        """
        Find the id of the last event for an alert
        :param events:
        :return:
        """
        for event in events:
            if event['r_eventid'] == "0":
                return event['eventid']
        return "0"

    def gather_alerts(self):
        """
        Gather either all alerts or information about specific alerts
        :return: JSON object of alert information
        """
        if self.args.active:
            self.db.query("""
                Select alertId from alerts where monitoringSystem="Zabbix" and alertStatus="Active";
            """)
            triggerids = self.db.store_result()

            triggers = self.trigger_getlist(self.url, self.token, triggerids)

            for trigger in triggers:
                row = {}

                host = self.host_get(self.url, self.token, trigger['triggerid'])
                events = self.event_get(self.url, self.token, trigger['triggerid'])

                row['monitoringSystem'] = "ZABBIX"
                row['entityName'] = host[0]['host']
                row['alertSubject'] = trigger['description']
                row['entityType'] = trigger['description']
                row['triggerid'] = trigger['triggerid']
                row['alertCriticality'] = trigger['priority']
                row['alertStartTime'] = self.find_start_time(events)
                row['alertId'] = trigger['triggerid']
                row['alertUpdateTime'] = int(time.time())
                row['alertStatus'] = self.find_status(events)
                row['alertCancelTime'] = self.find_cancel_time(events)
                row['alertType'] = 0
                row['entityId'] = host[0]['parentTemplates'][0]['templateid']
                row['hostId'] = host[0]['hostid']
                row['alertUrl'] = "http://msc-lex-zabbix.thinkmsc.net/zabbix/tr_events.php?" + \
                                  "triggerid=" + trigger['triggerid'] + \
                                  "&eventid=" + self.find_last_event(events)
                row['alertMessage'] = host[0]['host'] + " " + \
                                      trigger['description'] + " " + \
                                      trigger['comments']

                self.data[trigger['triggerid']] = row
        else:
            triggers = self.trigger_get(self.url, self.token)

            for trigger in triggers:
                row = {}

                host = self.host_get(self.url, self.token, trigger['triggerid'])
                events = self.event_get_limited(self.url, self.token, trigger['triggerid'])

                row['monitoringSystem'] = "ZABBIX"
                row['entityName'] = host[0]['host']
                row['alertSubject'] = trigger['description']
                row['entityType'] = trigger['description']
                row['triggerid'] = trigger['triggerid']
                row['alertCriticality'] = trigger['priority']
                row['alertStartTime'] = self.find_start_time(events)
                row['alertId'] = trigger['triggerid']
                row['alertUpdateTime'] = int(time.time())
                row['alertStatus'] = self.find_status(events)
                row['alertCancelTime'] = self.find_cancel_time(events)
                row['alertType'] = 0
                row['entityId'] = host[0]['parentTemplates'][0]['templateid']
                row['hostId'] = host[0]['hostid']
                row['alertUrl'] = "http://msc-lex-zabbix.thinkmsc.net/zabbix/tr_events.php?" + \
                                  "triggerid=" + trigger['triggerid'] + \
                                  "&eventid=" + self.find_last_event(events)
                row['alertMessage'] = host[0]['host'] + " " + \
                                      trigger['description'] + " " + \
                                      trigger['comments']

                self.data[trigger['triggerid']] = row

        return self.data

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--active", help="Query DB for current active alerts", action="store_true")

        self.args = self.parser.parse_args()

        self.url = "http://127.0.0.1/api_jsonrpc.php"

        self.token = self.login(self.url)

        self.db = _mysql.connect(host="localhost", user="root",
                                 passwd="root", db="alerts_db")

        self.data = {}


if __name__ == "__main__":
    gatheredAlerts = Alerts()

    print(gatheredAlerts.gather_alerts())
