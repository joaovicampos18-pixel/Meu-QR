import streamlit as st
from supabase import create_client
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import zipfile
import pandas as pd

# Configuração da Página
st.set_page_config(page_title="Gerador QR Pro", page_icon="📟", layout="wide")

# Estilo do Rodapé - Versão Minimalista e Menos Exposta
st.markdown("""
    <style>
    .footer { 
        position: fixed; 
        left: 0; 
        bottom: 0; 
        width: 100%; 
        background-color: rgba(255, 255, 255, 0.5); 
        color: #999; 
        text-align: right; 
        padding: 5px 20px; 
        font-size: 10px; 
        z-index: 999; 
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

def gerar_etiqueta_img(conteudo):
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
        font_p = ImageFont.load_default()
        font_l = ImageFont.load_default()

    draw.text((130, 15), str(conteudo), fill="black", font=font_p)
    draw.text((40, 80), "L", fill="black", font=font_l)
    draw.text((40, 125), "P", fill="black", font=font_l)
    draw.text((40, 170), "N", fill="black", font=font_l)
    canvas.paste(qr_img, (110, 80))
    
    img_io = BytesIO()
    canvas.save(img_io, format="PNG")
    return img_io.getvalue()

# Interface Principal
st.title("📟 Gerador de Etiquetas")

proximo = buscar_ultimo() + 1
st.metric(label="Próximo Código", value=f"{proximo:08d}")

tab_auto, tab_man, tab_list = st.tabs(["⚡ Auto", "🎯 Manual", "📋 Lista"])

with tab_auto:
    qtd = st.number_input("Qtd:", min_value=1, max_value=500, value=10)
    if st.button("🚀 Gerar Sequência", use_container_width=True):
        inicio, fim = proximo, proximo + qtd - 1
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(qtd):
                num_str = f"{(inicio + i):08d}"
                zf.writestr(f"Etiqueta_{num_str}.png", gerar_etiqueta_img(num_str))
        
        supabase.table("registros_etiquetas").insert({"inicio": inicio, "fim": fim, "quantidade": qtd}).execute()
        st.session_state['file_ready'] = buf.getvalue()
        st.session_state['last_lot'] = f"{inicio:08d}-{fim:08d}"
        st.rerun()

    if 'file_ready' in st.session_state:
        st.success(f"Salvo: {st.session_state['last_lot']}")
        st.download_button("📥 Baixar ZIP", st.session_state['file_ready'], "etiquetas.zip")
        del st.session_state['file_ready']

with tab_man:
    txt = st.text_input("Código manual:")
    if st.button("🎨 Gerar"):
        if txt:
            img = gerar_etiqueta_img(txt)
            st.image(img, width=300)
            st.download_button("📥 Baixar", img, "etiqueta.png")

with tab_list:
    lista = st.text_area("Cole a lista:", height=150)
    if st.button("📦 Gerar Lote"):
        codigos = [c.strip() for c in lista.split("\n") if c.strip()]
        if codigos:
            buf = BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                for cod in codigos:
                    zf.writestr(f"Etiqueta_{cod}.png", gerar_etiqueta_img(cod))
            st.download_button("📥 Baixar ZIP", buf.getvalue(), "lista.zip")
