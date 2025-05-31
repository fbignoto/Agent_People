from flask import Request

def soma(a, b):
    return a + b

def main(request: Request):
    a = int(request.args.get('a', 0))
    b = int(request.args.get('b', 0))
    
    result = soma(a, b)
    
    return f"O resultado da soma é: {result}"
