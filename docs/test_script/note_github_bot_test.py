# -*- coding: utf-8 -*-
# @Time    : 2023/11/15 下午10:19
# @Author  : sudoskys
# @File    : note_github_bot_test.py
# @Software: PyCharm
import os

from dotenv import load_dotenv
from github_bot_api import Event, Webhook
from github_bot_api import GithubApp
from github_bot_api.flask import create_flask_app

load_dotenv()

app_id = int(os.environ['GITHUB_APP_ID'])
with open(
        os.path.normpath(os.path.expanduser(os.getenv("GITHUB_PRIVATE_KEY_FILE", '~/.certs/github/bot_key.pem'))),
        'r'
) as cert_file:
    app_key = cert_file.read()

app = GithubApp(
    user_agent='my-bot/0.0.0',
    app_id=app_id,
    private_key=app_key
)

webhook = Webhook(secret=None)


@webhook.listen('issues')
def on_pull_request(event: Event) -> bool:
    print(event.payload)
    client = app.installation_client(event.payload['installation']['id'])
    repo = client.get_repo(event.payload['repository']['full_name'])
    issue = repo.get_issue(number=event.payload['issue']['number'])
    issue.create_comment('Hello World')
    return True


@webhook.listen('issue_comment')
def on_issue_comment(event: Event) -> bool:
    print(event.payload)
    client = app.installation_client(event.payload['installation']['id'])
    repo = client.get_repo(event.payload['repository']['full_name'])
    issue = repo.get_issue(number=event.payload['issue']['number'])
    issue.edit(
        body=f"Hello World\n\n{issue.body}"

    )
    return True


import os

os.environ['FLASK_ENV'] = 'development'
flask_app = create_flask_app(__name__, webhook)
flask_app.run()
