import streamlit as st
import FinanceDataReader as fdr
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 설정 (웹 브라우저 탭 이름)
st.set_page_config(page_title="한/미 국채 금리 대시보드", layout="wide")

st.title("📈 한/미 국채 금리 실시간 장기 추이")
st.markdown("이 페이지는 깃허브 코드를 통해 자동으로 업데이트되는 실시간 국채 금리 대시보드입니다.")

# 2. 데이터 로드 (캐싱 처리하여 속도 최적화)
@st.cache_data(ttl=3600) # 1시간마다 데이터 갱신
def get_data():
    today = datetime.now().strftime('%Y-%m-%d')
    start_date = '1990-01-01'
    symbols = {
        '한국 3년': 'KR3YT=RR', '한국 10년': 'KR10YT=RR',
        '미국 2년': 'US2YT=RR', '미국 10년': 'US10YT=RR'
    }
    df_list = []
    for name, sym in symbols.items():
        try:
            df = fdr.DataReader(sym, start_date, today)['Close']
            df.name = name
            df_list.append(df)
        except: pass
    return pd.concat(df_list, axis=1)

import pandas as pd
data = get_data()

# 3. 사이드바 - 기간 선택 기능
st.sidebar.header("설정")
date_range = st.sidebar.date_input(
    "조회 기간 선택",
    value=[data.index[0], data.index[-1]],
    min_value=data.index[0],
    max_value=data.index[-1]
)

# 선택된 기간으로 데이터 필터링
filtered_data = data.loc[date_range[0]:date_range[1]]

# 4. Plotly를 이용한 인터랙티브 차트 (홈페이지용)
fig = go.Figure()

# 한국 데이터
fig.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['한국 3년'], name="KR 3Y", line=dict(color='#3498db')))
fig.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['한국 10년'], name="KR 10Y", line=dict(color='#2c3e50', dash='dash')))

# 미국 데이터
fig.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['미국 2년'], name="US 2Y", line=dict(color='#e74c3c')))
fig.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['미국 10년'], name="US 10Y", line=dict(color='#8b0000', dash='dash')))

fig.update_layout(
    hovermode="x unified",
    template="plotly_white",
    xaxis_title="연도",
    yaxis_title="금리 (%)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# 5. 웹 화면에 출력
st.plotly_chart(fig, use_container_width=True)

# 데이터 표 보여주기
if st.checkbox('상세 데이터 보기'):
    st.write(filtered_data.tail(100))

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
