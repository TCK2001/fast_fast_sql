import streamlit as st
import pandas as pd
import sqlite3
import io

st.set_page_config(page_title="SQL Query Tool", page_icon="🔍", layout="wide")

st.title("📊 SQL Query Tool")
st.markdown("CSV 또는 Excel 파일을 업로드하고 SQL 쿼리를 실행하세요!")

# 세션 상태 초기화
if 'tables' not in st.session_state:
    st.session_state.tables = {}

# 파일 업로드 섹션
st.subheader("📁 파일 업로드")

col1, col2 = st.columns([3, 1])

with col1:
    uploaded_files = st.file_uploader(
        "파일을 업로드하세요 (.csv 또는 .xlsx)", 
        type=['csv', 'xlsx'],
        accept_multiple_files=True
    )

# 업로드된 파일 처리
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_key = uploaded_file.name
        
        # 이미 처리된 파일이 아니면 처리
        if file_key not in st.session_state.tables:
            try:
                # 파일 확장자 확인
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                # 파일 읽기
                if file_extension == 'csv':
                    df = pd.read_csv(uploaded_file)
                elif file_extension == 'xlsx':
                    df = pd.read_excel(uploaded_file)
                
                # 기본 테이블 이름 (파일명에서 확장자 제거)
                default_table_name = uploaded_file.name.rsplit('.', 1)[0]
                
                st.session_state.tables[file_key] = {
                    'df': df,
                    'table_name': default_table_name,
                    'filename': uploaded_file.name
                }
                
            except Exception as e:
                st.error(f"❌ {uploaded_file.name} 파일을 읽는 중 오류가 발생했습니다:\n{str(e)}")

# 업로드된 파일이 있을 때만 표시
if st.session_state.tables:
    st.markdown("---")
    st.subheader("📋 업로드된 파일 및 테이블 이름 설정")
    
    # 각 파일에 대한 테이블 이름 입력
    for file_key, table_data in st.session_state.tables.items():
        with st.expander(f"📄 {table_data['filename']}", expanded=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                new_table_name = st.text_input(
                    "테이블 이름:",
                    value=table_data['table_name'],
                    key=f"table_name_{file_key}"
                )
                st.session_state.tables[file_key]['table_name'] = new_table_name
            
            with col2:
                df = table_data['df']
                st.metric("행 수", len(df))
                st.metric("열 수", len(df.columns))
            
            with col3:
                if st.button("🗑️ 삭제", key=f"delete_{file_key}"):
                    del st.session_state.tables[file_key]
                    st.rerun()
            
            # 데이터 미리보기
            st.markdown("**데이터 미리보기 (처음 5행):**")
            st.dataframe(df.head(5), use_container_width=True)
            
            # 컬럼 정보
            with st.expander("ℹ️ 컬럼 정보"):
                col_info = pd.DataFrame({
                    '컬럼명': df.columns,
                    '데이터 타입': df.dtypes.values,
                    '결측치 개수': df.isnull().sum().values
                })
                st.dataframe(col_info, use_container_width=True)
    
    st.markdown("---")
    
    # SQL 쿼리 입력
    st.subheader("🔍 SQL 쿼리 입력")
    
    # 테이블 이름 목록 표시
    table_names = [table_data['table_name'] for table_data in st.session_state.tables.values()]
    st.info(f"💡 사용 가능한 테이블: {', '.join([f'`{name}`' for name in table_names])}")
    
    sql_query = st.text_area(
        "SQL 쿼리를 입력하세요:",
        height=150,
        placeholder=f"SELECT * FROM {table_names[0]} LIMIT 10" if table_names else "SELECT * FROM table_name LIMIT 10"
    )
    
    # 실행 버튼
    if st.button("▶️ 쿼리 실행", type="primary"):
        if sql_query.strip():
            try:
                # 메모리 내 SQLite 데이터베이스 생성
                conn = sqlite3.connect(':memory:')
                
                # 모든 데이터프레임을 SQLite 테이블로 저장
                for table_data in st.session_state.tables.values():
                    df = table_data['df']
                    table_name = table_data['table_name']
                    df.to_sql(table_name, conn, index=False, if_exists='replace')
                
                # SQL 쿼리 실행
                result_df = pd.read_sql_query(sql_query, conn)
                
                # 연결 종료
                conn.close()
                
                # 결과 표시
                st.success(f"✅ 쿼리가 성공적으로 실행되었습니다! (결과 행 수: {len(result_df)})")
                
                if len(result_df) > 0:
                    st.dataframe(result_df, use_container_width=True)
                    
                    # CSV 다운로드 버튼
                    csv = result_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 결과를 CSV로 다운로드",
                        data=csv,
                        file_name="query_result.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("쿼리 결과가 비어있습니다.")
                
            except Exception as e:
                st.error(f"❌ 쿼리 실행 중 오류가 발생했습니다:\n{str(e)}")
        else:
            st.warning("SQL 쿼리를 입력해주세요.")
    
    # SQL 예제
    st.markdown("---")
    with st.expander("💡 SQL 쿼리 예제"):
        if len(table_names) == 1:
            example_code = f"""
-- 모든 데이터 조회
SELECT * FROM {table_names[0]};

-- 특정 컬럼만 조회
SELECT column1, column2 FROM {table_names[0]};

-- 조건부 조회
SELECT * FROM {table_names[0]} WHERE column_name > 100;

-- 정렬
SELECT * FROM {table_names[0]} ORDER BY column_name DESC;

-- 그룹화 및 집계
SELECT column_name, COUNT(*), AVG(value) 
FROM {table_names[0]} 
GROUP BY column_name;

-- 상위 10개 행
SELECT * FROM {table_names[0]} LIMIT 10;
            """
        else:
            example_code = f"""
-- 단일 테이블 조회
SELECT * FROM {table_names[0]};

-- 두 테이블 JOIN
SELECT a.*, b.column_name
FROM {table_names[0]} a
JOIN {table_names[1]} b ON a.id = b.id;

-- UNION (합집합)
SELECT column1 FROM {table_names[0]}
UNION
SELECT column1 FROM {table_names[1]};

-- 서브쿼리
SELECT * FROM {table_names[0]}
WHERE column_name IN (SELECT column_name FROM {table_names[1]});
            """
        st.code(example_code, language="sql")

else:
    st.info("👆 파일을 업로드하여 시작하세요!")
    
    # 사용 안내
    st.markdown("### 📖 사용 방법")
    st.markdown("""
    1. CSV 또는 Excel 파일을 업로드합니다 (여러 파일 가능)
    2. 각 파일의 테이블 이름을 설정합니다
    3. 데이터 미리보기와 컬럼 정보를 확인합니다
    4. SQL 쿼리를 입력합니다 (여러 테이블 JOIN 가능)
    5. '쿼리 실행' 버튼을 클릭합니다
    6. 결과를 확인하고 필요시 CSV로 다운로드합니다
    """)

# 푸터
st.markdown("---")
st.markdown("*Made with Streamlit* 🎈")