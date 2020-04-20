from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import sys
import sqlite3
application = Flask(__name__)

# df = pd.read_csv('./data/gmoney_dongbaek_store_geo.csv', encoding='euc-kr')
con = sqlite3.connect("./data/yongin_gmoney_store_giheung.db")
df = pd.read_sql('select * from giheung', con=con)
con.close()

df['상호명'] = df['업종'] + '_' + df['상호명']
df['경도'] = df['경도'].astype(float)
df['위도'] = df['위도'].astype(float)

dong_list = list(df['동'].unique())
dong_list.sort()
selected_dong='동백동'

data = df[df['동']== selected_dong]

lats = list(data['위도'].values)
lngs = list(data['경도'].values)

@application.route("/")
def hello():
    return render_template("index.html")

@application.route('/gmoney')
def gmoney():
    return render_template("gmoney.html",
                    selected_dong = selected_dong,
                    dong_list = dong_list,
                    center_lat = data['위도'].mean(), 
                    center_lng = data['경도'].mean(),
                    titles = list(data['상호명'].values),
                    pos_data = zip(lats, lngs)
                    )

@application.route('/naver')
def naver():
    return render_template("gmoneyNaver.html")

@application.route('/kakao')
def kakao():
    return render_template("gmoneykakao.html")

@application.route('/ex')
def index():
    return render_template("gmoney_ex.html",
                    selected_dong = selected_dong,
                    dong_list = dong_list,
                    center_lat = data['위도'].mean(), 
                    center_lng = data['경도'].mean(),
                    titles = list(data['상호명'].values),
                    pos_data = zip(lats, lngs)
                    )

@application.route('/gmoney/search', methods=['GET','POST'])
def search():
    if request.method == 'POST':
        selected_dong = request.form.get('select')

        data = df[df['동']==selected_dong]
        lats = list(data['위도'].values)
        lngs = list(data['경도'].values)
        return render_template("gmoney.html", 
                    selected_dong = selected_dong,
                    dong_list = dong_list,
                    center_lat = data['위도'].mean(), 
                    center_lng = data['경도'].mean(),
                    titles = list(data['상호명'].values),
                    pos_data = zip(lats, lngs)
                    )

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=True)
