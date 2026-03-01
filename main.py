import streamlit as st
from supabase import create_client
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import zipfile
import pandas as pd
from fpdf import FPDF

# Configuração da Página
st.set_page_config(page_title="Gerador QR Pro", page_icon="📟", layout="wide")

# Rodapé Discreto - J.V.C.L. Silva
st.markdown("""
    <style>
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: rgba(255, 255, 255, 0.5); 
               color: #999; text-align: right; padding: 5px 20px; font-size: 10px; z-index: 999; }
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
    
    # CORREÇÃO DO ERRO: Soma as dimensões individualmente
    qr_w, qr_h = qr_img.size
    canvas_w = qr_w + 120
    canvas_h = qr_h + 100
    
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
st.title("📟 Gerador Zebra PDF")

proximo = buscar_ultimo() + 1
st.metric(label="Próximo Código Sequencial", value=f"{proximo:08d}")

tab_auto, tab_man, tab_list = st.tabs(["⚡ Automático", "🎯 Manual", "📋 Lista"])

with tab_auto:
    qtd = st.number_input("Quantidade:", min_value=1, max_value=200, value=10)
    if st.button("🚀 GERAR PDF E SALVAR", use_container_width=True):
        inicio, fim = proximo, proximo + qtd - 1
        
        # PDF formatado para etiquetas comuns de 80mm x 40mm
        pdf = FPDF(orientation='L', unit='mm', format=(40, 80))
        
        for i in range(qtd):
            num_str = f"{(inicio + i):08d}"
            img = gerar_etiqueta_pil(num_str)
            
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            
            pdf.add_page()
            # Ajusta a imagem para preencher bem a etiqueta Zebra
            pdf.image(img_byte_arr, x=2, y=2, w=76) 

        pdf_output = pdf.output(dest='S')
        
        try:
            supabase.table("registros_etiquetas").insert({"inicio": inicio, "fim": fim, "quantidade": qtd}).execute()
            st.success(f"Lote {inicio:08d} a {fim:08d} processado!")
            st.download_button("📥 Baixar PDF para Zebra", pdf_output, f"lote_{inicio}.pdf", "application/pdf")
        except:
            st.error("Erro ao salvar no banco, mas você ainda pode baixar o PDF.")
            st.download_button("📥 Baixar PDF mesmo assim", pdf_output, f"lote_{inicio}.pdf", "application/pdf")

with tab_man:
    txt = st.text_input("Código único:")
    if st.button("🎨 Gerar PDF Avulso"):
        if txt:
            pdf = FPDF(orientation='L', unit='mm', format=(40, 80))
            img = gerar_etiqueta_pil(txt)
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            pdf.add_page()
            pdf.image(img_byte_arr, x=2, y=2, w=76)
            st.download_button("📥 Baixar PDF", pdf.output(dest='S'), "etiqueta.pdf")

with tab_list:
    lista = st.text_area("Cole a lista (um por linha):", height=150)
    if st.button("📦 Gerar Lote da Lista"):
        codigos = [c.strip() for c in lista.split("\n") if c.strip()]
        if codigos:
            pdf = FPDF(orientation='L', unit='mm', format=(40, 80))
            for cod in codigos:
                img = gerar_etiqueta_pil(cod)
                img_io = BytesIO()
                img.save(img_io, format='PNG')
                pdf.add_page()
                pdf.image(img_io, x=2, y=2, w=76)
            st.download_button("📥 Baixar PDF da Lista", pdf.output(dest='S'), "lista.pdf")
