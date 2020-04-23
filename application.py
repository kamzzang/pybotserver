from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import sys
import sqlite3
application = Flask(__name__)

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

@application.route("/")
def hello():
    return render_template("index.html")

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


@application.route('/ex')
def ex():
    return render_template("gmoney_ex.html", 
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

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=True)
