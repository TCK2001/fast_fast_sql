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

# Oracle vs SQLite 語法比較
with st.expander("📚 Oracle vs SQLite 語法比較", expanded=False):
    st.markdown("### 🔄 主要語法差異對照表")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 日期函數", "🔢 字串函數", "📊 分析函數", "🔀 其他函數", "💡 常見範例"])
    
    with tab1:
        st.markdown("#### 日期與時間函數")
        
        comparison_date = pd.DataFrame({
            '功能': [
                '當前日期',
                '當前日期時間',
                '日期格式化',
                '日期加減',
                '日期差異（天）',
                '提取年份',
                '提取月份',
                '提取日',
                '月初',
                '月末',
                '季度',
                '星期幾'
            ],
            'Oracle': [
                'SYSDATE',
                'SYSTIMESTAMP',
                "TO_CHAR(SYSDATE, 'YYYY-MM-DD')",
                "SYSDATE + 7 或 ADD_MONTHS(SYSDATE, 1)",
                "日期1 - 日期2",
                "EXTRACT(YEAR FROM SYSDATE)",
                "EXTRACT(MONTH FROM SYSDATE)",
                "EXTRACT(DAY FROM SYSDATE)",
                "TRUNC(SYSDATE, 'MM')",
                "LAST_DAY(SYSDATE)",
                "TO_CHAR(SYSDATE, 'Q')",
                "TO_CHAR(SYSDATE, 'D')"
            ],
            'SQLite': [
                "DATE('now')",
                "DATETIME('now')",
                "STRFTIME('%Y-%m-%d', 'now')",
                "DATE('now', '+7 days') 或 DATE('now', '+1 month')",
                "JULIANDAY(日期1) - JULIANDAY(日期2)",
                "STRFTIME('%Y', 'now')",
                "STRFTIME('%m', 'now')",
                "STRFTIME('%d', 'now')",
                "DATE('now', 'start of month')",
                "DATE('now', 'start of month', '+1 month', '-1 day')",
                "CAST((STRFTIME('%m', 'now') + 2) / 3 AS INTEGER)",
                "STRFTIME('%w', 'now')"
            ]
        })
        st.dataframe(comparison_date, use_container_width=True)
        
        st.markdown("##### 📝 實際範例：")
        st.code("""
-- Oracle: 查詢最近 30 天的資料
SELECT * FROM employees 
WHERE hire_date >= SYSDATE - 30;

-- SQLite: 查詢最近 30 天的資料
SELECT * FROM employees 
WHERE hire_date >= DATE('now', '-30 days');

-- Oracle: 計算在職天數
SELECT employee_name, SYSDATE - hire_date AS days_employed
FROM employees;

-- SQLite: 計算在職天數
SELECT employee_name, JULIANDAY('now') - JULIANDAY(hire_date) AS days_employed
FROM employees;
        """, language="sql")
    
    with tab2:
        st.markdown("#### 字串處理函數")
        
        comparison_string = pd.DataFrame({
            '功能': [
                '字串連接',
                '轉大寫',
                '轉小寫',
                '字串長度',
                '去除空格',
                '子字串',
                '字串替換',
                '搜尋位置',
                '左側截取',
                '右側截取',
                '填充',
                'NULL 處理'
            ],
            'Oracle': [
                "字串1 || 字串2 或 CONCAT()",
                "UPPER(字串)",
                "LOWER(字串)",
                "LENGTH(字串)",
                "TRIM(字串)",
                "SUBSTR(字串, 起始, 長度)",
                "REPLACE(字串, 舊值, 新值)",
                "INSTR(字串, 搜尋值)",
                "SUBSTR(字串, 1, n)",
                "SUBSTR(字串, -n)",
                "LPAD(字串, 長度, 填充字元)",
                "NVL(欄位, 預設值)"
            ],
            'SQLite': [
                "字串1 || 字串2",
                "UPPER(字串)",
                "LOWER(字串)",
                "LENGTH(字串)",
                "TRIM(字串)",
                "SUBSTR(字串, 起始, 長度)",
                "REPLACE(字串, 舊值, 新值)",
                "INSTR(字串, 搜尋值)",
                "SUBSTR(字串, 1, n)",
                "SUBSTR(字串, -n)",
                "PRINTF('%0' || 長度 || 'd', 數字)",
                "IFNULL(欄位, 預設值) 或 COALESCE()"
            ]
        })
        st.dataframe(comparison_string, use_container_width=True)
        
        st.markdown("##### 📝 實際範例：")
        st.code("""
-- Oracle: 字串連接
SELECT employee_name || ' - ' || department AS full_info FROM employees;

-- SQLite: 字串連接（相同）
SELECT employee_name || ' - ' || department AS full_info FROM employees;

-- Oracle: NULL 處理
SELECT NVL(phone, '未提供') AS phone FROM employees;

-- SQLite: NULL 處理
SELECT IFNULL(phone, '未提供') AS phone FROM employees;
        """, language="sql")
    
    with tab3:
        st.markdown("#### 分析函數（視窗函數）")
        
        comparison_analytic = pd.DataFrame({
            '功能': [
                '行號',
                '排名',
                '密集排名',
                '百分位排名',
                '前一行',
                '後一行',
                '第一個值',
                '最後一個值',
                '累計總和',
                '移動平均',
                '分組',
                '中位數'
            ],
            'Oracle': [
                "ROW_NUMBER() OVER (...)",
                "RANK() OVER (...)",
                "DENSE_RANK() OVER (...)",
                "PERCENT_RANK() OVER (...)",
                "LAG(欄位, n) OVER (...)",
                "LEAD(欄位, n) OVER (...)",
                "FIRST_VALUE(欄位) OVER (...)",
                "LAST_VALUE(欄位) OVER (...)",
                "SUM(欄位) OVER (ORDER BY ...)",
                "AVG(欄位) OVER (ROWS BETWEEN n PRECEDING AND CURRENT ROW)",
                "NTILE(n) OVER (...)",
                "MEDIAN(欄位)"
            ],
            'SQLite': [
                "ROW_NUMBER() OVER (...)",
                "RANK() OVER (...)",
                "DENSE_RANK() OVER (...)",
                "PERCENT_RANK() OVER (...)",
                "LAG(欄位, n) OVER (...)",
                "LEAD(欄位, n) OVER (...)",
                "FIRST_VALUE(欄位) OVER (...)",
                "LAST_VALUE(欄位) OVER (...)",
                "SUM(欄位) OVER (ORDER BY ...)",
                "AVG(欄位) OVER (ROWS BETWEEN n PRECEDING AND CURRENT ROW)",
                "NTILE(n) OVER (...)",
                "使用 PERCENTILE_CONT() 或自定義"
            ]
        })
        st.dataframe(comparison_analytic, use_container_width=True)
        
        st.markdown("##### 📝 實際範例：")
        st.code("""
-- Oracle & SQLite: 部門內薪資排名（語法相同！）
SELECT 
    employee_name,
    department,
    salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) as dept_rank
FROM employees;

-- Oracle & SQLite: 累計總和（語法相同！）
SELECT 
    date,
    amount,
    SUM(amount) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total
FROM transactions;
        """, language="sql")
    
    with tab4:
        st.markdown("#### 其他常用函數")
        
        comparison_other = pd.DataFrame({
            '功能': [
                '條件判斷',
                '空值判斷',
                '數值轉字串',
                '字串轉數值',
                '四捨五入',
                '無條件進位',
                '無條件捨去',
                '絕對值',
                '隨機數',
                '序列/自增',
                'DECODE',
                '正則表達式'
            ],
            'Oracle': [
                "CASE WHEN ... THEN ... END",
                "NVL(欄位, 預設值)",
                "TO_CHAR(數值)",
                "TO_NUMBER(字串)",
                "ROUND(數值, 小數位)",
                "CEIL(數值)",
                "FLOOR(數值)",
                "ABS(數值)",
                "DBMS_RANDOM.VALUE",
                "序列.NEXTVAL",
                "DECODE(欄位, 值1, 結果1, ...)",
                "REGEXP_LIKE(), REGEXP_REPLACE()"
            ],
            'SQLite': [
                "CASE WHEN ... THEN ... END",
                "IFNULL(欄位, 預設值)",
                "CAST(數值 AS TEXT)",
                "CAST(字串 AS INTEGER/REAL)",
                "ROUND(數值, 小數位)",
                "使用 CAST 和運算",
                "CAST(數值 AS INTEGER)",
                "ABS(數值)",
                "RANDOM() / 18446744073709551616.0",
                "AUTOINCREMENT",
                "CASE WHEN ... THEN ... END",
                "不直接支援（需使用 LIKE）"
            ]
        })
        st.dataframe(comparison_other, use_container_width=True)
        
        st.markdown("##### 📝 實際範例：")
        st.code("""
-- Oracle: DECODE 函數
SELECT employee_name, 
       DECODE(department, 'IT', '資訊部', 'HR', '人資部', '其他') as dept_name
FROM employees;

-- SQLite: 使用 CASE WHEN 替代
SELECT employee_name,
       CASE department
           WHEN 'IT' THEN '資訊部'
           WHEN 'HR' THEN '人資部'
           ELSE '其他'
       END as dept_name
FROM employees;

-- Oracle: 序列
SELECT employee_seq.NEXTVAL FROM DUAL;

-- SQLite: 自增欄位
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
);
        """, language="sql")
    
    with tab5:
        st.markdown("#### 💡 常見場景轉換範例")
        
        st.markdown("##### 1️⃣ 分頁查詢")
        st.code("""
-- Oracle: 使用 ROWNUM 或 OFFSET-FETCH
SELECT * FROM (
    SELECT e.*, ROWNUM rn FROM employees e WHERE ROWNUM <= 20
) WHERE rn > 10;

-- 或 Oracle 12c+
SELECT * FROM employees 
ORDER BY employee_id 
OFFSET 10 ROWS FETCH NEXT 10 ROWS ONLY;

-- SQLite: 使用 LIMIT OFFSET
SELECT * FROM employees 
ORDER BY employee_id 
LIMIT 10 OFFSET 10;
        """, language="sql")
        
        st.markdown("##### 2️⃣ 取前 N 筆")
        st.code("""
-- Oracle: 使用 ROWNUM 或 FETCH FIRST
SELECT * FROM employees WHERE ROWNUM <= 5;

-- 或 Oracle 12c+
SELECT * FROM employees FETCH FIRST 5 ROWS ONLY;

-- SQLite: 使用 LIMIT
SELECT * FROM employees LIMIT 5;
        """, language="sql")
        
        st.markdown("##### 3️⃣ 日期範圍查詢")
        st.code("""
-- Oracle: 最近一個月
SELECT * FROM orders
WHERE order_date >= ADD_MONTHS(SYSDATE, -1);

-- SQLite: 最近一個月
SELECT * FROM orders
WHERE order_date >= DATE('now', '-1 month');
        """, language="sql")
        
        st.markdown("##### 4️⃣ 字串聚合")
        st.code("""
-- Oracle: 使用 LISTAGG
SELECT department,
       LISTAGG(employee_name, ', ') WITHIN GROUP (ORDER BY employee_name) as employees
FROM employees
GROUP BY department;

-- SQLite: 使用 GROUP_CONCAT
SELECT department,
       GROUP_CONCAT(employee_name, ', ') as employees
FROM employees
GROUP BY department;
        """, language="sql")
        
        st.markdown("##### 5️⃣ DUAL 表")
        st.code("""
-- Oracle: 使用 DUAL 執行計算
SELECT SYSDATE FROM DUAL;
SELECT 1 + 1 FROM DUAL;

-- SQLite: 不需要 DUAL（直接 SELECT）
SELECT DATE('now');
SELECT 1 + 1;
        """, language="sql")

st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #6c757d; padding: 1rem;'>
        <p>Made with ❤️ using Streamlit | 支援 SQLite 標準語法</p>
    </div>
    """, unsafe_allow_html=True)
