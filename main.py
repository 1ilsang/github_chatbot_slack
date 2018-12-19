# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template
import secretKey

app = Flask(__name__)

sc = SlackClient(secretKey.slack_token)

# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    
    #여기에 함수를 구현해봅시다.
    url = "https://music.bugs.co.kr/"
    
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")
    
    keywords = []

    artists = soup.find_all('p', class_='artist')

    keywords.append("Bugs 실시간 음악 차트 Top 10")
    keywords.append('\n')
    # for i, artist in enumerate(soup.find_all('p', class_='artist')):
    #     if i < 10:
    #         artists.append(artist.get_text().split())
    for i, keyword in enumerate(soup.find_all("p", class_="title")):
        if i < 10:
            row = "\t" + str(i + 1) + "위:  " + keyword.get_text().replace('\n', '') + " / " + str(artists[i].get_text().strip())
            keywords.append(row)

    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'\n'.join(keywords)

# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        if text[13:] == 'music':
            keywords = _crawl_naver_keywords(text)
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=keywords
            )

            return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

@app.route("/ss", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                            })

    if secretKey.slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)

