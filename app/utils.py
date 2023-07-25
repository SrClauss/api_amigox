import datetime
from os import getenv
from typing import List, Tuple
import random
from dotenv import load_dotenv


load_dotenv()
def generate_pairs(num) -> List[Tuple[int, int]]:
    """
    Generate pairs of integers from 0 to `num`.

    Args:
        num (int): The upper limit for generating the integers.

    Returns:
        List[Tuple[int, int]]: A list of tuples, each containing a pair
            of integers.

    Raises:
        None.
    """
    lista = [x for x in range(num)]
    listb = [x for x in range(num)]
    result = []

    for x in range(len(lista) - 1):
        random_index = random.randrange(len(listb))
        while lista[x] == listb[random_index]:
            random_index = random.randrange(len(listb))
        result.append((lista[x], listb[random_index]))
        listb.pop(random_index)


    if lista[-1] == listb[0]:
        return generate_pairs(num)
    else:
        result.append((lista[-1], listb[0]))
        return result


def send_confirmation_email(email, token):
    """
    A function that sends an email using the provided email address and token, do not implemented yet.
    
    Parameters:
        email (str): The recipient's email address.
        token (str): The token required to authenticate the email sending process.
        
    Returns:
        A string containing the message sent to the email address.
    """
    return {"email": email, "token": token, "exp": datetime.datetime.now() + datetime.timedelta(days=1)}
    #TODO Implement a email sending function

def send_recovery_email(email, token):
    """
    A function that sends an email using the provided email address and token, do not implemented yet.
    
    Parameters:
        email (str): The recipient's email address.
        token (str): The token required to authenticate the email sending process.
        
    Returns:
        A string containing the message sent to the email address.
    """
    return {"email": email, "token": token, "exp": datetime.datetime.now() + datetime.timedelta(days=1)}
    #TODO Implement a recoveryh email sending function

def test_headers(payload: dict[str, str]|None= None, authorization: str|None=None)->dict[str, str]:
    """
    Given a payload and an authorization token, this function generates and returns a dictionary of headers for an HTTP request.

    :param payload: The payload data to be sent in the request body (default is None).
    :param authorization: The authorization token to be included in the headers (default is None).
    :return: A dictionary of headers for the HTTP request.
    """

    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['API-Key'] = getenv('API_KEY')
    if payload:
        headers['Content-Length'] = str(len(payload))
    if authorization:
        headers['Authorization'] = 'Bearer ' + authorization
    return headers

 
    
    
