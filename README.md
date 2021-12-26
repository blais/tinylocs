# A Shortlinks Server on Google Cloud Run

This is my personal shortlinks server on hosted on Google Cloud Run and Google
Cloud Datastore. It's intended to be as simple as possible.

See Makefile for details.

To create a link from the command-line, use a PUT request:

    curl -X PUT    http://go.mysite.com/<NAME> -d 'passphrase=<PASSPHRASE>' -d 'url=<URL>'

To delete a link from the command-line, use a DELETE request:

    curl -X DELETE http://go.mysite.com/<NAME> -d 'passphrase=<PASSPHRASE>'
