FROM python:3.5

COPY Get-ZabbixAlerts.py /

RUN pip install requests argparse mysqlclient

CMD python Get-ZabbixAlerts.py
