# credentials.py


from neo_api_client import NeoAPI

def fetch_client () :

    # credentials
    # ------------------------------------------------------------------------------------------------------ 
    consumer_key = ''
    consumer_secret = ''
    mobile = ''
    mpin = ''
    login_password = ''
    # ------------------------------------------------------------------------------------------------------

    client = NeoAPI(consumer_key=consumer_key, consumer_secret=consumer_secret, environment='prod')
    client.login(mobilenumber=mobile, password=login_password)
    client.session_2fa(OTP=mpin)

    return client 
