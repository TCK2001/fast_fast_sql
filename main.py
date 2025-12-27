import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(
    page_title="SQL 查詢工具", 
    page_icon="🔍", 
    layout="wide"
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
    h1 {
        color: #1f77b4;
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 標題
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

# 初始化 session state
if 'tables' not in st.session_state:
    st.session_state.tables = {}

# 檔案上傳
st.markdown("### 📁 檔案上傳")
uploaded_files = st.file_uploader(
    "選擇檔案 (.csv 或 .xlsx)",
    type=['csv', 'xlsx'],
    accept_multiple_files=True,
    help="可同時上傳多個檔案"
)

# 處理上傳的檔案
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_key = uploaded_file.name
        
        if file_key not in st.session_state.tables:
            try:
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                if file_extension == 'csv':
                    df = pd.read_csv(uploaded_file)
                elif file_extension == 'xlsx':
                    df = pd.read_excel(uploaded_file)
                
                default_table_name = uploaded_file.name.rsplit('.', 1)[0]
                
                st.session_state.tables[file_key] = {
                    'df': df,
                    'table_name': default_table_name,
                    'filename': uploaded_file.name
                }
                
            except Exception as e:
                st.error(f"❌ 讀取 {uploaded_file.name} 檔案時發生錯誤：\n{str(e)}")

# 顯示已上傳的檔案
if st.session_state.tables:
    st.markdown("---")
    st.markdown("### 📋 已上傳的檔案與表格設定")
    
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
            
            st.markdown("**📊 資料預覽（前 5 行）：**")
            st.dataframe(df.head(5), use_container_width=True, height=200)
            
            with st.expander("ℹ️ 欄位詳細資訊"):
                col_info = pd.DataFrame({
                    '欄位名稱': df.columns,
                    '資料型態': df.dtypes.values,
                    '缺失值數量': df.isnull().sum().values
                })
                st.dataframe(col_info, use_container_width=True)
    
    st.markdown("---")
    
    # SQL 查詢區
    st.markdown("### 🔍 SQL 查詢")
    
    table_names = [table_data['table_name'] for table_data in st.session_state.tables.values()]
    st.info(f"💡 **可用表格：** {' , '.join([f'`{name}`' for name in table_names])}")
    
    sql_query = st.text_area(
        "輸入您的 SQL 查詢：",
        height=180,
        placeholder=f"SELECT * FROM {table_names[0]} LIMIT 10" if table_names else "SELECT * FROM table_name LIMIT 10",
        help="支援標準 SQL 語法，包含 JOIN、GROUP BY、WHERE 等"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        run_button = st.button("▶️ 執行查詢", type="primary", use_container_width=True)
    
    if run_button:
        if sql_query.strip():
            with st.spinner('🔄 正在執行查詢...'):
                try:
                    conn = sqlite3.connect(':memory:')
                    
                    for table_data in st.session_state.tables.values():
                        df = table_data['df']
                        table_name = table_data['table_name']
                        df.to_sql(table_name, conn, index=False, if_exists='replace')
                    
                    result_df = pd.read_sql_query(sql_query, conn)
                    conn.close()
                    
                    st.success(f"✅ 查詢執行成功！共返回 **{len(result_df):,}** 行資料")
                    
                    if len(result_df) > 0:
                        st.markdown("#### 📊 查詢結果")
                        st.dataframe(result_df, use_container_width=True, height=400)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("結果行數", f"{len(result_df):,}")
                        with col2:
                            st.metric("結果欄位數", len(result_df.columns))
                        with col3:
                            st.metric("資料大小", f"{result_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
                        
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
            example_code = f"""-- 查詢所有資料
SELECT * FROM {table_names[0]};

-- 條件查詢
SELECT * FROM {table_names[0]} WHERE column_name > 100;

-- 分組與聚合
SELECT column_name, COUNT(*), AVG(value) 
FROM {table_names[0]} 
GROUP BY column_name;"""
        else:
            example_code = f"""-- 兩表 JOIN
SELECT a.*, b.column_name
FROM {table_names[0]} a
JOIN {table_names[1]} b ON a.id = b.id;

-- JOIN 與 GROUP BY 組合
SELECT a.category, COUNT(*) as count, AVG(b.value) as avg_value
FROM {table_names[0]} a
LEFT JOIN {table_names[1]} b ON a.id = b.id
GROUP BY a.category
ORDER BY count DESC;"""
        st.code(example_code, language="sql")

else:
    st.markdown("""
        <div style='text-align: center; padding: 3rem; background-color: #f8f9fa; border-radius: 15px; margin: 2rem 0;'>
            <h2 style='color: #6c757d;'>👆 開始使用</h2>
            <p style='font-size: 1.2rem; color: #6c757d;'>請上傳 CSV 或 Excel 檔案</p>
        </div>
        """, unsafe_allow_html=True)
    
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

# Oracle vs SQLite 語法比較
st.markdown("---")
with st.expander("📚 Oracle vs SQLite 語法比較參考", expanded=False):
    st.markdown("### 🔄 主要語法差異對照")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 日期", "🔢 字串", "📊 視窗函數", "🔀 其他", "💡 範例"])
    
    with tab1:
        st.markdown("#### 日期與時間函數")
        comparison_date = pd.DataFrame({
            '功能': ['當前日期', '日期格式化', '日期加減', '日期差異', '提取年月日', '月初/月末'],
            'Oracle': [
                'SYSDATE',
                "TO_CHAR(SYSDATE, 'YYYY-MM-DD')",
                'SYSDATE + 7',
                '日期1 - 日期2',
                'EXTRACT(YEAR FROM date)',
                "TRUNC(SYSDATE, 'MM')"
            ],
            'SQLite': [
                "DATE('now')",
                "STRFTIME('%Y-%m-%d', 'now')",
                "DATE('now', '+7 days')",
                'JULIANDAY(日期1) - JULIANDAY(日期2)',
                "STRFTIME('%Y', date)",
                "DATE('now', 'start of month')"
            ]
        })
        st.dataframe(comparison_date, use_container_width=True, hide_index=True)
        
        st.code("""-- Oracle: 最近 30 天
SELECT * FROM employees WHERE hire_date >= SYSDATE - 30;

-- SQLite: 最近 30 天  
SELECT * FROM employees WHERE hire_date >= DATE('now', '-30 days');""", language="sql")
    
    with tab2:
        st.markdown("#### 字串處理函數")
        comparison_string = pd.DataFrame({
            '功能': ['字串連接', '轉大/小寫', '子字串', '字串替換', 'NULL處理'],
            'Oracle': [
                "字串1 || 字串2",
                'UPPER() / LOWER()',
                'SUBSTR(字串, 起始, 長度)',
                'REPLACE(字串, 舊, 新)',
                'NVL(欄位, 預設值)'
            ],
            'SQLite': [
                "字串1 || 字串2",
                'UPPER() / LOWER()',
                'SUBSTR(字串, 起始, 長度)',
                'REPLACE(字串, 舊, 新)',
                'IFNULL(欄位, 預設值)'
            ]
        })
        st.dataframe(comparison_string, use_container_width=True, hide_index=True)
        
        st.code("""-- Oracle: NULL 處理
SELECT NVL(phone, '未提供') FROM employees;

-- SQLite: NULL 處理
SELECT IFNULL(phone, '未提供') FROM employees;""", language="sql")
    
    with tab3:
        st.markdown("#### 視窗函數（Window Functions）")
        comparison_window = pd.DataFrame({
            '功能': ['行號', '排名', '前/後一行', '累計總和', '分組'],
            'Oracle': [
                'ROW_NUMBER() OVER (...)',
                'RANK() / DENSE_RANK()',
                'LAG() / LEAD()',
                'SUM() OVER (ORDER BY ...)',
                'NTILE(n) OVER (...)'
            ],
            'SQLite': [
                'ROW_NUMBER() OVER (...)',
                'RANK() / DENSE_RANK()',
                'LAG() / LEAD()',
                'SUM() OVER (ORDER BY ...)',
                'NTILE(n) OVER (...)'
            ]
        })
        st.dataframe(comparison_window, use_container_width=True, hide_index=True)
        
        st.info("✅ 視窗函數在 Oracle 和 SQLite 中語法完全相同！")
        
        st.code("""-- 部門內薪資排名（Oracle & SQLite 相同）
SELECT 
    employee_name,
    department,
    salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rank
FROM employees;""", language="sql")
    
    with tab4:
        st.markdown("#### 其他常用函數")
        comparison_other = pd.DataFrame({
            '功能': ['條件判斷', '型別轉換', '四捨五入', '序列/自增', 'DECODE'],
            'Oracle': [
                'CASE WHEN ... END',
                'TO_CHAR() / TO_NUMBER()',
                'ROUND(數值, 位數)',
                '序列.NEXTVAL',
                'DECODE(欄位, 值1, 結果1, ...)'
            ],
            'SQLite': [
                'CASE WHEN ... END',
                'CAST(... AS TEXT/INTEGER)',
                'ROUND(數值, 位數)',
                'AUTOINCREMENT',
                '使用 CASE WHEN 替代'
            ]
        })
        st.dataframe(comparison_other, use_container_width=True, hide_index=True)
        
        st.code("""-- Oracle: DECODE
SELECT DECODE(dept, 'IT', '資訊部', 'HR', '人資部', '其他') FROM emp;

-- SQLite: CASE WHEN
SELECT CASE dept WHEN 'IT' THEN '資訊部' WHEN 'HR' THEN '人資部' ELSE '其他' END FROM emp;""", language="sql")
    
    with tab5:
        st.markdown("#### 💡 常見場景範例")
        
        st.markdown("**1️⃣ 分頁查詢**")
        st.code("""-- Oracle
SELECT * FROM (
    SELECT e.*, ROWNUM rn FROM employees e WHERE ROWNUM <= 20
) WHERE rn > 10;

-- SQLite
SELECT * FROM employees LIMIT 10 OFFSET 10;""", language="sql")
        
        st.markdown("**2️⃣ 取前 N 筆**")
        st.code("""-- Oracle
SELECT * FROM employees WHERE ROWNUM <= 5;

-- SQLite
SELECT * FROM employees LIMIT 5;""", language="sql")
        
        st.markdown("**3️⃣ 字串聚合**")
        st.code("""-- Oracle
SELECT dept, LISTAGG(name, ', ') WITHIN GROUP (ORDER BY name) FROM emp GROUP BY dept;

-- SQLite
SELECT dept, GROUP_CONCAT(name, ', ') FROM emp GROUP BY dept;""", language="sql")
        
        st.markdown("**4️⃣ DUAL 表**")
        st.code("""-- Oracle (需要 DUAL)
SELECT SYSDATE FROM DUAL;

-- SQLite (不需要)
SELECT DATE('now');""", language="sql")

# 頁尾
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #6c757d; padding: 1rem;'>
        <p>Made with ❤️ by TCK | 支援 SQLite 標準語法</p>
    </div>
    """, unsafe_allow_html=True)
