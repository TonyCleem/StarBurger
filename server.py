HTML = """
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css" integrity="sha384-B0vP5xmATw1+K9KRQjQERJvTumQW0nPEzvF6L/Z6nronJ3oUOFUFpCjEUQouq2+l" crossorigin="anonymous">
    <title>Узнать IP адрес</title>
  </head>
  <body class="bg-info">
    <div class="container">
      <h1 class="text-white text-center mx-auto p-2 mt-4 mb-3">Ваш IP-адрес</h1>
      <div class="bg-light card-block mx-auto text-center">
        <h1 class="display-3 p-2">0.0.0.0</h1>
      </div>
    </div>
  </body>
</html>
"""


def process_http_request(environ, start_response):
    status = "200 OK"
    response_headers = [
        ("Content-type", "text/html; charset=utf-8"),
    ]
    start_response(status, response_headers)
    html_as_bytes = HTML.encode("utf-8")
    print(environ)
    return [html_as_bytes]
