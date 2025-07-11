import streamlit as st
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import tempfile
import base64
import os

st.set_page_config(page_title="PDF Print Manager", layout="centered")


# ------------------ Detect if Page is Color ------------------

def is_color_page(page):
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    grayscale = img.convert("L").convert("RGB")
    return list(img.getdata()) != list(grayscale.getdata())


# ------------------ Split PDF into Color & B/W ------------------

def split_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    color_writer = PdfWriter()
    bw_writer = PdfWriter()
    color_count = 0
    bw_count = 0

    for i, page in enumerate(doc):
        pdf_reader = PdfReader(uploaded_file)
        page_obj = doc.load_page(i)
        if is_color_page(page_obj):
            color_writer.add_page(PdfReader(uploaded_file).pages[i])
            color_count += 1
        else:
            bw_writer.add_page(PdfReader(uploaded_file).pages[i])
            bw_count += 1

    # Create temp files
    color_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    bw_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    with open(color_file.name, 'wb') as f:
        color_writer.write(f)
    with open(bw_file.name, 'wb') as f:
        bw_writer.write(f)

    return color_file.name, bw_file.name, color_count, bw_count


# ------------------ File Download Helper ------------------

def get_pdf_download_link(file_path, label):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        href = f'<a href="data:application/pdf;base64,{base64_pdf}" download="{os.path.basename(file_path)}">{label}</a>'
        return href


# ------------------ Streamlit App ------------------

st.title("📄 PDF Print Manager")
st.caption("Automatically detect color vs black-and-white pages and manage your printing cost.")

uploaded_pdf = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_pdf:
    with st.spinner("Analyzing PDF..."):
        color_file, bw_file, color_pages, bw_pages = split_pdf(uploaded_pdf)

    st.success("PDF analyzed successfully!")
    st.write(f"🖍️ Color Pages: **{color_pages}**")
    st.write(f"🖤 B&W Pages: **{bw_pages}**")

    # Download buttons
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(get_pdf_download_link(color_file, "⬇️ Download Color PDF"), unsafe_allow_html=True)
    with col2:
        st.markdown(get_pdf_download_link(bw_file, "⬇️ Download B&W PDF"), unsafe_allow_html=True)

    # Cost calculator
    st.subheader("🧮 Print Cost Calculator")
    color_price = st.number_input("Price per Color Page (₹)", min_value=0.0, step=0.1)
    bw_price = st.number_input("Price per B&W Page (₹)", min_value=0.0, step=0.1)

    if st.button("Calculate Total"):
        total = color_pages * color_price + bw_pages * bw_price
        st.success(f"💰 Total Printing Cost: ₹{total:.2f}")
