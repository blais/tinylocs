"""Example script to read from a bucket."""

# TODO(blais): Implement partial match and typo auto-fixing
# TODO(blais): Implement search
# TODO(blais): Add access statistics (count, latest date)
# TODO(blais): Add expiration date
# TODO(blais): Make a script to upload to Drive and create a link at the same time
# TODO(blais): Support a boolean flag to render in an iframe
# TODO(blais): Auto-clean up Google drive links (remove /edit)
# TODO(blais): Document ids do not support /; figure out how to support those
# TODO(blais): When adding a link, automatically detect if it should be an alias
# (if it is a duplicate)


import os
import logging
import functools
from os import path
from typing import Optional

import flask
from flask import request, redirect, url_for, session, render_template
import wtforms

from google.cloud import firestore


def create_app():
    """Create the application."""
    approot = path.dirname(__file__)
    app = flask.Flask(
        __name__,
        static_folder=path.join(approot, "static"),
        template_folder=path.join(approot, "templates"),
    )
    app.logger.setLevel(logging.INFO)
    app.config["SECRET_KEY"] = "de49e1d6-84cb-42ae-9966-a9ba40031608"
    try:
        app.passphrase = os.environ["TINYLOCS_PASS"]
    except KeyError:
        logging.fatal("Invalid configuration; please set the TINYLOCS_PASS passphrase.")

    return app


app = create_app()


@app.errorhandler(404)
def page_not_found(e):
    """Special handler for not-found situation that prompts to create link."""
    return render_template("404.html"), 404


app.register_error_handler(404, page_not_found)


def login_required(f):
    """Require login on access."""

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login", ref=request.url))
        return f(*args, **kwargs)

    return decorated_function


class LoginForm(wtforms.Form):
    passphrase = wtforms.PasswordField(
        "Passphrase", [wtforms.validators.DataRequired()]
    )


@app.route("/_/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        if form.passphrase.data == app.passphrase:
            session["user"] = "admin"
            ref_url = flask.request.args.get("ref")
            return redirect(ref_url)
        else:
            return flask.abort(403, description="Access denied")
    else:
        return render_template("login.html", form=form)


@app.route("/_/logout")
@login_required
def logout():
    session.pop("user")
    return redirect(url_for("home"))


def get(name: str):
    """Get a document reference by name."""
    db = firestore.Client()
    return db.collection("links").document(name)


@app.route("/<name>", methods=["GET", "PUT", "POST", "DELETE"])
def go(name):
    if request.method == "GET":
        # Fetch link.
        doc_ref = get(name)
        doc = doc_ref.get()
        if not doc.exists:
            return redirect(url_for("entity", name=name))
        return redirect(doc.to_dict()["url"])

    elif request.method in {"PUT", "POST"}:
        # Check passphrase and craete/update link.
        passphrase = request.form.get("passphrase")
        if passphrase != app.passphrase:
            return flask.abort(403, description="Access denied")
        url = request.form.get("url")
        alias = request.form.get("alias")
        update_link(name, alias, url)
        if request.method == "POST":
            return redirect(url_for("done", name=name))
        else:
            # For PUT requests, return for a shell command.
            return "DONE\n"

    elif request.method == "DELETE":
        # Check passphrase and craete/update link.
        passphrase = request.form.get("passphrase")
        if passphrase != app.passphrase:
            return flask.abort(403, description="Access denied")
        update_link(name, None, None)
        return "DONE\n"


def update_link(name, alias, url):
    """Handle adding a link."""
    doc_ref = get(name)
    if not alias and not url:
        # Delete the entity.
        doc = doc_ref.get()
        if not doc.exists:
            return flask.abort(400, description="Name does not exist")
        doc_ref.delete()

    elif not url:
        # Add an alias to an existing entity.
        doc = doc_ref.get()
        if not doc.exists:
            return flask.abort(400, description="Name does not exist")
        docdict = doc.to_dict()
        aliases = docdict.setdefault("alias", [])
        aliases.append(alias)

    else:
        # Create a new entity, possibly with an alias.
        docdict = {"name": name, "url": url}
        if alias:
            docdict["alias"] = alias
        doc_ref.set(docdict)


class LinkForm(wtforms.Form):
    name = wtforms.StringField("name", [wtforms.validators.Length(min=2)])
    alias = wtforms.StringField("alias", [wtforms.validators.Length(min=2)])
    url = wtforms.URLField("url")


@app.route("/_/entity", defaults={"name": None}, methods=["GET", "POST"])
@app.route("/_/entity/<name>", methods=["GET", "POST"])
@login_required
def entity(name: Optional[str]):
    if request.method == "GET":
        doc_ref = get(name)
        doc = doc_ref.get().to_dict()
        form = LinkForm(request.form)
        if doc:
            button_name = "Update"
            for attr, value in doc.items():
                getattr(form, attr).data = value
        else:
            form.name.data = name
            button_name = "Create"
        return render_template("entity.html", form=form, title="Entity", button_name=button_name)

    elif request.method == "POST":
        name = request.form.get("name")
        alias = request.form.get("alias")
        url = request.form.get("url")
        update_link(name, alias, url)
        return redirect(url_for("done", name=name))


@app.route("/_/done/<name>")
@login_required
def done(name: str):
    return render_template("done.html", url=url_for("go", name=name, _external=True))


class SearchForm(wtforms.Form):
    byname = wtforms.StringField("byname", [wtforms.validators.Length(min=2)])


@app.route("/_/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "GET":
        form = SearchForm(request.form)
        return render_template("search.html", form=form)
    elif request.method == "POST":
        byname = request.form.get("byname")
        if byname:
            return redirect(url_for("entity", name=byname))
        else:
            return redirect(url_for("search"), code=303)


@app.route("/")
@login_required
def home():
    return redirect(url_for("entity"))
