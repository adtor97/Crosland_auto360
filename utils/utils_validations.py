import pandas as pd

def validate_Q(Q):

    if Q in ["Q1", "Q2", "Q3", "Q4"]:
        return True
    else:
        return False

def validate_admin(user, password):
    if user == "crosland" and password == "360report":
        return True
    else: return False
