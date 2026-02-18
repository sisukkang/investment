import streamlit as st
import FinanceDataReader as fdr
import pandas as pd  # pandas 임포트 위치를 상단으로 고정
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="한/미 국채 금리 대시보드", layout="wide")

st.title("📈 한/미 국채 금리 실시간 장기 추이")
st.markdown("데이터 소스에 접근할 수 없는 경우 일시적으로 차트가 표시되지 않을 수 있습니다.")

# 2. 데이터 로드 함수 (에러 핸들링 강화)
@st.cache_data(ttl=3600)
def get_data():
    today = datetime.now().strftime('%Y-%m-%d')
    start_date = '2000-01-01'  # 너무 먼 과거보다는 실질적 데이터가 있는 2000년부터 시작
    symbols = {
        '한국 3년': 'KR3YT=RR', 
        '한국 10년': 'KR10YT=RR',
        '미국 2년': 'US2YT=RR', 
        '미국 10년': 'US10YT=RR'
    }
    
    df_list = []
    for name, sym in symbols.items():
        try:
            # 개별 데이터 수집 시도
            df = fdr.DataReader(sym, start_date, today)['Close']
            if not df.empty:
                df.name = name
                df_list.append(df)
        except Exception as e:
            # 어떤 심볼에서 에러가 났는지 로그에 남김 (Manage app에서 확인 가능)
            print(f"Error fetching {name}: {e}")
            continue
    
    # [핵심 수정] 데이터가 하나도 없을 경우 빈 데이터프레임 반환하여 에러 방지
    if not df_list:
        return pd.DataFrame()
        
    return pd.concat(df_list, axis=1)

# 데이터 가져오기
data = get_data()

# 3. 데이터가 비어있는 경우 처리
if data.empty:
    st.error("⚠️ 데이터를 불러오지 못했습니다. 잠시 후 다시 시도하거나 데이터 소스 연결 상태를 확인해주세요.")
    st.info("Tip: Streamlit Cloud의 'Manage app' 메뉴에서 로그를 확인하면 상세한 원인을 알 수 있습니다.")
else:
    # 사이드바 - 기간 선택
    st.sidebar.header("설정")
    
    # 데이터의 실제 시작/종료 날짜 확인
    min_date = data.index.min().to_pydatetime()
    max_date = data.index.max().to_pydatetime()
    
    date_range = st.sidebar.date_input(
        "조회 기간 선택",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # 데이터 필터링 (선택된 날짜가 2개일 때만 실행)
    if len(date_range) == 2:
        filtered_data = data.loc[date_range[0]:date_range[1]]

        # 4. Plotly 차트 생성
        fig = go.Figure()

        # 컬럼 존재 여부 확인 후 그래프 추가
        colors = {'한국 3년': '#3498db', '한국 10년': '#2c3e50', '미국 2년': '#e74c3c', '미국 10년': '#8b0000'}
        
        for col in filtered_data.columns:
            line_style = dict(color=colors.get(col, '#000000'))
            if '10년' in col:
                line_style['dash'] = 'dash'
            
            fig.add_trace(go.Scatter(
                x=filtered_data.index, 
                y=filtered_data[col], 
                name=col, 
                line=line_style
            ))

        fig.update_layout(
            hovermode="x unified",
            template="plotly_white",
            xaxis_title="연도",
            yaxis_title="금리 (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # 데이터 표
        if st.checkbox('상세 데이터 보기'):
            st.write(filtered_data.tail(100))

st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
