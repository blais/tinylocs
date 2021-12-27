# A Shortlinks Server on Google Cloud Run

This is my personal shortlinks server. Design goals:

- As simple as possible, with a web UI.
- Hosted on Google Cloud Run and used Google Cloud Datastore. (This costs roughly
  ~0 to run and you don't have to manage a VM).

See Makefile for details.

To create a link from the command-line, use a PUT request:

    curl -X PUT    http://go.mysite.com/<NAME> -d 'passphrase=<PASSPHRASE>' -d 'url=<URL>'

To delete a link from the command-line, use a DELETE request:

    curl -X DELETE http://go.mysite.com/<NAME> -d 'passphrase=<PASSPHRASE>'
