import sys
from termcolor import colored,cprint
from time import time, sleep
import webbrowser
from boto3.session import Session
import argparse
import openpyxl


def print_event(eventmsg,color,on_color=None):
    if args.verbose:
        if not args.no_color:
            if on_color:
                eventmsg=colored(eventmsg,color,on_color)
            else:
                eventmsg=colored(eventmsg,color)
        print(eventmsg)

def comma_separated_values(values):
    return values.split(',')


#Argument parsing
parser = argparse.ArgumentParser(description='Route53 Record Collector')
parser.add_argument(
    '-a',
    '--accounts',
    metavar='account_id',
    type=comma_separated_values,
    help='multiple account_ids separated with comma. eg. 122389992,31313313,31313133'
)


parser.add_argument(
    '-o',
    '--output',
    metavar='file_name',
    type=str,
    help='File name to save as, file type is recognised from the extension. eg subdomains.xlsx'
)




parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help='Enable verbose to get details.'
)


parser.add_argument(
    '-nc',
    '--no-color',
    action='store_true',
    help='Color less standard output.'
)

parser.add_argument(
    '-l',
    '--list',
    action='store_true',
    help='List all subdomains, without any verbose.'
)

parser.add_argument(
    '-t',
    '--types',
     metavar='record_type',
     type=comma_separated_values,
     help='DNS record types separated with comma. eg. a,cname'
)


parser.add_argument(
    '-e',
    '--exclude',
     metavar='regular_expression',
     type=comma_separated_values,
     help='exclude subdomains which matching this regular expression. eg. ".*_domainkey.*"'
)


parser.add_argument(
    '-r',
    '--region',
     metavar='region_name',
     type=str,
     help='Region name. eg. us-east-1'
)

parser.add_argument(
    '-u',
    '--start-url',
     metavar='Start URL',
     type=str,
     required=True,
     help='aws SSO start URL. eg. https://d-1010ad440.awsapps.com/start'
)



args = parser.parse_args()





if args.list:
    args.verbose=None

session =Session()

###Skeleton Creation###

#Input details
start_url = args.start_url


if args.region:
    region = args.region
else:
    region = 'us-east-1'


#OIDC Connection
sso_oidc = session.client('sso-oidc')
client_creds = sso_oidc.register_client(
    clientName='r53collector',
    clientType='public',
)
if client_creds:
    print_event("[+] Client credentials fetched Succussfully.","yellow")


       

#Device Authorization initiation
device_authorization = sso_oidc.start_device_authorization(
    clientId=client_creds['clientId'],
    clientSecret=client_creds['clientSecret'],
    startUrl=start_url,
)

if device_authorization:
    print_event("[+] Device authorization has been initiated through browser. Waiting for authorization...","yellow")




#Browser Authorization 
url = device_authorization['verificationUriComplete']
device_code = device_authorization['deviceCode']
expires_in = device_authorization['expiresIn']
interval = device_authorization['interval']
webbrowser.open(url, autoraise=True)


def authwait():
    for n in range(1, expires_in // (interval+5) + 1):
        sleep(interval+5)
        try:
            global token
            token = sso_oidc.create_token(
                grantType='urn:ietf:params:oauth:grant-type:device_code',
                deviceCode=device_code,
                clientId=client_creds['clientId'],
                clientSecret=client_creds['clientSecret'],
            )
            if n>1:
                print_event("\r[+] Device yet to be authorized in browser, waiting...","yellow")
                print_event(f"[+] Authorization Successful after {n} attemps.","green")
    
            else:
                print_event(f"[+] Authorization Successful in first attempt.","green")


            break
        except sso_oidc.exceptions.AuthorizationPendingException:
            if args.verbose:
                if n==1:
                    cprint("Device yet to be authorized in browser, waiting...","red",attrs=["blink"],end='', flush=True)
                else:
                    cprint("\rDevice yet to be authorized in browser, waiting...","red",attrs=["blink"],end='', flush=True)

            pass
authwait()


access_token = token['accessToken']


sso = session.client('sso')
account_list_raw = sso.list_accounts(
    accessToken=access_token,
    maxResults=1000  
)
####Skeleton Completed####



access_token = token['accessToken']



account_list_raw = sso.list_accounts(
    accessToken=access_token,
    maxResults=1000  
)


#Fetch all accessible accounts otherwise give list

if args.accounts:
    account_list= args.accounts
else:
    account_list =  [account['accountId'] for account in account_list_raw['accountList']]

print_event(f'[+] Total accounts: {len(account_list)}','yellow')
print_event(f"    {account_list}\n\n","cyan")





combined_subdomains = set()



def get_dns_value():
    if 'ResourceRecords' in record :
        dns_value=[value['Value'] for value in  record['ResourceRecords'] ]
    elif 'AliasTarget' in record:
        if 'DNSName' in record['AliasTarget']:
            dns_value=record['AliasTarget']['DNSName']       
        else:
            dns_value="dnsvalueerror1"
    else:
        dns_value="dnsvalueerror2"
    return dns_value




def get_subdomains(zone_id):
    
    subdomains= []
    try:
        response = route53.list_resource_record_sets(
            HostedZoneId=zone_id,
        )

        for record in response['ResourceRecordSets']:

            def get_dns_value():
                if 'ResourceRecords' in record :
                    dns_value=[value['Value'] for value in  record['ResourceRecords'] ]
                elif 'AliasTarget' in record:
                    if 'DNSName' in record['AliasTarget']:
                        dns_value=record['AliasTarget']['DNSName']       
                    else:
                        dns_value="dnsvalueerror1"
                else:
                    dns_value="dnsvalueerror2"
                return dns_value

            #if record['Type'] not in ['SOA', 'NS', 'MX', 'TXT'] and not record['Name'].startswith('_'):
            if args.types:
                dns_types = list(map(str.upper, args.types))
                if record['Type'] in dns_types:



                    get_dns_value()


                    subdomains.append(record['Name'].rstrip('.'))
                    combined_subdomains.add(record['Name'].rstrip('.'))
                    if args.verbose:
                        print_event(f"    {record['Type']} : {record['Name'].rstrip('.')}","magenta")  
                        print(f"{record['Type']} : {record['Name']} ==> {get_dns_value()}")                
            else:
                get_dns_value()
                subdomains.append(record['Name'].rstrip('.'))
                combined_subdomains.add(record['Name'].rstrip('.'))
                if args.verbose: 
                    print_event(f"    {record['Type']} : {record['Name'].rstrip('.')}","magenta")
                    print(f"{record['Type']} : {record['Name']} ==> {get_dns_value()}")
    except Exception as e:
        print(f"Failed to get subdomains for zone {zone_id}: {e}")

    return subdomains









for account_id in account_list:
    account_roles = sso.list_account_roles(
        accessToken=access_token,
        accountId=account_id
    )
    roleNames = [role['roleName'] for role in account_roles['roleList']]
    
    #print(roleNames)


    try: 
   #Get credentials for each account
        role_creds = sso.get_role_credentials(
            roleName='Security_Audit',
            accountId=account_id,
            accessToken=access_token,
        )

        #Create session with these credentials
        session = Session(
            region_name=region,
            aws_access_key_id=role_creds['roleCredentials']['accessKeyId'],
            aws_secret_access_key=role_creds['roleCredentials']['secretAccessKey'],
            aws_session_token=role_creds['roleCredentials']['sessionToken'],
        )


        #Route53 client
        route53 = session.client('route53')
        response = route53.list_hosted_zones()


        if args.verbose:
            cprint(f"[+] Route53 DNS records in account {account_id}:","yellow","on_blue")
        for zone in response['HostedZones']:
            zone_id = zone['Id']
            subdomains = get_subdomains(zone_id)


        if args.verbose:
            print()
            print()
    except:
        cprint(f"You do not have enough privileges in account {account_id}!", "red", attrs=["bold"], file=sys.stderr)


print_event(f"[+] Unique subdomains across all accounts: {len(combined_subdomains)}","yellow","on_blue")
for subdomain in combined_subdomains:

    print_event(f"    {subdomain}", "light_cyan")
    
if args.output:
    filelocation=args.output
    if filelocation.endswith('txt'):
        with open(filelocation,'w') as textfile:
            for subdomain in combined_subdomains:
                textfile.write(subdomain+'\n')
        print_event(f"\n[+] All subdomains have been saved in text format in {filelocation}","yellow")

    




