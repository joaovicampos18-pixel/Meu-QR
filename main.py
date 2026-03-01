import streamlit as st
from supabase import create_client
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import pytz # Biblioteca para fuso horário

# 1. Configuração da Página
st.set_page_config(page_title="Gerador QR Pro - João Vitor", page_icon="📟", layout="wide")

# 2. Rodapé Discreto
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
    qr = qrcode.QRCode(version=1, box_size=12, border=1)
    qr.add_data(str(conteudo))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    qr_w, qr_h = qr_img.size
    canvas_w, canvas_h = qr_w + 300, qr_h + 120
    canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(canvas)
    
    try:
        font_p = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_l = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
        font_data = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_p = ImageFont.load_default(); font_l = ImageFont.load_default(); font_data = ImageFont.load_default()

    draw.text((150, 20), str(conteudo), fill="black", font=font_p)
    draw.text((40, 100), "L", fill="black", font=font_l)
    draw.text((40, 160), "P", fill="black", font=font_l)
    draw.text((40, 220), "N", fill="black", font=font_l)
    
    # CORREÇÃO DO FUSO HORÁRIO
    fuso_br = pytz.timezone('America/Sao_Paulo')
    data_br = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
    draw.text((canvas_w - 180, canvas_h - 30), data_br, fill="gray", font=font_data)
    
    canvas.paste(qr_img, (130, 100))
    return canvas

# --- INTERFACE ---
st.title("📟 Gerador Zebra (100x65mm) - Horário Brasília")

proximo = buscar_ultimo() + 1
st.metric(label="Próximo Código Sequencial", value=f"{proximo:08d}")

tab_auto, tab_man, tab_list = st.tabs(["⚡ Automático", "🎯 Manual", "📋 Lista"])

with tab_auto:
    qtd = st.number_input("Quantidade:", min_value=1, max_value=200, value=10)
    
    st.write("---")
    st.subheader("👁️ Pré-visualização (Amostra com Hora de Brasília)")
    img_preview = gerar_etiqueta_pil(f"{proximo:08d}")
    st.image(img_preview, caption=f"Amostra: {proximo:08d}", width=500)
    st.write("---")

    if st.button("🚀 GERAR PDF 10x6.5cm", use_container_width=True):
        inicio, fim = proximo, proximo + qtd - 1
        pdf = FPDF(orientation='L', unit='mm', format=(65, 100))
        
        for i in range(qtd):
            num_str = f"{(inicio + i):08d}"
            pdf.add_page()
            pdf.image(gerar_etiqueta_pil(num_str), x=5, y=5, w=90) 
        
        pdf_output = pdf.output()
        try:
            supabase.table("registros_etiquetas").insert({"inicio": inicio, "fim": fim, "quantidade": qtd}).execute()
            st.success(f"Lote {inicio:08d} a {fim:08d} salvo!")
            st.download_button("📥 Baixar PDF Zebra", bytes(pdf_output), f"lote_{inicio}.pdf", "application/pdf")
        except:
            st.download_button("📥 Baixar PDF", bytes(pdf_output), f"lote_{inicio}.pdf", "application/pdf")

# (As abas Manual e Lista seguem a mesma lógica)
