import streamlit as st
import pandas as pd
import os
import re
import tempfile
import zipfile

def clean_final_repo_name(title: str) -> str:
    if not title:
        return ""
    name = title.strip()
    name = re.sub(r"^#+\s*", "", name)
    if "-" in name:
        name = name.rsplit("-", 1)[0].strip()
    return name

def export_repos_to_excel(base_dir, output_path):
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
        final_name = clean_final_repo_name(title)

        data.append({
            "Tên repo": repo_dir,
            "Tiêu đề": title,
            "Nội dung": body,
            "Tên repo cuối cùng": final_name
        })

    df = pd.DataFrame(data, columns=["Tên repo", "Tiêu đề", "Nội dung", "Tên repo cuối cùng"])
    df.to_excel(output_path, index=False)

# -------------------- Streamlit UI --------------------

st.title("📂 Xuất Repo sang Excel")

uploaded_file = st.file_uploader("Upload file .zip chứa các repo (baiviet.zip)", type=["zip"])

if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "repos.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Giải nén
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)

        output_path = os.path.join(tmpdir, "repocuoicung.xlsx")
        export_repos_to_excel(tmpdir, output_path)

        with open(output_path, "rb") as f:
            st.success("✅ Đã xuất Excel thành công!")
            st.download_button(
                label="📥 Tải file Excel",
                data=f,
                file_name="repocuoicung.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
