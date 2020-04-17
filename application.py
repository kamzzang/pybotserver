from flask import Flask, render_template
import pandas as pd
import sys
import sqlite3

application = Flask(__name__)

# df = pd.read_csv('./data/gmoney_dongbaek_store_geo.csv', encoding='euc-kr')
con = sqlite3.connect("./data/yongin_gmoney_store_giheung.db")
df = pd.read_sql('select * from giheung', con=con)
con.close()

df['경도'] = df['경도'].astype(float)
df['위도'] = df['위도'].astype(float)

# 동백2동 주민센터 기준으로 적용
center_lat = 37.2732065 # df['위도'].mean()
center_lng = 127.1515643 # df['경도'].mean()

lats = list(df['위도'].values)
lngs = list(df['경도'].values)

@application.route("/")
def hello():
    massage = "경기도 용인시 기흥구 지역화폐(Y페이) 가맹점 검색 사이트입니다."
    return massage

@application.route('/gmoney')
def gmoney():
    return render_template("gmoney.html",
                           loc='기흥구',
                           center_lat = center_lat,
                           center_lng = center_lng,
                           titles = list(df['상호명'].values),
                           pos_data = zip(lats, lngs)
                           )

@application.route('/kakao')
def kakao():
    return render_template("gmoneykakao.html")

@application.route('/ex')
def index():#titles, lats, lngs):
    return render_template("gmoneyex.html")


if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000)
