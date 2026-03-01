import streamlit as st
from supabase import create_client
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
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

# --- ETIQUETA PADRAO (10x6.5 cm) ---
def gerar_etiqueta_pil(conteudo):
    qr = qrcode.QRCode(version=1, box_size=12, border=1)
    qr.add_data(str(conteudo))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    canvas_w, canvas_h = qr_img.size[0] + 300, qr_img.size[1] + 120
    canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(canvas)
    try:
        font_p = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_l = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
        font_data = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_p = ImageFont.load_default(); font_l = ImageFont.load_default(); font_data = ImageFont.load_default()
    draw.text((150, 20), str(conteudo), fill="black", font=font_p)
    draw.text((40, 100), "L", fill="black", font=font_l); draw.text((40, 160), "P", fill="black", font=font_l); draw.text((40, 220), "N", fill="black", font=font_l)
    fuso_br = pytz.timezone('America/Sao_Paulo')
    data_br = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
    draw.text((canvas_w - 180, canvas_h - 30), data_br, fill="gray", font=font_data)
    canvas.paste(qr_img, (130, 100))
    return canvas

# --- ETIQUETA LARGA (31.5x8 cm) ---
def gerar_etiqueta_larga_pil(lista_codigos):
    canvas_w, canvas_h = 3150, 800
    canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(canvas)
    try:
        font_t = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
        font_c = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        font_t = ImageFont.load_default(); font_c = ImageFont.load_default()

    if lista_codigos:
        partes = str(lista_codigos[0]).split('.')
        if len(partes) >= 2:
            titulo = f"RUA {partes[0]} POSICAO {partes[1]}"
            w_t = draw.textlength(titulo, font=font_t)
            draw.text(((canvas_w - w_t) / 2, 25), titulo, fill="black", font=font_t)

    largura_item = 3150 / 7
    # Linhas divisorias grossas
    for i in range(1, 7):
        x_l = i * largura_item
        draw.line([(x_l, 120), (x_l, 780)], fill="black", width=8)

    for i, cod in enumerate(lista_codigos[:7]):
        qr = qrcode.QRCode(version=1, box_size=14, border=1)
        qr.add_data(str(cod))
        qr.make(fit=True)
        qr_img = qr.paste_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        
        x_item = i * largura_item
        offset_qr = (largura_item - qr_img.size[0]) / 2
        x_final = x_item + offset_qr
        
        w_c = draw.textlength(str(cod), font=font_c)
        offset_txt = (qr_img.size[0] - w_c) / 2
        
        draw.text((x_final + offset_txt, 140), str(cod), fill="black", font=font_c)
        canvas.paste(qr_img, (int(x_final), 220))
    return canvas

# --- INTERFACE ---
st.title("Gerador de LPN/QR Code")
prox = buscar_ultimo() + 1
st.metric(label="Proximo Codigo", value=f"{prox:08d}")

t1, t2, t3, t4 = st.tabs(["Automatico", "Manual", "Lista", "Etiqueta Larga"])

with t1:
    q = st.number_input("Qtd (10x6.5):", min_value=1, max_value=200, value=10, key="k1")
    st.image(gerar_etiqueta_pil(f"{prox:08d}"), width=500)
    if st.button("GERAR LOTE", key="b1"):
        ini, fim = prox, prox + q - 1
        pdf = FPDF(orientation='L', unit='mm', format=(65, 100))
        for i in range(q):
            pdf.add_page()
            pdf.image(gerar_etiqueta_pil(f"{(ini + i):08d}"), x=5, y=5, w=90)
        out = pdf.output()
        supabase.table("registros_etiquetas").insert({"inicio": ini, "fim": fim, "quantidade": q}).execute()
        st.download_button("Baixar PDF", bytes(out), f"lote_{ini}.pdf", "application/pdf")

with t2:
    m = st.text_input("Codigo (10x6.5):", key="k2")
    if m:
        st.image(gerar_etiqueta_pil(m), width=500)
        if st.button("GERAR MANUAL", key="b2"):
            pdf2 = FPDF(orientation='L', unit='mm', format=(65, 100))
            pdf2.add_page()
            pdf2.image(gerar_etiqueta_pil(m), x=5, y=5, w=90)
            st.download_button("Baixar PDF", bytes(pdf2.output()), "manual.pdf")

with t3:
    l = st.text_area("Lista (10x6.5):", height=150, key="k3")
    if l:
        cs = [c.strip() for c in l.split("\n") if c.strip()]
        if cs:
            st.image(gerar_etiqueta_pil(cs[0]), width=500)
            if st.button("GERAR LISTA", key="b3"):
                pdf3 = FPDF(orientation='L', unit='mm', format=(65, 100))
                for c in cs:
                    pdf3.add_page()
                    pdf3.image(gerar_etiqueta_pil(c), x=5, y=5, w=90)
                st.download_button("Baixar PDF", bytes(pdf3.output()), "lista.pdf")

with t4:
    lg = st.text_area("Codigos (31.5x8):", height=150, key="k4")
    if lg:
        it = [e.strip() for e in lg.split("\n") if e.strip()]
        if it:
            st.image(gerar_etiqueta_larga_pil(it[:7]), use_container_width=True)
            if st.button("GERAR LARGA", key="b4"):
                pdf4 = FPDF(orientation='L', unit='mm', format=(80, 315))
                for i in range(0, len(it), 7):
                    pdf4.add_page()
                    pdf4.image(gerar_etiqueta_larga_pil(it[i:i+7]), x=0, y=0, w=315, h=80)
                st.download_button("Baixar PDF", bytes(pdf4.output()), "larga.pdf")
