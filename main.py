import streamlit as st
from supabase import create_client
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from datetime import datetime

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
    # Gera o QR Code
    qr = qrcode.QRCode(version=1, box_size=12, border=1)
    qr.add_data(str(conteudo))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    qr_w, qr_h = qr_img.size
    
    # Canvas para 10x6.5cm
    canvas_w = qr_w + 300 
    canvas_h = qr_h + 120
    
    canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(canvas)
    
    try:
        font_p = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_l = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
        font_data = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18) # Fonte pequena para data
    except:
        font_p = ImageFont.load_default()
        font_l = ImageFont.load_default()
        font_data = ImageFont.load_default()

    # Código Principal
    draw.text((150, 20), str(conteudo), fill="black", font=font_p)
    
    # Legendas L P N
    draw.text((40, 100), "L", fill="black", font=font_l)
    draw.text((40, 160), "P", fill="black", font=font_l)
    draw.text((40, 220), "N", fill="black", font=font_l)
    
    # Data e Hora (Canto inferior direito)
    data_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    draw.text((canvas_w - 180, canvas_h - 30), data_str, fill="gray", font=font_data)
    
    # QR Code
    canvas.paste(qr_img, (130, 100))
    
    return canvas

# --- INTERFACE ---
st.title("📟 Gerador Zebra (10x6.5cm) com Data")

proximo = buscar_ultimo() + 1
st.metric(label="Próximo Código Sequencial", value=f"{proximo:08d}")

tab_auto, tab_man, tab_list = st.tabs(["⚡ Automático", "🎯 Manual", "📋 Lista"])

with tab_auto:
    qtd = st.number_input("Quantidade:", min_value=1, max_value=200, value=10)
    
    st.write("---")
    st.subheader("👁️ Pré-visualização com Data de Controle")
    img_preview = gerar_etiqueta_pil(f"{proximo:08d}")
    st.image(img_preview, caption=f"Amostra: {proximo:08d}", width=500)
    st.write("---")

    if st.button("🚀 GERAR PDF 10x6.5cm", use_container_width=True):
        inicio, fim = proximo, proximo + qtd - 1
        pdf = FPDF(orientation='L', unit='mm', format=(65, 100))
        
        for i in range(qtd):
            num_str = f"{(inicio + i):08d}"
            pdf.add_page()
            # Ajustado para ocupar bem o espaço de 10cm da sua Zebra
            pdf.image(gerar_etiqueta_pil(num_str), x=5, y=5, w=90) 
        
        pdf_output = pdf.output()
        try:
            supabase.table("registros_etiquetas").insert({
                "inicio": inicio, 
                "fim": fim, 
                "quantidade": qtd
            }).execute()
            st.success(f"Lote {inicio:08d} a {fim:08d} salvo no banco!")
            st.download_button("📥 Baixar PDF Zebra", bytes(pdf_output), f"lote_{inicio}.pdf", "application/pdf")
        except:
            st.download_button("📥 Baixar PDF (Erro de Conexão)", bytes(pdf_output), f"lote_{inicio}.pdf", "application/pdf")

with tab_man:
    txt = st.text_input("Código único:")
    if txt:
        st.image(gerar_etiqueta_pil(txt), width=500)
    if st.button("🎨 Gerar Etiqueta Manual"):
        if txt:
            pdf = FPDF(orientation='L', unit='mm', format=(65, 100))
            pdf.add_page()
            pdf.image(gerar_etiqueta_pil(txt), x=5, y=5, w=90)
            st.download_button("📥 Baixar PDF Avulso", bytes(pdf.output()), "manual.pdf")

with tab_list:
    lista = st.text_area("Cole a lista:", height=150)
    if lista:
        codigos_pre = [c.strip() for c in lista.split("\n") if c.strip()]
        if codigos_pre:
            st.image(gerar_etiqueta_pil(codigos_pre[0]), width=500)

    if st.button("📦 Gerar PDF da Lista"):
        codigos = [c.strip() for c in lista.split("\n") if c.strip()]
        if codigos:
            pdf = FPDF(orientation='L', unit='mm', format=(65, 100))
            for cod in codigos:
                pdf.add_page()
                pdf.image(gerar_etiqueta_pil(cod), x=5, y=5, w=90)
            st.download_button("📥 Baixar PDF da Lista", bytes(pdf.output()), "lista.pdf")
