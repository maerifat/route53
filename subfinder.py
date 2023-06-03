import boto3
import requests
import socket
from datetime import datetime
import ssl
from cryptography import x509
from cryptography.hazmat.backends import default_backend


# Get current date and time
#now = datetime.now()

# Format date and time as string
#dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
session = boto3.Session(profile_name='dns')
route53 = session.client('route53')


def get_subdomains(zone_id):
    subdomains = []
    try:
        response = route53.list_resource_record_sets(
            HostedZoneId=zone_id,
        )
        for record in response['ResourceRecordSets']:
            if record['Type'] not in ['SOA', 'NS', 'MX', 'TXT'] and not record['Name'].startswith('_') and '_domainkey' not in record['Name']:
                subdomains.append(record['Name'].rstrip('.'))
    except Exception as e:
        print(f"Failed to get subdomains for zone {zone_id}: {e}")
    with open("subs.txt","a") as file:
        for subdomain in subdomains:
            file.write(subdomain + '\n')


    print(subdomains)




try:
    response = route53.list_hosted_zones()
    for zone in response['HostedZones']:
        zone_id = zone['Id']
        subdomains = get_subdomains(zone_id)

except Exception as e:
    print(f"Failed to get hosted zones: {e}")
