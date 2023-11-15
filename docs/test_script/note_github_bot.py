# -*- coding: utf-8 -*-
# @Time    : 2023/11/15 下午9:49
# @Author  : sudoskys
# @File    : note_github_bot.py
# @Software: PyCharm
import os

import requests
from dotenv import load_dotenv
from flask import Flask, request
from github import Github, GithubIntegration

load_dotenv()

__flask_app_name__ = 'github_bot'
app = Flask(__flask_app_name__)
app_id = int(os.environ['GITHUB_APP_ID'])
with open(
        os.path.normpath(os.path.expanduser(os.getenv("GITHUB_PRIVATE_KEY_FILE", '~/.certs/github/bot_key.pem'))),
        'r'
) as cert_file:
    app_key = cert_file.read()

git_integration = GithubIntegration(
    app_id,
    app_key,
)


@app.route("/", methods=['POST'])
def bot():
    # Get the event payload
    payload = request.json
    # Check if the event is a GitHub PR creation event
    if not all(k in payload.keys() for k in ['action', 'pull_request']) and \
            payload['action'] == 'opened':
        return "ok"
    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']
    # Get a git connection as our bot
    # Here is where we are getting the permission to talk as our bot and not
    # as a Python webservice
    git_connection = Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )
    repo = git_connection.get_repo(f"{owner}/{repo_name}")

    issue = repo.get_issue(number=payload['pull_request']['number'])

    # Call meme-api to get a random meme
    response = requests.get(url='https://meme-api.herokuapp.com/gimme')
    if response.status_code != 200:
        return 'ok'

    # Get the best resolution meme
    meme_url = response.json()['preview'][-1]
    # Create a comment with the random meme
    issue.create_comment(f"![Alt Text]({meme_url})")
    return "ok"


if __name__ == "__main__":
    app.run(debug=True, port=5000)
