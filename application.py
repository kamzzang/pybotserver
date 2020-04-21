from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import sys
import sqlite3
application = Flask(__name__)

con = sqlite3.connect("./data/yongin_gmoney_store_giheung_suji.db")
df = pd.read_sql('select * from store', con=con)
con.close()

df['경도'] = df['경도'].astype(float)
df['위도'] = df['위도'].astype(float)

selected_gu='기흥구'
selected_dong='동백동'

dong_list = list(df[df['도로명주소'].str.contains(selected_gu)]['동'].unique())
data = df[df['동']== selected_dong]

lats = list(data['위도'].values)
lngs = list(data['경도'].values)

@application.route("/")
def hello():
    return render_template("index.html")

@application.route('/gmoney')
def gmoney():
    return render_template("gmoney.html", 
                        selected_gu = selected_gu,
                        selected_dong = selected_dong,
                        dong_list = dong_list,
                        center_lat = data['위도'].mean(), 
                        center_lng = data['경도'].mean(),
                        titles = list(data['상호명'].values),
                        pos_data = zip(lats, lngs)
                        )

@application.route('/naver')
def naver():
    return render_template("gmoneyNaver.html", 
                        selected_gu = selected_gu,
                        selected_dong = selected_dong,
                        dong_list = dong_list,
                        center_lat = data['위도'].mean(), 
                        center_lng = data['경도'].mean(),
                        titles = list(data['상호명'].values),
                        category = list(data['업종분류'].values),
                        pos_data = zip(lats, lngs)
                        )

@application.route('/naverex')
def naverex():
    return render_template("naverex.html"
                        )

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
        selected_gu = request.form.get('select_gu')
        selected_dong = request.form.get('select_dong')
        dong_list = list(df[df['도로명주소'].str.contains(selected_gu)]['동'].unique())
        data = df[(df['구']==selected_gu) & (df['동']==selected_dong)]

        lats = list(data['위도'].values)
        lngs = list(data['경도'].values)
        return render_template("gmoney.html", 
                    selected_gu = selected_gu,
                    selected_dong = selected_dong,
                    dong_list = dong_list,
                    center_lat = data['위도'].mean(), 
                    center_lng = data['경도'].mean(),
                    titles = list(data['상호명'].values),
                    category = list(data['업종분류'].values),
                    pos_data = zip(lats, lngs)
                    )

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=True)
