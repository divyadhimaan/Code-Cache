from lambda_function import app

def handler(event, context):
    return app(event, context)
