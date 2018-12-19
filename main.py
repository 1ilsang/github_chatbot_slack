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
ERR_TEXT = "명령어가 잘못됐거나 없는 유저입니다. 도움말은 help 를 입력해 주세요."

# Help desk
def _help_desk():
    keywords = []
    keywords.append("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")
    keywords.append("\n")
    keywords.append("HELP:: 명령어 리스트.")
    keywords.append("\n")
    keywords.append("\t1. music : 벅스에서 인기순위 탑 10을 출력합니다.")
    keywords.append("\n")
    keywords.append("\t2. {아이디}, {행동1}, {행동2}, ... : 각 { } 안에 명령어를 넣어주세요.")
    keywords.append("\t\t\t{아이디}, 0 : 해당 아이디의 정보를 출력합니다.")
    keywords.append("\t\t\t{아이디}, 1 : 해당 아이디의 팔로워들의 활동정보 10개를 보여줍니다.")
    keywords.append("\t\t\t{아이디}, 2, 1 : 해당 아이디의 마지막 푸쉬 날짜, 횟수를 출력합니다.")
    keywords.append("\t\t\t{아이디}, 2, 2 : 1년간 해당 아이디가 가장 많이 푸쉬한 날을 출력합니다.")
    keywords.append("\t\t\t{아이디}, yyyy/mm/dd : yyyy/mm/dd 일에 푸쉬한 횟수를 출력합니다.")
    keywords.append('\n')
    keywords.append('\n')
    keywords.append("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")
    
    return u'\n'.join(keywords)

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

# 인자로 받은 아이디의 정보를 출력한다.
def _get_user_profile(userId):
    # userId = userId.replace(',', '')
    url = "https://github.com/" + userId

    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")
    
    keywords = []
    name = soup.find('span', class_='p-name vcard-fullname d-block overflow-hidden').get_text()
    bio = soup.find('div', class_='d-inline-block mb-3 js-user-profile-bio-contents')
    print(bio)
    company = soup.find('span', class_='p-org').get_text()
    location = soup.find('span', class_='p-label').get_text()
    email = str(soup.find('a', class_='u-email'))
    url = soup.find('a', class_='u-url').get_text()
    # repositories = soup.find('span', class_='Counter')
    # stars = soup.find('', class_='')
    # followers = soup.find('', class_='')
    # following = soup.find('', class_='')
    # organizations = soup.find('', class_='')
    
    keywords.append("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")
    keywords.append("\n")
    keywords.append("ID : " + userId)
    keywords.append("Name : " + name)
    # keywords.append("Bio : " + bio)
    keywords.append("Company : " + company)
    keywords.append("Location : " + location)
    keywords.append("Email : " + email)
    keywords.append("Link URL : " + url)
    keywords.append("Repositories : " + ", Stars : " + ", Followers : " + ", Following : ")
    keywords.append("Organizations : ")
    keywords.append("\n")
    keywords.append("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")
    
    return u'\n'.join(keywords)
    
# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"][13:].replace(',', '').split()

        # textList = [cmd for cmd in text if]
        # print(textList)
        if text[0] == 'music':
            keywords = _crawl_naver_keywords(text)
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=keywords
            )
            return make_response("App mention message has been sent", 200,)
        
        elif text[0] == 'help':
            keywords = _help_desk()
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=keywords
            )
            return make_response("App mention message has been sent", 200,)
            
        elif text[1] == '0':
            keywords = _get_user_profile(text[0])
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=keywords
            )
            return make_response("App mention message has been sent", 200,)
            
        else:
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=ERR_TEXT
            )
            return make_response("App mention message has been sent", 401,)

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

