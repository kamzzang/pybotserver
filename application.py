from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import sys
import sqlite3
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
url = 'https://movie.naver.com/movie/running/current.nhn' # 네이버 영화 웹 페이지 - 현재 상영영화 - 예매순
response = requests.get(url)
soup_rank = BeautifulSoup(response.text, 'html.parser')

url = 'https://movie.naver.com/movie/running/premovie.nhn?order=reserve' # 네이버 영화 웹 페이지 - 개봉 예정 영화 - 예매순
response = requests.get(url)
soup_schdule = BeautifulSoup(response.text, 'html.parser')
# 카카오톡 챗봇 영화 제공서비스 실행 함수
def movie_search(search_type, start_cnt): 
    
    img_url = []        # 포스터 경로 url
    title = []          # 영화 제목
    description = []    # 세부 정보 : 영화 예매 순위 응답 - 평점과 예매율, 개봉 예정작 응답 - 개봉예정일
    link_url = []       # 영화 예매 및 정보가 제공되는 사이트로 연결을 위한 웹 페이지 경로 url
    
    if search_type == 'rank': # 영화 예매 순위 요청
        soup = soup_rank
        
        img_tag = soup.find_all("div", {"class":"thumb"})   # 영화 포스터 이미지, 제목, 정보제공 링크가 있는 태그
        cnt = 1
        for src in img_tag:
            if cnt >= start_cnt and cnt < start_cnt+5:      # 카트 리스트 응답은 한번에 최대 5개만 가능하므로 정보를 5개만 저장함
                src_img = src.find('img')
                img_url.append(src_img.get('src'))
                title.append(src_img.get('alt'))

                src_link = src.find('a')
                link_url.append('https://movie.naver.com' + src_link.get('href')) # 링크 url 완성
            cnt+=1
        img_url.insert(0,'')            # 카트 리스트로 응답을 보내기 위해서 위해 첫 인덱스에는 제목같은 내용이 들어가므로 각 데이터에 내용 삽입
        title.insert(0,'영화 예매 순위') # 카트 리스트 제목
        link_url.insert(0,url)          # 카트 리스트 제목란은 크롤링 페이지로 이동가능하도록 링크 삽입

        get_score = soup.find_all("span",{"class" : "num"}) # 평점과 예매율이 있는 태크
        cnt=1
        temp=''
        for i in get_score:
            if start_cnt == 1:
                if cnt >= 1 and cnt < 11: # 평점, 예매율이 번갈아 가면서 저장되기 때문에 5개의 영화에 대해서 총 10개의 데이터를 받음
                    if cnt % 2 == 1: 
                        temp = i.text
                    else:
                        description.append('평점 : ' + temp + '\t' + '예매율 : ' + i.text + '%') # 세부 정보에 평점과 예매율 저장
            else:
                if cnt >= 11 and cnt < 21: 
                    if cnt % 2 == 1: 
                        temp = i.text
                    else:
                        description.append('평점 : ' + temp + '\t' + '예매율 : ' + i.text + '%')
            cnt+=1
        description.insert(0,'')
        
        button_message = "영화 예매 순위 더보기" # 총 10위까지 응답을 위해서 첫 메시지에는 "순위 더보기 버튼"을 넣어주기 위한 버튼 클릭 시 발화되는 메세지
        
    else:
        soup = soup_schdule
        
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

    answer = '날씨 정보 제공 서비스 준비중입니다.' # 날씨 정보는 추후 작업 예정
    
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

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=True)
