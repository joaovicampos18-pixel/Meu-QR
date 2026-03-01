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
    # Gera o QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(str(conteudo))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    qr_w, qr_h = qr_img.size
    
    # AJUSTE DE LARGURA: Aumentei de 120 para 180 para dar folga ao número de 8 dígitos
    canvas_w = qr_w + 180 
    canvas_h = qr_h + 100
    
    canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(canvas)
    
    try:
        # Usando fontes padrão do Streamlit Cloud se a DejaVu falhar
        font_p = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
        font_l = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except:
        font_p = ImageFont.load_default()
        font_l = ImageFont.load_default()

    # AJUSTE DE POSIÇÃO: Texto começa no pixel 120 (antes era 130) para ganhar espaço à direita
    draw.text((120, 15), str(conteudo), fill="black", font=font_p)
    
    # Letras Laterais
    draw.text((30, 80), "L", fill="black", font=font_l)
    draw.text((30, 125), "P", fill="black", font=font_l)
    draw.text((30, 170), "N", fill="black", font=font_l)
    
    # Cola o QR Code
    canvas.paste(qr_img, (100, 80))
    
    return canvas

# --- INTERFACE ---
st.title("📟 Gerador Zebra - Sem Cortes")

proximo = buscar_ultimo() + 1
st.metric(label="Próximo Código Sequencial", value=f"{proximo:08d}")

tab_auto, tab_man, tab_list = st.tabs(["⚡ Automático", "🎯 Manual", "📋 Lista"])

with tab_auto:
    qtd = st.number_input("Quantidade:", min_value=1, max_value=200, value=10)
    
    st.write("---")
    st.subheader("👁️ Pré-visualização")
    
    limite_preview = min(qtd, 10)
    # Usando colunas individuais para garantir que o Streamlit não corte a imagem
    for i in range(limite_preview):
        num_preview = f"{(proximo + i):08d}"
        img_preview = gerar_etiqueta_pil(num_preview)
        st.image(img_preview, caption=f"Etiqueta {num_preview}", width=350) # Largura fixa maior na tela
    
    st.write("---")

    if st.button("🚀 GERAR PDF COMPLETO", use_container_width=True):
        inicio, fim = proximo, proximo + qtd - 1
        pdf = FPDF(orientation='L', unit='mm', format=(40, 80))
        for i in range(qtd):
            pdf.add_page()
            # Ajuste de escala no PDF para garantir que caiba na etiqueta real
            pdf.image(gerar_etiqueta_pil(f"{(inicio + i):08d}"), x=2, y=2, w=75) 
        
        pdf_output = pdf.output()
        try:
            supabase.table("registros_etiquetas").insert({"inicio": inicio, "fim": fim, "quantidade": qtd}).execute()
            st.success(f"Lote {inicio:08d} a {fim:08d} salvo!")
            st.download_button("📥 Baixar PDF", bytes(pdf_output), f"lote_{inicio}.pdf", "application/pdf")
        except:
            st.download_button("📥 Baixar PDF (Offline)", bytes(pdf_output), f"lote_{inicio}.pdf", "application/pdf")

# (As abas Manual e Lista seguem a mesma lógica de gerar_etiqueta_pil)
with tab_man:
    txt = st.text_input("Código único:")
    if txt:
        st.image(gerar_etiqueta_pil(txt), width=350)
    if st.button("🎨 Gerar PDF Avulso"):
        if txt:
            pdf = FPDF(orientation='L', unit='mm', format=(40, 80))
            pdf.add_page()
            pdf.image(gerar_etiqueta_pil(txt), x=2, y=2, w=75)
            st.download_button("📥 Baixar PDF", bytes(pdf.output()), "etiqueta_avulsa.pdf")

with tab_list:
    lista = st.text_area("Cole a lista:", height=150)
    if lista:
        codigos_pre = [c.strip() for c in lista.split("\n") if c.strip()]
        for cod in codigos_pre[:10]:
            st.image(gerar_etiqueta_pil(cod), width=350)

    if st.button("📦 Gerar PDF da Lista"):
        codigos = [c.strip() for c in lista.split("\n") if c.strip()]
        if codigos:
            pdf = FPDF(orientation='L', unit='mm', format=(40, 80))
            for cod in codigos:
                pdf.add_page()
                pdf.image(gerar_etiqueta_pil(cod), x=2, y=2, w=75)
            st.download_button("📥 Baixar PDF da Lista", bytes(pdf.output()), "lista.pdf")
