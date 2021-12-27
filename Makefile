#!/usr/bin/env make
# Makefile for building my personal shortlnks website on Google Cloud Run.

PROJECT=static-website-with-ssh
SERVICE=go-furius-ca
REGION=us-east4
DOMAIN=go.furius.ca
PORT=8080
IMAGE=us-docker.pkg.dev/$(PROJECT)/gcr.io/$(SERVICE)
GOOGLE_APPLICATION_CREDENTIALS=$(HOME)/.google/static-website-with-ssh-c3c90494d39e.json
APPDIR=.

# Note: Set the real passphrase in the Google Cloud Run "environments & secrets".
TINYLOCS_PASS=enter
export TINYLOCS_PASS

# Build a local version of the container.
build:
	docker build --tag $(SERVICE) $(APPDIR)

# Push the container to the artifacts repository.
push:
	docker tag $(SERVICE) $(IMAGE)
	docker push $(IMAGE):latest

# Deploy the container to furius.ca.
deploy:
	gcloud run deploy $(SERVICE) --image $(IMAGE) --region=$(REGION) --allow-unauthenticated

# Run the container locally for testing.
CREDS =											\
   -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/static-website-with-ssh.json		\
   -v $(GOOGLE_APPLICATION_CREDENTIALS):/tmp/keys/static-website-with-ssh.json:ro	\
   -e TINYLOCS_PASS=$(TESTPASS)

debug:
	PYTHONUNBUFFERED=1 FLASK_ENV=development gunicorn --bind :8080 --workers 2 --threads 8 --timeout 0 tinylocs.app:app

local:
	PYTHONUNBUFFERED=1 FLASK_ENV=development FLASK_APP=tinylocs.app:app flask run --port=8080

run docker-run:
	docker run -p 8080:$(PORT) -e PORT=$(PORT) $(CREDS) $(SERVICE)

# DNS mappings commands.
MAPPINGS_CMD = gcloud beta run domain-mappings --region=$(REGION)

list-mapping:
	$(MAPPINGS_CMD) list
delete-mapping:
	$(MAPPINGS_CMD) delete --domain=$(DOMAIN)
create-mapping:
	$(MAPPINGS_CMD) create --domain=$(DOMAIN) --service=$(SERVICE)
describe-mapping:
	$(MAPPINGS_CMD) describe --domain=$(DOMAIN)
