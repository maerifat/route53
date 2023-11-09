from time import time, sleep
import webbrowser
from boto3.session import Session

session =Session()

###Skeleton Creation###

#Input details
start_url = 'https://d-9xxxxx.awsapps.com/start#'
region = 'us-east-1' 


#OIDC Connection
sso_oidc = session.client('sso-oidc')
client_creds = sso_oidc.register_client(
    clientName='xxxxxxx',
    clientType='public',
)

#Device Authorization (tool)
device_authorization = sso_oidc.start_device_authorization(
    clientId=client_creds['clientId'],
    clientSecret=client_creds['clientSecret'],
    startUrl=start_url,
)

#Browser Authorization 
url = device_authorization['verificationUriComplete']
device_code = device_authorization['deviceCode']
expires_in = device_authorization['expiresIn']
interval = device_authorization['interval']
webbrowser.open(url, autoraise=True)

answer= input("Please press ENTER after you authorize in browser.")

#Token creation (for access details of a user - main sso page)
token = sso_oidc.create_token(
    grantType='urn:ietf:params:oauth:grant-type:device_code',
    deviceCode=device_code,
    clientId=client_creds['clientId'],
    clientSecret=client_creds['clientSecret'],
)

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


#Fetch all accessible accounts
account_list =  [account['accountId'] for account in account_list_raw['accountList']]
print(f'Total accounts: {len(account_list)}')
print(account_list) 


for account_id in account_list:
    account_roles = sso.list_account_roles(
        accessToken=access_token,
        accountId=account_id
    )
    roleNames = [role['roleName'] for role in account_roles['roleList']]
    
    #print(roleNames)



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

    #Demo with S#
    newclient = session.client('s3')
    response = newclient.list_buckets()

    # Output the bucket names
    print(f'Existing buckets: in account {account_id}')
    for bucket in response['Buckets']:
        print(f'  {bucket["Name"]}')

    print("#"*20)
    print()




