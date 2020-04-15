from flask import Flask, render_template
import pandas as pd
import sys
application = Flask(__name__)

df = pd.read_csv('./data/gmoney_dongbaek_store_geo.csv', encoding='euc-kr')
df['경도'] = df['경도'].astype(float)
df['위도'] = df['위도'].astype(float)

lats = list(df['위도'].values)
lngs = list(df['경도'].values)

@application.route("/")
def hello():
    massage = "gmoney, kakao, ex"
    return massage

@application.route('/gmoney')
def gmoney():
    return render_template("gmoney.html",
                    center_lat = df['위도'].mean(), 
                    center_lng = df['경도'].mean(),
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
