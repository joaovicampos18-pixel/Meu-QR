import streamlit as st
from supabase import create_client
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import pytz

# 1. Configuracao da Pagina
st.set_page_config(page_title="Gerador de LPN/QR Code", page_icon="📟", layout="wide")

# 2. Rodape Discreto
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

# --- LOGICA ETIQUETA PADRAO (10x6.5 cm) ---
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
    fuso_br = pytz.timezone('America/Sao_Paulo')
    data_br = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
    draw.text((canvas_w - 180, canvas_h - 30), data_br, fill="gray", font=font_data)
    canvas.paste(qr_img, (130, 100))
    return canvas

# --- LOGICA ETIQUETA LARGA (31.5x8 cm - 7 QR Codes) ---
def gerar_etiqueta_larga_pil(lista_codigos):
    canvas_w, canvas_h = 3150, 800
    canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(canvas)
    try:
        font_cod = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
    except:
        font_cod = ImageFont.load_default()
    largura_item = 450 
    for i, cod in enumerate(lista_codigos[:7]):
        qr = qrcode.QRCode(version=1, box_size=11, border=1)
        qr.add_data(str(cod))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        x_pos = 20 + (i * largura_item)
        canvas.paste(qr_img, (x_pos, 180))
        draw.text((x_pos + 30, 100), str(cod), fill="black", font=font_cod)
    return canvas

# --- INTERFACE ---
st.title("Gerador de LPN/QR Code")

proximo = buscar_ultimo() + 1
st.metric(label="Proximo Codigo Sequencial", value=f"{proximo:08d}")

tab_auto, tab_man, tab_list, tab_larga = st.tabs(["Automatico", "Manual", "Lista", "Etiqueta Larga"])

with tab_auto:
    qtd = st.number_input("Quantidade (10x6.5):", min_value=1, max_value=200, value=10)
    st.write("---")
    st.subheader("Pre-visualizacao")
    st.image(gerar_etiqueta_pil(f"{proximo:08d}"), width=500)
    if st.button("GERAR PDF E SALVAR", key="btn_gerar_auto"):
        inicio, fim = proximo, proximo + qtd - 1
        pdf = FPDF(orientation='L', unit='mm', format=(65, 100))
        for i in range(qtd):
            pdf.add_page()
            pdf.image(gerar_etiqueta_pil(f"{(inicio + i):08d}"), x=5, y=5, w=90) 
        pdf_out = pdf.output()
        try:
            supabase.table("registros_etiquetas").insert({"inicio": inicio, "fim": fim, "quantidade": qtd}).execute()
            st.success(f"Lote {inicio:08d} a {fim:08d} salvo")
            st.download_button("Baixar PDF", bytes(pdf_out), f"lote_{inicio}.pdf", "application/pdf")
        except:
            st.download_button("Baixar PDF (Offline)", bytes(pdf_out), f"lote_{inicio}.pdf", "application/pdf")

with tab_man:
    txt = st.text_input("Codigo unico (10x6.5):", key="input_manual_cod")
    if txt:
        st.image(gerar_etiqueta_pil(txt), width=500)
        if st.button("Gerar PDF Individual", key="btn_individual"):
            pdf_man = FPDF(orientation='L', unit='mm', format=(65, 100))
            pdf_man.add_page()
            pdf_man.image(gerar_etiqueta_pil(txt), x=5, y=5, w=90)
            st.download_button("Baixar PDF Individual", bytes(pdf_man.output()), "individual.pdf")

with tab_list:
    lista_txt = st.text_area("Cole a lista (10x6.5 - um por linha):", height=150, key="txt_area_lista")
    if lista_txt:
        cods_l = [c.strip() for c in lista_txt.split("\n") if c.strip()]
        if cods_l:
            st.image(gerar_etiqueta_pil(cods_l[0]), width=500)
            if st.button("Gerar PDF Lista", key="btn_pdf_lista"):
                pdf_list = FPDF(orientation='L', unit='mm', format=(65, 100))
                for c in cods_l:
                    pdf_list.add_page()
                    pdf_list.image(gerar_etiqueta_pil(c), x=5, y=5, w=90)
                st.download_button("Baixar PDF Lista", bytes(pdf_list.output()), "lista.pdf")

with tab_larga:
    st.subheader("Configuracao: 31.5 x 8 cm (Ate 7 QR Codes)")
    lista_larga_txt = st.text_area("Cole os codigos para a etiqueta larga:", height=200, key="txt_area_larga")
    if lista_larga_txt:
        itens_lg = [e.strip() for e in lista_larga_txt.split("\n") if e.strip()]
        if itens_lg:
            st.write("Pre-visualizacao (Primeiros 7):")
            st.image(gerar_etiqueta_larga_pil(itens_lg[:7]), use_container_width=True)
            if st.button("Gerar PDF Etiqueta Larga", key="btn_larga"):
                pdf_lg = FPDF(orientation='L', unit='mm', format=(80, 315))
                for i in range(0, len(itens_lg), 7):
                    grupo_lg = itens_lg[i : i+7]
                    pdf_lg.add_page()
                    pdf_lg.image(gerar_etiqueta_larga_pil(grupo_lg), x=0, y=0, w=315, h=80)
                st.download_button("Baixar PDF Largo", bytes(pdf_lg.output()), "etiquetas_largas.pdf")
