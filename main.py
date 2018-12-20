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
ERR_TEXT = "명령어가 잘못됐거나 없는 유저입니다. 도움말은 *help* 를 입력해 주세요."


# Help desk
def _help_desk():
    keywords = []
    keywords.append("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")
    keywords.append("\n")
    keywords.append("HELP:: 명령어 리스트.")
    keywords.append("\n")
    keywords.append("\t1. *music* : 벅스에서 인기순위 탑 10을 출력합니다.")
    keywords.append("\n")
    keywords.append("\t2. *{아이디}*, *{행동1}* : 각 { } 안에 명령어를 넣어주세요.")
    keywords.append("\t\t\t{아이디}, 0 : 해당 아이디의 정보를 출력합니다.")
    keywords.append("\t\t\t{아이디}, 1 : 해당 아이디의 반 년간 푸쉬량을 그래프로 보여줍니다.")
    # keywords.append("\t\t\t{아이디}, 2 : 해당 아이디의 친구들?.")
    keywords.append("\t\t\t{아이디}, yyyy-mm-dd : yyyy-mm-dd 일에 푸쉬한 횟수를 출력합니다.")
    keywords.append('\n')
    keywords.append('\n')
    keywords.append("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")

    return u'\n'.join(keywords)


# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    # 여기에 함수를 구현해봅시다.
    url = "https://music.bugs.co.kr/"
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

    keywords = []

    artists = soup.find_all('p', class_='artist')

    keywords.append("*Bugs 실시간 음악 차트 Top 10*")
    keywords.append('\n')
    # for i, artist in enumerate(soup.find_all('p', class_='artist')):
    #     if i < 10:
    #         artists.append(artist.get_text().split())
    for i, keyword in enumerate(soup.find_all("p", class_="title")):
        if i < 10:
            row = "\t" + str(i + 1) + "위:  " + keyword.get_text().replace('\n', '') + " / " + str(
                artists[i].get_text().strip())
            keywords.append(row)

    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'\n'.join(keywords)


# 인자로 받은 아이디의 정보를 출력한다.
def _get_user_profile(userId):
    url = "https://github.com/" + userId

    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

    keywords = []

    data = {}
    data['name'] = soup.find('span', class_='p-name vcard-fullname d-block overflow-hidden')
    data['bio'] = soup.find('div', class_='p-note user-profile-bio mb-3').find('div')
    data['company'] = soup.find('span', class_='p-org')
    data['location'] = soup.find('span', class_='p-label')
    data['email'] = soup.find('li', {'itemprop': 'email'})
    data['url'] = soup.find('li', {'itemprop': 'url'})

    for i, j in data.items():
        try:
            if i == 'email' or i == 'url':
                data[i] = str(j.find('a').get_text())
            else:
                data[i] = str(j.get_text())
        except:
            data[i] = 'None'

    rsffList = soup.find_all('a', class_='UnderlineNav-item')
    del rsffList[0]
    rsff = []
    for i in rsffList:
        try:
            ret = rsff.append(i.find('span').get_text().strip())
        except:
            break

    organizations = soup.find_all('a', class_='avatar-group-item')
    orgList = []
    for i in organizations:
        try:
            orgList.append(i.find('img')['alt'])
        except:
            break;

    keywords.append("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")
    keywords.append("\n")
    keywords.append("\tID : " + userId)
    keywords.append("\tName : " + data['name'])
    keywords.append("\tBio : " + data['bio'])
    keywords.append("\n")
    keywords.append("\tCompany : " + data['company'])
    keywords.append("\tLocation : " + data['location'])
    keywords.append("\tEmail : " + data['email'])
    keywords.append("\tLink URL : " + data['url'])
    keywords.append(
        "\t*Repositories : " + rsff[0] + ",   Stars : " + rsff[1] + ",   Followers : " + rsff[2] + ",   Following : " +
        rsff[3] + "*")
    keywords.append("\n")
    keywords.append("\tOrganizations : ")
    tmp = []
    for i in orgList:
        tmp.append(i)
    keywords.append("\t\t" + str(tmp))
    keywords.append("\n")
    keywords.append("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")

    return u'\n'.join(keywords)


# 인자로 받은 아이디의 컨트리뷰션 그래프를 출력한다.
def _get_contributions_graph(userId):
    url = "https://github.com/" + userId
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

    keywords = []
    keywords.append("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")
    keywords.append("\n")
    keywords.append(str(userId) + " 님의 활동 그래프 (9 번이 넘는 커밋은 *9 로 표시* 되었습니다).")
    keywords.append("\n")

    cgraph = soup.find_all('rect', class_="day")[175:]

    totalCnt = 0
    maxCnt = 0
    maxDD = ''

    for i in range(0, 7):
        rgraph = []
        cnt = i
        while cnt < len(cgraph):
            try:
                ret = int(cgraph[cnt]['data-count'])
                if maxCnt < ret:
                    maxCnt = ret
                    maxDD = cgraph[cnt]['data-date']

                totalCnt += ret

                if ret > 9:
                    ret = 9

                rgraph.append(str(ret))
            except:
                break
            cnt += 7
        keywords.append("\t" + str(rgraph))

    keywords.append("\n")
    keywords.append("\t반년간 토탈 푸쉬 횟수 : *" + str(totalCnt) + "*")
    keywords.append("\t가장 많이한 푸쉬 횟수 : *" + str(maxCnt) + "*")
    keywords.append("\t가장 많이 푸쉬한 날짜 : *" + str(maxDD) + "*")
    keywords.append("\n")
    keywords.append("\n")
    keywords.append("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")

    return u'\n'.join(keywords)


# yyyy/mm/dd 일에 해당하는 푸쉬 수를 출력
def _get_dd_contribution(userId, dd):
    url = "https://github.com/" + userId
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")
    cgraph = soup.find_all('rect', class_="day")

    ret = -1

    for i in range(len(cgraph)):
        if cgraph[i]['data-date'] == dd:
            ret = cgraph[i]['data-count']
            break

    keywords = []
    keywords.append("\n")
    if ret == -1:
        keywords.append(">\t\t날짜를 초과하셨습니다.")
    else:
        keywords.append(">\t\t" + str(userId) + " 님의 " + str(dd) + " 일 푸쉬량 : *" + str(ret) + "*")
    keywords.append("\n")

    return u'\n'.join(keywords)


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        try:
            text = slack_event["event"]["text"][13:].replace(',', '').split()
            compile_text = re.compile(r'\d\d\d\d-\d\d-\d\d')

            if len(text) > 1:
                match_text = compile_text.findall(text[1])

            keywords = ERR_TEXT

            STATUS_CODE = 100
            if text[0] == 'music':
                keywords = _crawl_naver_keywords(text)

            elif text[0] == 'help':
                keywords = _help_desk()

            elif text[1] == '0':
                keywords = _get_user_profile(text[0])

            elif text[1] == '1':
                keywords = _get_contributions_graph(text[0])

            elif len(text) > 1 and match_text[0] is not None:
                keywords = _get_dd_contribution(text[0], match_text[0])

            else:
                keywords = ERR_TEXT
                STATUS_CODE = 400

            if STATUS_CODE != 400:
                STATUS_CODE = 200
        except:
            STATUS_CODE = 500
            keywords = ERR_TEXT

        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, STATUS_CODE, {"X-Slack-No-Retry": 1})


@app.route("/ss", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)
    # print(slack_event)
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
    app.run('localhost', port=8080, debug=True)
