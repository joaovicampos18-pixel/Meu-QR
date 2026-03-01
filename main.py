import streamlit as st
from supabase import create_client
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
import pytz

# 1. Configuracao da Pagina
st.set_page_config(page_title="Gerador de LPN/QR Code", layout="wide")

# 2. Estilo e Creditos (Nome Completo)
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E1E1E; margin-bottom: 0px; }
    .dev-credits { font-size: 14px; color: #555; margin-bottom: 20px; border-bottom: 1px solid #DDD; padding-bottom: 10px; }
    </style>
    <div class="main-title">Gerador de LPN/QR Code</div>
    <div class="dev-credits">Desenvolvido por: <b>Joao Vitor de Campos Leandro Silva</b> | 2026</div>
    """, unsafe_allow_html=True)

def conectar():
    try:
        u = st.secrets["SUPABASE_URL"].strip()
        k = st.secrets["SUPABASE_KEY"].strip()
        return create_client(u, k)
    except: return None

db = conectar()

def buscar_ultimo():
    try:
        res = db.table("registros_etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
        return int(res.data[0]['fim']) if res.data else 0
    except: return 0

def gerar_et_pil(txt):
    qr = qrcode.QRCode(version=1, box_size=12, border=1)
    qr.add_data(str(txt))
    qr.make(fit=True)
    qimg = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    cw, ch = qimg.size[0] + 300, qimg.size[1] + 120
    canv = Image.new('RGB', (cw, ch), 'white')
    d = ImageDraw.Draw(canv)
    try:
        f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
        f3 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        f1 = ImageFont.load_default(); f2 = ImageFont.load_default(); f3 = ImageFont.load_default()
    d.text((150, 20), str(txt), fill="black", font=f1)
    d.text((40, 100), "L", fill="black", font=f2); d.text((40, 160), "P", fill="black", font=f2); d.text((40, 220), "N", fill="black", font=f2)
    fz = pytz.timezone('America/Sao_Paulo')
    dt = datetime.now(fz).strftime("%d/%m/%Y %H:%M")
    d.text((cw - 180, ch - 30), dt, fill="gray", font=f3)
    canv.paste(qimg, (130, 100))
    return canv

def gerar_larga_pil(lista):
    cw, ch = 3150, 800
    canv = Image.new('RGB', (cw, ch), 'white')
    d = ImageDraw.Draw(canv)
    try:
        ft = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
        fc = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        ft = ImageFont.load_default(); fc = ImageFont.load_default()
    if lista:
        pts = str(lista[0]).split('.')
        if len(pts) >= 2:
            tit = f"RUA {pts[0]} POSICAO {pts[1]}"
            wt = d.textlength(tit, font=ft)
            d.text(((cw - wt) / 2, 25), tit, fill="black", font=ft)
    w_item = 3150 / 7
    for i in range(1, 7):
        xl = i * w_item
        d.line([(xl, 120), (xl, 780)], fill="black", width=8)
    for i, c in enumerate(lista[:7]):
        qr = qrcode.QRCode(version=1, box_size=14, border=1)
        qr.add_data(str(c))
        qr.make(fit=True)
        qimg = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        xi = i * w_item
        ox = (w_item - qimg.size[0]) / 2
        xf = xi + ox
        wc = d.textlength(str(c), font=fc)
        ot = (qimg.size[0] - wc) / 2
        d.text((xf + ot, 140), str(c), fill="black", font=fc)
        canv.paste(qimg, (int(xf), 220))
    return canv

# --- INTERFACE ---
px = buscar_ultimo() + 1
st.metric(label="Proximo Codigo", value=f"{px:08d}")
t1, t2, t3, t4 = st.tabs(["Automatico", "Manual", "Lista", "Larga"])

with t1:
    q = st.number_input("Qtd:", 1, 200, 10, key="k1")
    st.image(gerar_et_pil(f"{px:08d}"), width=450)
    if st.button("GERAR LOTE", key="b1"):
        ini, fim = px, px + q - 1
        pdf = FPDF('L', 'mm', (65, 100))
        for i in range(q):
            pdf.add_page(); pdf.image(gerar_et_pil(f"{(ini+i):08d}"), 5, 5, 90)
        out = pdf.output()
        db.table("registros_etiquetas").insert({"inicio":ini,"fim":fim,"quantidade":q}).execute()
        st.download_button("Baixar PDF", bytes(out), f"lote_{ini}.pdf")

with t2:
    m = st.text_input("Codigo:", key="k2")
    if m:
        st.image(gerar_et_pil(m), width=450)
        if st.button("GERAR MANUAL", key="b2"):
            p2 = FPDF('L', 'mm', (65, 100))
            p2.add_page(); p2.image(gerar_et_pil(m), 5, 5, 90)
            st.download_button("Baixar PDF", bytes(p2.output()), "manual.pdf")

with t3:
    ls = st.text_area("Lista:", height=150, key="k3")
    if ls:
        cs = [c.strip() for c in ls.split("\n") if c.strip()]
        if cs:
            st.image(gerar_et_pil(cs[0]), width=450)
            if st.button("GERAR LISTA", key="b3"):
                p3 = FPDF('L', 'mm', (65, 100))
                for c in cs: p3.add_page(); p3.image(gerar_et_pil(c), 5, 5, 90)
                st.download_button("Baixar PDF", bytes(p3.output()), "lista.pdf")

with t4:
    lg = st.text_area("Codigos (7 por folha):", height=150, key="k4")
    if lg:
        it = [e.strip() for e in lg.split("\n") if e.strip()]
        if it:
            st.image(gerar_larga_pil(it[:7]), use_container_width=True)
            if st.button("GERAR LARGA", key="b4"):
                p4 = FPDF('L', 'mm', (80, 315))
                for i in range(0, len(it), 7):
                    p4.add_page(); p4.image(gerar_larga_pil(it[i:i+7]), 0, 0, 315, 80)
                st.download_button("Baixar PDF", bytes(p4.output()), "larga.pdf")
