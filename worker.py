from js import Response, fetch
import asyncio
from petcare import app

async def on_fetch(request, env):
    # Convert Cloudflare request to WSGI environ
    environ = {
        'REQUEST_METHOD': request.method,
        'PATH_INFO': request.url.pathname,
        'QUERY_STRING': request.url.search[1:] if request.url.search else '',
        'CONTENT_TYPE': request.headers.get('content-type', ''),
        'CONTENT_LENGTH': str(len(await request.text()) if request.body else 0),
        'SERVER_NAME': request.url.hostname,
        'SERVER_PORT': '443' if request.url.protocol == 'https:' else '80',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': request.url.protocol[:-1],
        'wsgi.input': await request.text() if request.body else '',
        'wsgi.errors': None,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False
    }
    
    # Add headers to environ
    for key, value in request.headers.items():
        key = 'HTTP_' + key.upper().replace('-', '_')
        environ[key] = value
    
    response_data = []
    status = None
    headers = []
    
    def start_response(status_line, response_headers):
        nonlocal status, headers
        status = int(status_line.split(' ')[0])
        headers = response_headers
    
    result = app(environ, start_response)
    
    for data in result:
        response_data.append(data)
    
    body = b''.join(response_data).decode('utf-8')
    
    return Response.new(body, {
        'status': status,
        'headers': dict(headers)
    })