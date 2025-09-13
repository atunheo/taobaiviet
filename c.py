import streamlit as st
import pandas as pd
import os
import re
import tempfile
import zipfile
import random
import html

# Danh sách link để random
links_pool = [
    "181.run", "182.run", "183.run",
    "za51.run", "za52.run", "za53.run",
    "uu1.run", "uu2.run", "uu3.run"
]

# Patterns để remove
REMOVE_PATTERNS = ["181.run", "182.run", "183.run"]
MD_LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+|[^\)]+)\)')

def clean_text(text: str) -> str:
    """Loại bỏ dấu # ở đầu dòng và làm sạch text"""
    if not text:
        return ""
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        # Loại bỏ dấu # ở đầu dòng
        cleaned_line = re.sub(r"^#+\s*", "", line.strip())
        cleaned_lines.append(cleaned_line)
    return "\n".join(cleaned_lines)

def md_links_to_html(s: str) -> str:
    """Chuyển markdown link [text](url) thành <a>"""
    def repl(m):
        text = html.escape(m.group(1))
        url = html.escape(m.group(2))
        return f'<a href="{url}" target="_blank">{text}</a>'
    return MD_LINK_RE.sub(repl, s)

def extract_url_from_html(s: str) -> str:
    """Lấy URL từ nội dung HTML đã convert của cột A"""
    match = re.search(r'href="([^"]+)"', s)
    if match:
        return match.group(1)
    return "https://182.run"  # fallback nếu không tìm thấy link

def convert_cell_to_html(cell: object, is_colA: bool=False) -> str:
    """Convert nội dung cell thành HTML"""
    if pd.isna(cell):
        return ""

    s = str(cell).replace('\r\n', '\n').replace('\r', '\n')
    lines = [ln.rstrip() for ln in s.split('\n')]
    lines = [ln for ln in lines if not any(p in ln for p in REMOVE_PATTERNS)]

    html_parts, list_items, in_list = [], [], False

    for ln in lines:
        stripped = ln.strip()
        if stripped == "":
            if in_list and list_items:
                html_parts.append("<ul>")
                for it in list_items:
                    html_parts.append(f"  <li>{it}</li>")
                html_parts.append("</ul>")
                list_items, in_list = [], False
            html_parts.append("<p></p>")
            continue

        if re.match(r'^[-\*\u2022]\s+', stripped):
            item = re.sub(r'^[-\*\u2022]\s+', '', stripped)
            item = md_links_to_html(item)
            if '<a ' not in item:
                item = html.escape(item)
            list_items.append(item)
            in_list = True
            continue

        if in_list and list_items:
            html_parts.append("<ul>")
            for it in list_items:
                html_parts.append(f"  <li>{it}</li>")
            html_parts.append("</ul>")
            list_items, in_list = [], False

        line_with_links = md_links_to_html(stripped)

        # Nếu là cột A và có 【链接地址：】 thì chèn thẻ <a> với text = URL
        if is_colA and "【链接地址：】" in stripped:
            match = re.search(r"【链接地址：】\s*(\S+)", stripped)
            if match:
                url = match.group(1).strip()
                anchor = f"<a href=\"{url}\" target=\"_blank\" style=\"font-size:25px\">{url}</a>"
                line_with_links = f"【链接地址：】{anchor}"

        if '<a ' in line_with_links:
            html_parts.append(f"<p>{line_with_links}</p>")
        else:
            html_parts.append(f"<p>{html.escape(line_with_links)}</p>")

    if in_list and list_items:
        html_parts.append("<ul>")
        for it in list_items:
            html_parts.append(f"  <li>{it}</li>")
        html_parts.append("</ul>")

    fragment = "\n".join(html_parts)
    return fragment

def create_column_A_content(original_text: str) -> str:
    """Tạo nội dung cột A theo logic từ htmls.py"""
    # Random 1 link
    link = random.choice(links_pool)
    anchor = f"【链接地址：<a href='https://{link}' target='_blank'>{link}</a>】"
    
    # Xử lý text gốc
    clean_text = re.sub(r"【链接地址：.*?】", "", original_text).strip()
    
    # Tìm dấu '-' thứ 2 và chèn anchor trước đó
    parts = clean_text.split(" - ", 2)
    if len(parts) >= 3:
        clean_text_with_anchor = f"{parts[0]} - {parts[1]} {anchor} - {parts[2]}"
    else:
        clean_text_with_anchor = f"{clean_text} {anchor}"
    
    # Wrap trong div với style
    return f"<div style='font-size:25px;color:pink'>{clean_text_with_anchor}</div>"

def export_repos_to_excel(base_dir, output_path):
    """Xuất repos từ zip thành Excel với 2 cột"""
    data = []
    for repo_dir in os.listdir(base_dir):
        repo_path = os.path.join(base_dir, repo_dir)
        if not os.path.isdir(repo_path):
            continue

        readme_path = os.path.join(repo_path, "README.md")
        if not os.path.exists(readme_path):
            continue

        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        lines = content.splitlines()
        title = lines[0].strip() if lines else ""
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        
        # Làm sạch tiêu đề và nội dung, loại bỏ dấu #
        cleaned_title = clean_text(title)
        cleaned_body = clean_text(body)

        data.append({
            "Tiêu đề": cleaned_title,
            "Nội dung": cleaned_body
        })

    df = pd.DataFrame(data, columns=["Tiêu đề", "Nội dung"])
    df.to_excel(output_path, index=False)
    return df

def process_excel_with_html(df):
    """Xử lý DataFrame để thêm HTML tags và random links"""
    if df.shape[1] < 2:
        st.error("File cần ít nhất 2 cột (A và B).")
        return None

    colA = df.columns[0]
    colB = df.columns[1]

    new_a_values = []
    new_b_values = []

    for idx, row in df.iterrows():
        # Random 1 link cho cả A & B
        link = random.choice(links_pool)
        
        # === CỘT A - Sử dụng logic từ htmls.py ===
        original_text = str(row[colA]) if pd.notnull(row[colA]) else ""
        new_a = create_column_A_content(original_text)
        new_a_values.append(new_a)

        # === CỘT B - Giữ nguyên nội dung gốc, chỉ thêm HTML tags ===
        # Convert cột B, thay thế <p></p><p></p> bằng link động từ A
        def convert_B(row):
            url = extract_url_from_html(row[colA])
            anchor_dynamic = f"<p> <a href='{url}' target='_blank' style='font-size:30px; color:pink'>永久地址</a></p>"
            html_B = convert_cell_to_html(row[colB], is_colA=False)
            # thay thế đúng vị trí <p></p><p></p>
            html_B = re.sub(r"<p></p>\s*<p></p>", anchor_dynamic, html_B, count=1)
            return html_B

        new_b = convert_B(row)
        new_b_values.append(new_b)

    # Cập nhật DataFrame
    df[colA] = new_a_values
    df[colB] = new_b_values
    
    return df

# -------------------- Streamlit UI --------------------

st.title("📂 Script Hoàn Chỉnh - Xử lý Zip + HTML")

# Tab 1: Xử lý file Zip
tab1, tab2 = st.tabs(["📁 Xử lý File Zip", "📊 Xử lý File Excel"])

with tab1:
    st.header("Bước 1: Upload file .zip")
    uploaded_zip = st.file_uploader("Chọn file .zip chứa các thư mục với README.md", type=["zip"])
    
    if uploaded_zip is not None:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "repos.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getbuffer())

            # Giải nén
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmpdir)

            # Xuất Excel
            excel_path = os.path.join(tmpdir, "repocuoicung.xlsx")
            df = export_repos_to_excel(tmpdir, excel_path)
            
            st.success("✅ Đã tạo Excel từ file zip!")
            st.dataframe(df.head())
            
            # Download file Excel
            with open(excel_path, "rb") as f:
                st.download_button(
                    label="📥 Tải file Excel",
                    data=f,
                    file_name="repocuoicung.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

with tab2:
    st.header("Bước 2: Xử lý file Excel với HTML")
    uploaded_excel = st.file_uploader("Chọn file Excel để thêm HTML tags", type=["xlsx", "xls"])
    
    if uploaded_excel is not None:
        try:
            # Đọc file Excel
            df = pd.read_excel(uploaded_excel)
            st.write("**Dữ liệu gốc:**")
            st.dataframe(df.head())
            
            # Xử lý với HTML
            df_processed = process_excel_with_html(df)
            
            if df_processed is not None:
                st.write("**Dữ liệu sau khi xử lý:**")
                st.dataframe(df_processed.head())
                
                # Tạo file Excel đã xử lý
                output_buffer = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                df_processed.to_excel(output_buffer.name, index=False)
                
                with open(output_buffer.name, "rb") as f:
                    st.success("✅ Đã xử lý xong!")
                    st.download_button(
                        label="📥 Tải file Excel đã xử lý",
                        data=f,
                        file_name="baiviet_processed.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                # Cleanup
                os.unlink(output_buffer.name)
                
        except Exception as e:
            st.error(f"Đã xảy ra lỗi: {e}")

# Hướng dẫn sử dụng
st.sidebar.markdown("""
## 📋 Hướng dẫn sử dụng

### Tab 1: Xử lý File Zip
1. Upload file .zip chứa các thư mục
2. Mỗi thư mục phải có file README.md
3. Script sẽ tạo Excel với 2 cột: "Tiêu đề" và "Nội dung"
4. Tự động loại bỏ dấu # trong nội dung

### Tab 2: Xử lý File Excel  
1. Upload file Excel có ít nhất 2 cột
2. Script sẽ thêm HTML tags và random links
3. Cột A: Thêm link random và format HTML
4. Cột B: Giữ nguyên + thêm link động

### Tính năng:
- ✅ Loại bỏ dấu # trong text
- ✅ Random links từ pool có sẵn
- ✅ Chuyển đổi markdown thành HTML
- ✅ Thêm link động giữa các cột
""")
