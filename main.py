import streamlit as st
from supabase import create_client
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import pandas as pd
from fpdf import FPDF

# 1. Configuração da Página
st.set_page_config(page_title="Gerador QR Pro", page_icon="📟", layout="wide")

# 2. Rodapé Discreto - J.V.C.L. Silva
st.markdown("""
    <style>
    .footer { 
        position: fixed; left: 0; bottom: 0; width: 100%; 
        background-color: rgba(255, 255, 255, 0.8); 
        color: #999; text-align: right; padding: 5px 20px; 
        font-size: 10px; z-index: 999; 
    }
    </style>
    <div class="footer">Dev: J.V.C.L. Silva | 2026</div>
    """, unsafe_allow_html=True)

def conectar():
    try:
        url = st.secrets["SUPABASE_URL"].strip()
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except: return None

supabase = conectar()

def buscar_ultimo():
    try:
        res = supabase.table("registros_etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
        return int(res.data[0]['fim']) if res.data else 0
    except: return 0

def gerar_etiqueta_pil(conteudo):
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(str(conteudo))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    qr_w, qr_h = qr_img.size
    canvas_w, canvas_h = qr_w + 120, qr_h + 100
    canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(canvas)
    
    try:
        font_p = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
        font_l = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except:
        font_p = ImageFont.load_default(); font_l = ImageFont.load_default()

    draw.text((130, 15), str(conteudo), fill="black", font=font_p)
    draw.text((40, 80), "L", fill="black", font=font_l)
    draw.text((40, 125), "P", fill="black", font=font_l)
    draw.text((40, 170), "N", fill="black", font=font_l)
    canvas.paste(qr_img, (110, 80))
    return canvas

# --- INTERFACE ---
st.title("📟 Gerador Zebra - Visualização Real")

proximo = buscar_ultimo() + 1
st.metric(label="Próximo Código Sequencial", value=f"{proximo:08d}")

tab_auto, tab_man, tab_list = st.tabs(["⚡ Automático", "🎯 Manual", "📋 Lista"])

with tab_auto:
    qtd = st.number_input("Quantidade:", min_value=1, max_value=200, value=10)
    
    st.write("---")
    st.subheader("👁️ Pré-visualização (Primeiras 10)")
    
    limite_preview = min(qtd, 10)
    # Reduzido para 2 colunas para garantir que a imagem fique inteira e grande
    cols = st.columns(2) 
    for i in range(limite_preview):
        num_preview = f"{(proximo + i):08d}"
        img_preview = gerar_etiqueta_pil(num_preview)
        with cols[i % 2]:
            # width=None e use_container_width=True garantem que ela ocupe a coluna sem cortar
            st.image(img_preview, caption=f"Etiqueta: {num_preview}", use_container_width=True)
            st.write("") # Espaçador para não grudar na de baixo
    
    st.write("---")

    if st.button("🚀 GERAR PDF COMPLETO", use_container_width=True):
        inicio, fim = proximo, proximo + qtd - 1
        pdf = FPDF(orientation='L', unit='mm', format=(40, 80))
        for i in range(qtd):
            pdf.add_page()
            pdf.image(gerar_etiqueta_pil(f"{(inicio + i):08d}"), x=2, y=2, w=76) 
        
        pdf_output = pdf.output()
        try:
            supabase.table("registros_etiquetas").insert({"inicio": inicio, "fim": fim, "quantidade": qtd}).execute()
            st.success(f"Lote {inicio:08d} a {fim:08d} salvo!")
            st.download_button("📥 Baixar PDF", bytes(pdf_output), f"lote_{inicio}.pdf", "application/pdf")
        except:
            st.download_button("📥 Baixar PDF (Offline)", bytes(pdf_output), f"lote_{inicio}.pdf", "application/pdf")

with tab_man:
    txt = st.text_input("Código único:")
    if txt:
        st.image(gerar_etiqueta_pil(txt), width=400, caption="Visualização Completa")
    if st.button("🎨 Gerar PDF Avulso"):
        if txt:
            pdf = FPDF(orientation='L', unit='mm', format=(40, 80))
            pdf.add_page()
            pdf.image(gerar_etiqueta_pil(txt), x=2, y=2, w=76)
            st.download_button("📥 Baixar PDF", bytes(pdf.output()), "etiqueta_avulsa.pdf")

with tab_list:
    lista = st.text_area("Cole a lista:", height=150)
