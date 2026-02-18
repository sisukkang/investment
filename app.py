import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="한/미 국채 금리 모니터링", layout="wide")

st.title("📈 한/미 국채 금리 실시간 대시보드")
st.markdown("데이터 소스 최적화 완료: 한국(Investing) / 미국(FRED - 연준 공식 데이터)")

# 2. 데이터 수집 함수 (안정성 강화)
@st.cache_data(ttl=3600)
def fetch_bond_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*20) # 최근 20년 데이터
    
    df_final = pd.DataFrame()
    debug_info = []

    # --- (1) 한국 국채 수집 (Investing 소스 강제 지정) ---
    kr_symbols = {'한국 3년': 'KR3YT=RR', '한국 10년': 'KR10YT=RR'}
    for name, sym in kr_symbols.items():
        try:
            # data_source='investing'을 명시하여 야후 파이낸스 404 에러를 방지합니다.
            temp = fdr.DataReader(sym, start_date.strftime('%Y-%m-%d'), data_source='investing')['Close']
            if not temp.empty:
                df_final[name] = temp
                debug_info.append(f"✅ {name} 로드 완료 (Investing)")
        except Exception as e:
            debug_info.append(f"❌ {name} 로드 실패: {e}")

    # --- (2) 미국 국채 수집 (FRED - 연준 데이터 사용으로 안정성 극대화) ---
    us_symbols = {'미국 2년': 'DGS2', '미국 10년': 'DGS10'}
    for name, sym in us_symbols.items():
        try:
            # FRED 데이터를 직접 호출합니다.
            temp = fdr.DataReader(sym, start_date.strftime('%Y-%m-%d'), data_source='fred')
            if not temp.empty:
                df_final[name] = temp.iloc[:, 0] # 첫 번째 열(금리)만 선택
                debug_info.append(f"✅ {name} 로드 완료 (FRED)")
        except Exception as e:
            debug_info.append(f"❌ {name} 로드 실패: {e}")

    return df_final.sort_index(), debug_info

# 데이터 실행
data, logs = fetch_bond_data()

# 3. 사이드바 진단 및 설정
with st.sidebar:
    st.header("🛠️ 시스템 진단 로그")
    for log in logs:
        st.write(log)
    
    if not data.empty:
        st.divider()
        st.header("📅 조회 기간 설정")
        min_d, max_d = data.index.min().to_pydatetime(), data.index.max().to_pydatetime()
        selected_range = st.date_input("조회 범위", value=[min_d, max_d], min_value=min_d, max_value=max_d)

# 4. 차트 출력
if data.empty:
    st.error("🚨 데이터를 불러오지 못했습니다. 잠시 후 'Reboot App'을 실행해 주세요.")
else:
    if len(selected_range) == 2:
        filtered_data = data.loc[selected_range[0]:selected_range[1]]
        
        fig = go.Figure()
        colors = {'한국 3년': '#3498db', '한국 10년': '#2c3e50', '미국 2년': '#e74c3c', '미국 10년': '#8b0000'}
        
        for col in filtered_data.columns:
            is_long = '10년' in col
            fig.add_trace(go.Scatter(
                x=filtered_data.index, y=filtered_data[col], name=col,
                line=dict(color=colors.get(col, 'gray'), width=2, dash='dash' if is_long else 'solid')
            ))

        fig.update_layout(
            hovermode="x unified", height=650, template="plotly_white",
            xaxis_title="연도", yaxis_title="금리 (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

st.caption(f"최종 업데이트 (KST): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
