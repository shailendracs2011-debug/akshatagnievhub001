from config.wsgi import application

def handler(request, context):
    return application(request.environ, context.start_response)
