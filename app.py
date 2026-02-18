import streamlit as st
import FinanceDataReader as fdr
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="한/미 국채 금리 모니터", layout="wide")

st.title("📈 한/미 국채 금리 실시간 대시보드")
st.markdown("데이터 소스 안정성을 위해 이원화 수집 방식을 사용합니다. (FDR & yfinance)")

# 2. 데이터 로드 함수
@st.cache_data(ttl=3600)
def fetch_bond_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*20) # 최근 20년 데이터
    
    df_final = pd.DataFrame()
    debug_info = []

    # --- (1) 미국 국채 수집 (yfinance 사용 - Streamlit에서 더 안정적) ---
    us_symbols = {'미국 10년': '^TNX', '미국 2년': '^IRX'} # ^IRX는 13주물이나 추세용으로 대체 가능
    for name, sym in us_symbols.items():
        try:
            ticker = yf.Ticker(sym)
            temp = ticker.history(start=start_date, end=end_date)['Close']
            if not temp.empty:
                # yfinance 금리는 10배로 나오는 경우가 있어 보정 (예: 4.5% -> 4.5)
                if name == '미국 10년': 
                    temp = temp # TNX는 그대로 사용
                df_final[name] = temp
                debug_info.append(f"✅ {name} 로드 완료 (yfinance)")
        except Exception as e:
            debug_info.append(f"❌ {name} 로드 실패: {e}")

    # --- (2) 한국 국채 수집 (FinanceDataReader 사용) ---
    kr_symbols = {'한국 3년': 'KR3YT=RR', '한국 10년': 'KR10YT=RR'}
    for name, sym in kr_symbols.items():
        try:
            temp = fdr.DataReader(sym, start_date.strftime('%Y-%m-%d'))['Close']
            if not temp.empty:
                df_final[name] = temp
                debug_info.append(f"✅ {name} 로드 완료 (FDR)")
        except Exception as e:
            debug_info.append(f"❌ {name} 로드 실패: {e}")

    return df_final.sort_index(), debug_info

# 데이터 실행
data, logs = fetch_bond_data()

# 3. 화면 구현
with st.sidebar:
    st.header("🛠️ 시스템 진단")
    for log in logs:
        st.write(log)
    
    if not data.empty:
        st.divider()
        st.header("📅 기간 필터")
        min_d, max_d = data.index.min().to_pydatetime(), data.index.max().to_pydatetime()
        selected_range = st.date_input("조회 범위", value=[min_d, max_d], min_value=min_d, max_value=max_d)

if data.empty:
    st.error("🚨 모든 데이터 소스에서 응답이 없습니다. 잠시 후 다시 시도해 주세요.")
    st.info("전문가 팁: Streamlit Cloud 설정에서 'Reboot App'을 눌러 세션을 초기화해 보세요.")
else:
    # 차트 시각화
    fig = go.Figure()
    colors = {'한국 3년': '#3498db', '한국 10년': '#2c3e50', '미국 2년': '#e74c3c', '미국 10년': '#8b0000'}
    
    for col in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index, y=data[col], name=col,
            line=dict(color=colors.get(col, 'gray'), dash='dash' if '10년' in col else 'solid')
        ))

    fig.update_layout(
        hovermode="x unified", height=600,
        xaxis_title="연도", yaxis_title="금리 (%)",
        legend=dict(orientation="h", y=1.05, x=1, xanchor="right")
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(data.tail(10), use_container_width=True)

st.caption(f"최종 업데이트 (UTC): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
