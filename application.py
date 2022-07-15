from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import sys
import sqlite3
import json
# crawling용 모듈
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import requests
import urllib

application = Flask(__name__)

# ---------------------------------------------------------------------------
# 지역화폐 가맹정 서비스
# ---------------------------------------------------------------------------
# 용인시 데이터 로딩 및 초기 데이터 준비
con = sqlite3.connect("./data/yongin_gmoney_store_giheung_suji.db")
df_yongin = pd.read_sql('select * from store', con=con)
con.close()

df_yongin['경도'] = df_yongin['경도'].astype(float)
df_yongin['위도'] = df_yongin['위도'].astype(float)
df_yongin['업종분류'] = df_yongin['업종분류'].astype(int)

yselected_gu='기흥구'
yselected_dong='동백동'

ydong_list = list(df_yongin[df_yongin['구']==yselected_gu]['동'].unique())
ydata = df_yongin[(df_yongin['구']==yselected_gu) & (df_yongin['동']== yselected_dong)]

ylats = list(ydata['위도'].values)
ylngs = list(ydata['경도'].values)

# 서울 강동구 데이터 로딩 및 초기 데이터 준비
con = sqlite3.connect("./data/seoul_zmoney_store_gangdong.db")
df_seoul = pd.read_sql('select * from store', con=con)
con.close()

df_seoul['경도'] = df_seoul['경도'].astype(float)
df_seoul['위도'] = df_seoul['위도'].astype(float)
df_seoul['업종분류'] = df_seoul['업종분류'].astype(int)

sselected_gu='강동구'
sselected_dong='명일동'

sdong_list = list(df_seoul[df_seoul['구']==sselected_gu]['동'].unique())
sdata = df_seoul[(df_seoul['구']==sselected_gu) & (df_seoul['동']== sselected_dong)]

slats = list(sdata['위도'].values)
slngs = list(sdata['경도'].values)

# ---------------------------------------------------------------------------
# 카카오톡 챗봇
# ---------------------------------------------------------------------------
# 카카오톡 챗봇을 위한 데이터 준비
# url = 'https://movie.naver.com/movie/running/current.nhn' # 네이버 영화 웹 페이지 - 현재 상영영화 - 예매순
# response = requests.get(url)
# soup_rank = BeautifulSoup(response.text, 'html.parser')

# url = 'https://movie.naver.com/movie/running/premovie.nhn?order=reserve' # 네이버 영화 웹 페이지 - 개봉 예정 영화 - 예매순
# response = requests.get(url)
# soup_schdule = BeautifulSoup(response.text, 'html.parser')
# 카카오톡 챗봇 영화 제공서비스 실행 함수
def movie_search(search_type, start_cnt): 
    movie_url = { 'rank' : 'https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&qvt=0&query=%EB%B0%95%EC%8A%A4%EC%98%A4%ED%94%BC%EC%8A%A4', # 네이버 박스오피스 검색 결과 페이지
                  'schdule' : 'https://movie.naver.com/movie/running/premovie.nhn?order=reserve' # 네이버영화 개봉 예정작 예매순 1~20위 
                }

    img_url = []        # 포스터 경로 url
    title = []          # 영화 제목
    description = []    # 세부 정보 : 영화 예매 순위 응답 - 평점과 예매율, 개봉 예정작 응답 - 개봉예정일
    link_url = []       # 영화 예매 및 정보가 제공되는 사이트로 연결을 위한 웹 페이지 경로 url
    
    if search_type == 'rank': # 영화 예매 순위 요청
        url = movie_url[search_type]
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # soup = soup_rank

        total_tag = soup.find("ul", {"class": "_panel"})

        img_tag = soup.find_all("div", {"class":"thumb"})           # 영화 포스터 이미지, 제목 태그
        link_tag = total_tag.find_all("a")                          # 영화 정보제공 링크
        sub_tag = total_tag.find_all("span", {"class": "sub_text"}) # 관객수

        cnt = 1
        for src, link, sub in zip(img_tag, link_tag, sub_tag):
            if cnt >= start_cnt and cnt < start_cnt + 5:  # 카트 리스트 응답은 한번에 최대 5개만 가능하므로 정보를 5개만 저장함
                src_img = src.find('img')
                img_url.append(src_img.get('src'))
                title.append(src_img.get('alt'))
                link_url.append('https://search.naver.com/search.naver' + link.get('href'))
                description.append('관객수 : ' + sub.text)
            cnt+=1

        img_url.insert(0,'')            # 카트 리스트로 응답을 보내기 위해서 위해 첫 인덱스에는 제목같은 내용이 들어가므로 각 데이터에 내용 삽입
        title.insert(0,'박스오피스 순위')  # 카트 리스트 제목
        link_url.insert(0,url)          # 카트 리스트 제목란은 크롤링 페이지로 이동가능하도록 링크 삽입
        description.insert(0,'')
        
        button_message = "박스오피스 순위 더보기" # 총 10위까지 응답을 위해서 첫 메시지에는 "순위 더보기 버튼"을 넣어주기 위한 버튼 클릭 시 발화되는 메세지
        
    else:
        url = movie_url[search_type]
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # soup = soup_schdule
        
        img_tag = soup.find_all("div", {"class":"thumb"})
        cnt = 1
        for src in img_tag:
            if cnt >= start_cnt and cnt < start_cnt+5:
                src_img = src.find('img')
                img_url.append(src_img.get('src'))
                title.append(src_img.get('alt'))

                src_link = src.find('a')
                link_url.append('https://movie.naver.com' + src_link.get('href'))
            cnt+=1
        img_url.insert(0,'')
        title.insert(0,'개봉예정 영화')
        link_url.insert(0,url)
        
        sch_date = soup.find_all("dl", {'class' : 'info_txt1'})
        cnt=1
        for i in sch_date:
            if cnt >= start_cnt and cnt < start_cnt+5:
                temp = i.text.replace('\t','').replace('\n','').replace('\r','').split(',')
                for text in temp:
                    if '개봉' in text: temp=text
                temp = temp.split('|')[-1].split('감독')[0]
                description.append(temp)
            cnt+=1
        description.insert(0,'')
        
        button_message = "개봉 예정 영화 더보기"

    # 응답 메시지가 첫 메시지인지 더보기 요청인지에 따라 첫 메시지일 때만 "더보기" 버튼 생성, 순위 표시    
    if start_cnt == 1: # 첫번째 응답 메시지에 순위와 출처 추가 및 버튼 생성
        title[0] = title[0] + '(1위~5위)_출처: Naver영화' 
        button_data = [
                        {
                          "type": "block",
                          "label": "+ 더보기",
                          "message" : button_message, # 버튼 클릭 시 사용자가 전송한 것과 동일하게 하는 메시지
                          "data": {
                            }
                        }
                      ]
    else:
        title[0] = title[0] + '(6위~10위)_출처: Naver영화'
        button_data = [
                {
                  "type": "text", # 버튼 타입을 텍스트로 하고 라벨 및 메시지를 비우면 버튼이 나오지 않음(두 번의 메시지를 동일한 포맷으로 res 변수로 만들기 위함)
                  "label": "",
                  "message" : "",
                  "data": {
                    }
                }
              ]
        
        
    listItems=[]

    cnt=0
    for i in range(6): # 응답용 카트 리스트 타입의 res에 추가할 정보 완성
        if cnt == 0: itemtype = 'title' # 카드 이미지의 첫 type은 title
        else: itemtype = 'item'         # 카드 이미지의 제목 다음 type은 item
            
        listItems.append({
                "type": itemtype,               # 카드 리스트의 아이템 티입
                "imageUrl": img_url[i],         # 이미지 링크 url
                "title": title[i],              # 제목
                "description": description[i],  # 세부 정보
                "linkUrl": {
                  "type": "OS",                 # PC나 모바일별 별도 url설정 가능하나 web용으로 동일 적용
                    "webUrl": link_url[i]       # 영화 정보 링크 url
                    }
                })
        cnt+=1
        
    return listItems, button_data

@application.route("/")
def hello():
    return render_template("index.html")

# ---------------------------------------------------------------------------
# 지역화폐 가맹정 서비스 route
# ---------------------------------------------------------------------------
@application.route('/gmoney')
def gmoney():
    return render_template("gmoney.html", 
                        selected_gu = yselected_gu,
                        selected_dong = yselected_dong,
                        selected_category = '전체',
                        dong_list = ydong_list,
                        center_lat = ydata['위도'].mean(), 
                        center_lng = ydata['경도'].mean(),
                        titles = list(ydata['상호명'].values),
                        category = list(ydata['업종분류'].values),
                        pos_data = zip(ylats, ylngs)
                        )

@application.route('/gmoney/ysearch', methods=['GET','POST'])
def ysearch():
    if request.method == 'POST':
        yselected_gu = request.form.get('select_gu')
        yselected_dong = request.form.get('select_dong')
        yselected_category = request.form['options']

        ydong_list = list(df_yongin[df_yongin['구']==yselected_gu]['동'].unique())
        if yselected_category == '전체':
            ydata = df_yongin[(df_yongin['구']==yselected_gu) & (df_yongin['동']== yselected_dong)]
        else:
            ydata = df_yongin[(df_yongin['구']==yselected_gu) & (df_yongin['동']== yselected_dong) & (df_yongin['업종']==yselected_category)]
            if ydata.empty:
                center_lat = df_yongin[(df_yongin['구']==yselected_gu) & (df_yongin['동']==yselected_dong)]['위도'].mean()
                center_lng = df_yongin[(df_yongin['구']==yselected_gu) & (df_yongin['동']==yselected_dong)]['경도'].mean()
            else:
                center_lat = ydata['위도'].mean()
                center_lng = ydata['경도'].mean()

        if yselected_dong == '마북동':
            center_lat = 37.3015845
            center_lng = 127.1152282
        elif yselected_dong == '보정동':
            center_lat = 37.3201946
            center_lng = 127.1109263
        else:
            center_lat = ydata['위도'].mean()
            center_lng = ydata['경도'].mean()

        ylats = list(ydata['위도'].values)
        ylngs = list(ydata['경도'].values)
        return render_template("gmoney.html", 
                    selected_gu = yselected_gu,
                    selected_dong = yselected_dong,
                    selected_category = yselected_category,
                    dong_list = ydong_list,
                    center_lat = center_lat, 
                    center_lng = center_lng,
                    titles = list(ydata['상호명'].values),
                    category = list(ydata['업종분류'].values),
                    pos_data = zip(ylats, ylngs)
                    )

@application.route('/zmoney')
def zmoney():
    return render_template("zmoney.html", 
                        selected_gu = sselected_gu,
                        selected_dong = sselected_dong,
                        selected_category = '전체',
                        dong_list = sdong_list,
                        center_lat = sdata['위도'].mean(), 
                        center_lng = sdata['경도'].mean(),
                        titles = list(sdata['상호명'].values),
                        category = list(sdata['업종분류'].values),
                        pos_data = zip(slats, slngs)
                        )

@application.route('/zmoney/ssearch', methods=['GET','POST'])
def ssearch():
    if request.method == 'POST':
        sselected_gu = request.form.get('select_gu')
        sselected_dong = request.form.get('select_dong')
        sselected_category = request.form['options']

        sdong_list = list(df_seoul[df_seoul['구']==sselected_gu]['동'].unique())
        if sselected_category == '전체':
            sdata = df_seoul[(df_seoul['구']==sselected_gu) & (df_seoul['동']==sselected_dong)]
            center_lat = sdata['위도'].mean()
            center_lng = sdata['경도'].mean()
        else:
            sdata = df_seoul[(df_seoul['구']==sselected_gu) & (df_seoul['동']==sselected_dong) & (df_seoul['업종']==sselected_category)]
            if sdata.empty:
                center_lat = df_seoul[(df_seoul['구']==sselected_gu) & (df_seoul['동']==sselected_dong)]['위도'].mean()
                center_lng = df_seoul[(df_seoul['구']==sselected_gu) & (df_seoul['동']==sselected_dong)]['경도'].mean()
            else:
                center_lat = sdata['위도'].mean()
                center_lng = sdata['경도'].mean()

        slats = list(sdata['위도'].values)
        slngs = list(sdata['경도'].values)

        return render_template("zmoney.html", 
                    selected_gu = sselected_gu,
                    selected_dong = sselected_dong,
                    selected_category = sselected_category,
                    dong_list = sdong_list,
                    center_lat = center_lat, 
                    center_lng = center_lng,
                    titles = list(sdata['상호명'].values),
                    category = list(sdata['업종분류'].values),
                    pos_data = zip(slats, slngs)
                    )

# ---------------------------------------------------------------------------
# 카카오톡 챗봇 route
# ---------------------------------------------------------------------------
@application.route('/movies', methods=['POST']) # 영화 정보 블럭에 스킬로 연결된 경로
def movies():
    req = request.get_json()
    
    input_text = req['userRequest']['utterance'] # 사용자가 전송한 실제 메시지
    
    if '개봉' in input_text: # 전송 메시지에 "개봉"이 있을 경우는 개봉 예정작 정보를 응답
        search_type = 'schdule'
    else:                   # "개봉"이 메시지에 없으면 예매 순위를 응답
        search_type = 'rank'
        
    if '더보기' in input_text: # 더보기를 요청했을 경우는 메시지에 더보기가 입력되게 설정을 해서 이 경우는 6위부터 10위까지 저장
        start_cnt = 6
    else:
        start_cnt = 1         # 첫 요청일 경우 1위 부터 5위까지 저장

    # 검색 타입(예매 순위 or 개봉 예정작)과 검색 시작 번호를 movie_search 함수로 전달하여 아이템과 버튼 설정을 반환받음  
    listItems, button_data = movie_search(search_type, start_cnt) 

    # 카드 리스트형 응답용 메시지
    res = {
          "contents": [
            {
              "type": "card.list",
              "cards": [
                {
                  "listItems": listItems,
                    "buttons": button_data
                }
              ]
            }
          ]
        }            

    # 전송
    return jsonify(res)


@application.route('/weather', methods=['POST']) # 날씨 정보 블럭에 스킬로 연결된 경로
def weather():

    req = request.get_json()
    
    params = req['action']['detailParams']
    if 'sys_location' not in params.keys(): # 입력 텍스트에 지역이 없을 경우는 바로 경고 메시지 전송
        res = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "지역을 입력하세요."
                        }
                    }
                ]
            }
        }

        return jsonify(res)
    if 'sys_location' in params.keys(): # 지역을 시 구 동으로 3개까지 입력을 받을 수 있어서 순서대로 location에 저장
        location = params['sys_location']['value']
    if 'sys_location1' in params.keys():
        location += ' + ' + params['sys_location1']['value']
    if 'sys_location2' in params.keys():
        location += ' + ' + params['sys_location2']['value']
    
    location_encoding = urllib.parse.quote(location + '+날씨') # url 인코딩
    url = 'https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query=%s'%(location_encoding)
    
    req = Request(url)
    page = urlopen(req)
    html = page.read()
    soup = BeautifulSoup(html, 'html.parser')
    
    # if soup.find('span', {'class':'btn_select'})==None:    # 동일 시에 구만 다른 같은 이름의 동이 있을 경우 에러발생
    #     region = soup.find('li', {'role' : 'option'}).text
    # else:
    #     region = soup.find('span', {'class':'btn_select'}).text
    region = soup.find('h2', {'class': 'title'}).text

    if 'sys_date_period' in params.keys(): # 주 단위의 날씨를 요청했을 경우
        weekly_weather = soup.find_all('div', {'class': 'day_data'})
        answer = '%s 주간 기상정보입니다.\n\n' % (region)
        for i in weekly_weather:
            answer += i.text.replace('오전', '').replace('오후', '').replace('기온', '') + '\n'


    elif 'sys_date' not in params.keys() or 'today' in params['sys_date']['value']: # 날짜 관련 문구가 없거나 "오늘"을 입력했을 경우
        info = soup.find('p', {'class': 'summary'}).text
        temp = soup.find('div', {'class': 'temperature_text'}).text[6:]

        sub_info_1 = soup.find_all('span', {'class': 'rainfall'})
        rain_rate = '오전 : %s, 오후 : %s' % (sub_info_1[0].text, sub_info_1[1].text)

        sub_info_2 = soup.find_all('li', {'class': 'item_today level2'})
        finedust = sub_info_2[0].text.split(' ')[3]
        Ultrafinedust = sub_info_2[1].text.split(' ')[3]

        answer = '%s 현재 기상정보입니다.\n\n' % (region)
        answer += info + '\n'
        answer += '기온 : ' + temp + '\n'
        answer += '강수확률 : ' + rain_rate + '\n'
        answer += '미세먼지 : ' + finedust + '\n'
        answer += '초미세먼지 : ' + Ultrafinedust
    
    elif 'tomorrow' in params['sys_date']['value']: # 내일 날씨를 요청했을 경우
        def convert(text):
            text = text.split(' ')
            return ' '.join(text).split()

        tomorrow = soup.find_all('div', {'class': 'day_data'})[1].text
        tomorrow = convert(tomorrow)
        answer = '%s 내일 기상정보입니다.\n\n' % (region)
        answer += '기온 : ' + tomorrow[-3].replace('기온', ' ') + '/ ' + tomorrow[-1].replace('기온', ' ') + '\n'
        answer += '강수확률 : ' + tomorrow[2] + '\n'
        
    # 일반 텍스트형 응답용 메시지
    res = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": answer
                    }
                }
            ]
        }
    }

    return jsonify(res)


@application.route('/locsearch', methods=['POST']) # 길찾기 정보 블럭에 스킬로 연결된 경로
def locsearch():
    req = request.get_json()
    
    params = req['action']['detailParams']
    
    keyword = params['keyword']['value'] # 되묻기를 통해서 입력받은 일반 text형 키워드(날씨에서 사용하는 지역으로 인식되지 않게 하기 위함)
    
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json?query='+keyword
    headers = {"Authorization": "KakaoAK b0ac56c826bb8e11d36f4eef04a186ec"}
    result = json.loads(str(requests.get(url,headers=headers).text))
    
    search_url = []
    title = []
    
    if len(result['documents']) > 0: # 입력받은 키워드 값으로 API 호출 시 값이 있을 경우 저장함
        for data in result['documents']:
            title.append(data['place_name'])
            search_url.append('https://map.kakao.com/link/to/{}'.format(data['id']))

        title.insert(0,'카카오맵 길찾기로 연결됩니다.')
        search_url.insert(0,'')
    else:
        res = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "검색이 불가한 지역입니다."
                        }
                    }
                ]
            }
        }
        return jsonify(res) 
        
    listItems=[]

    cnt=0
    if len(title) >= 5: items = 6
    else: items = len(title)
        
    for i in range(items): # 응답용 카트 리스트 타입의 res에 추가할 정보 완성
        if cnt == 0: itemtype = 'title' # 카드 이미지의 첫 type은 title
        else: itemtype = 'item'         # 카드 이미지의 제목 다음 type은 item
            
        listItems.append({
                "type": itemtype,               # 카드 리스트의 아이템 티입
                "title": title[i],              # 제목
                "linkUrl": {
                  "type": "OS",                 # PC나 모바일별 별도 url설정 가능하나 web용으로 동일 적용
                    "webUrl": search_url[i]       # 영화 정보 링크 url
                    }
                })
        cnt+=1

    # 카드 리스트형 응답용 메시지
    res = {
          "contents": [
            {
              "type": "card.list",
              "cards": [
                {
                  "listItems": listItems
                }
              ]
            }
          ]
        }            

    # 전송
    return jsonify(res)

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=True)
