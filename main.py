import streamlit as st
import pandas as pd
import sqlite3
import io

st.set_page_config(
    page_title="SQL 查詢工具", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS 樣式
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    .stTextArea>div>div>textarea {
        border-radius: 10px;
    }
    h1 {
        color: #1f77b4;
        font-weight: bold;
        padding-bottom: 1rem;
    }
    h2 {
        color: #2c3e50;
        padding-top: 1rem;
    }
    h3 {
        color: #34495e;
    }
    .uploadedFile {
        border-radius: 10px;
        padding: 1rem;
        background-color: #f0f2f6;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 標題和描述
st.title("🔍 SQL 查詢工具")
st.markdown("""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; 
                border-radius: 15px; 
                color: white; 
                margin-bottom: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        <h3 style='color: white; margin: 0;'>📊 上傳 CSV 或 Excel 檔案，使用 SQL 查詢您的資料</h3>
        <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>支援多檔案上傳、自訂表格名稱、JOIN 查詢等進階功能</p>
    </div>
    """, unsafe_allow_html=True)

# 세션 상태 초기화
if 'tables' not in st.session_state:
    st.session_state.tables = {}

# 檔案上傳區塊
st.markdown("### 📁 檔案上傳")

uploaded_files = st.file_uploader(
    "選擇檔案 (.csv 或 .xlsx)",
    type=['csv', 'xlsx'],
    accept_multiple_files=True,
    help="可同時上傳多個檔案"
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
                st.error(f"❌ 讀取 {uploaded_file.name} 檔案時發生錯誤：\n{str(e)}")

# 上傳檔案顯示區
if st.session_state.tables:
    st.markdown("---")
    st.markdown("### 📋 已上傳的檔案與表格設定")
    
    # 每個檔案的表格名稱輸入
    for file_key, table_data in st.session_state.tables.items():
        with st.expander(f"📄 {table_data['filename']}", expanded=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                new_table_name = st.text_input(
                    "表格名稱：",
                    value=table_data['table_name'],
                    key=f"table_name_{file_key}",
                    help="此名稱將用於 SQL 查詢中"
                )
                st.session_state.tables[file_key]['table_name'] = new_table_name
            
            with col2:
                df = table_data['df']
                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("📊 總行數", f"{len(df):,}")
                with metric_col2:
                    st.metric("📋 總欄位數", len(df.columns))
            
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ 刪除", key=f"delete_{file_key}", type="secondary"):
                    del st.session_state.tables[file_key]
                    st.rerun()
            
            # 資料預覽
            st.markdown("**📊 資料預覽（前 5 行）：**")
            st.dataframe(df.head(5), use_container_width=True, height=200)
            
            # 欄位資訊
            with st.expander("ℹ️ 欄位詳細資訊"):
                col_info = pd.DataFrame({
                    '欄位名稱': df.columns,
                    '資料型態': df.dtypes.values,
                    '缺失值數量': df.isnull().sum().values
                })
                st.dataframe(col_info, use_container_width=True)
    
    st.markdown("---")
    
    # SQL 查詢輸入
    st.markdown("### 🔍 SQL 查詢")
    
    # 表格名稱列表顯示
    table_names = [table_data['table_name'] for table_data in st.session_state.tables.values()]
    st.info(f"💡 **可用表格：** {' , '.join([f'`{name}`' for name in table_names])}")
    
    sql_query = st.text_area(
        "輸入您的 SQL 查詢：",
        height=180,
        placeholder=f"SELECT * FROM {table_names[0]} LIMIT 10" if table_names else "SELECT * FROM table_name LIMIT 10",
        help="支援標準 SQL 語法，包含 JOIN、GROUP BY、WHERE 等"
    )
    
    # 執行按鈕
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        run_button = st.button("▶️ 執行查詢", type="primary", use_container_width=True)
    
    if run_button:
        if sql_query.strip():
            with st.spinner('🔄 正在執行查詢...'):
                try:
                    # 記憶體內 SQLite 資料庫
                    conn = sqlite3.connect(':memory:')
                    
                    # 將所有資料框存入 SQLite 表格
                    for table_data in st.session_state.tables.values():
                        df = table_data['df']
                        table_name = table_data['table_name']
                        df.to_sql(table_name, conn, index=False, if_exists='replace')
                    
                    # 執行 SQL 查詢
                    result_df = pd.read_sql_query(sql_query, conn)
                    
                    # 關閉連線
                    conn.close()
                    
                    # 顯示結果
                    st.success(f"✅ 查詢執行成功！共返回 **{len(result_df):,}** 行資料")
                    
                    if len(result_df) > 0:
                        st.markdown("#### 📊 查詢結果")
                        st.dataframe(result_df, use_container_width=True, height=400)
                        
                        # 結果統計
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("結果行數", f"{len(result_df):,}")
                        with col2:
                            st.metric("結果欄位數", len(result_df.columns))
                        with col3:
                            st.metric("資料大小", f"{result_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
                        
                        # CSV 下載按鈕
                        csv = result_df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 下載結果為 CSV",
                            data=csv,
                            file_name="query_result.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.warning("⚠️ 查詢結果為空")
                    
                except Exception as e:
                    st.error(f"❌ 查詢執行時發生錯誤：\n```\n{str(e)}\n```")
        else:
            st.warning("⚠️ 請輸入 SQL 查詢語句")
    
    # SQL 範例
    st.markdown("---")
    with st.expander("💡 SQL 查詢範例", expanded=False):
        if len(table_names) == 1:
            example_code = f"""
-- 查詢所有資料
SELECT * FROM {table_names[0]};

-- 查詢特定欄位
SELECT column1, column2 FROM {table_names[0]};

-- 條件查詢
SELECT * FROM {table_names[0]} WHERE column_name > 100;

-- 排序
SELECT * FROM {table_names[0]} ORDER BY column_name DESC;

-- 分組與聚合
SELECT column_name, COUNT(*), AVG(value) 
FROM {table_names[0]} 
GROUP BY column_name;

-- 限制返回行數
SELECT * FROM {table_names[0]} LIMIT 10;
            """
        else:
            example_code = f"""
-- 單表查詢
SELECT * FROM {table_names[0]};

-- 兩表 JOIN
SELECT a.*, b.column_name
FROM {table_names[0]} a
JOIN {table_names[1]} b ON a.id = b.id;

-- UNION (聯集)
SELECT column1 FROM {table_names[0]}
UNION
SELECT column1 FROM {table_names[1]};

-- 子查詢
SELECT * FROM {table_names[0]}
WHERE column_name IN (SELECT column_name FROM {table_names[1]});

-- JOIN 與 GROUP BY 組合
SELECT a.category, COUNT(*) as count, AVG(b.value) as avg_value
FROM {table_names[0]} a
LEFT JOIN {table_names[1]} b ON a.id = b.id
GROUP BY a.category
ORDER BY count DESC;
            """
        st.code(example_code, language="sql")

else:
    st.markdown("""
        <div style='text-align: center; padding: 3rem; background-color: #f8f9fa; border-radius: 15px; margin: 2rem 0;'>
            <h2 style='color: #6c757d;'>👆 開始使用</h2>
            <p style='font-size: 1.2rem; color: #6c757d;'>請上傳 CSV 或 Excel 檔案</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 使用說明
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📖 使用說明
        
        **步驟 1：** 上傳檔案  
        支援 CSV 和 Excel 格式，可同時上傳多個檔案
        
        **步驟 2：** 設定表格名稱  
        為每個上傳的檔案設定在 SQL 中使用的表格名稱
        
        **步驟 3：** 檢視資料  
        查看資料預覽和欄位資訊，確認資料正確載入
        """)
    
    with col2:
        st.markdown("""
        ### 🎯 功能特色
        
        **✨ 多檔案支援**  
        可同時處理多個資料檔案並進行關聯查詢
        
        **🔗 JOIN 查詢**  
        支援表格之間的 JOIN、UNION 等進階操作
        
        **📊 結果匯出**  
        查詢結果可直接下載為 CSV 檔案
        """)
    
    # 功能展示
    st.markdown("---")
    st.markdown("### 💻 支援的 SQL 功能")
    
    features_col1, features_col2, features_col3 = st.columns(3)
    
    with features_col1:
        st.markdown("""
        **基本查詢**
        - SELECT
        - WHERE
        - ORDER BY
        - LIMIT
        """)
    
    with features_col2:
        st.markdown("""
        **聚合函數**
        - COUNT()
        - SUM()
        - AVG()
        - GROUP BY
        """)
    
    with features_col3:
        st.markdown("""
        **進階操作**
        - JOIN (INNER/LEFT/RIGHT)
        - UNION
        - 子查詢
        - CASE WHEN
        """)

# 頁尾
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #6c757d; padding: 1rem;'>
        <p>Made with ❤️ using Streamlit | 支援 SQLite 標準語法</p>
    </div>
    """, unsafe_allow_html=True)
