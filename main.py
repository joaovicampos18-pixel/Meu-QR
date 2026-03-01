import streamlit as st
from supabase import create_client
import qrcode, pytz
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Gerador QR", layout="wide")

# Ajuste de Cor para Visibilidade (Azul Royal para destacar no fundo claro/escuro)
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #4A90E2; margin-bottom: 0px; }
    .dev-credits { 
        font-size: 16px; 
        color: #FFFFFF; 
        background-color: #4A90E2; 
        padding: 10px; 
        border-radius: 5px; 
        margin-bottom: 20px;
    }
    </style>
    <div class="main-title">Gerador de LPN/QR Code</div>
    <div class="dev-credits">Desenvolvido por: <b>Joao Vitor de Campos Leandro Silva</b> | 2026</div>
    """, unsafe_allow_html=True)

def conectar():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None
db = conectar()

def buscar_ultimo():
    try:
        r = db.table("registros_etiquetas").select("fim").order("fim",desc=True).limit(1).execute()
        return int(r.data[0]['fim']) if r.data else 0
    except: return 0

def f_padrao(txt):
    qr = qrcode.QRCode(box_size=12, border=1)
    qr.add_data(str(txt)); qr.make(fit=True)
    img = qr.make_image().convert('RGB')
    canv = Image.new('RGB', (img.size[0]+300, img.size[1]+120), 'white')
    d = ImageDraw.Draw(canv)
    try:
        f1=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",60)
        f3=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",18)
    except: f1=f3=ImageFont.load_default()
    d.text((150,20),str(txt),fill="black",font=f1)
    dt = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M")
    d.text((canv.size[0]-180,canv.size[1]-30),dt,fill="gray",font=f3)
    canv.paste(img,(130,100))
    return canv

def f_larga(lista):
    canv = Image.new('RGB', (3150, 800), 'white')
    d = ImageDraw.Draw(canv)
    try:
        ft=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",90)
        fc=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",60)
    except: ft=fc=ImageFont.load_default()
    if lista and '.' in str(lista[0]):
        p = str(lista[0]).split('.')
        tit = f"RUA {p[0]} POSICAO {p[1]}"
        d.text(((3150-d.textlength(tit,font=ft))/2,25),tit,fill="black",font=ft)
    w = 3150/7
    for i in range(1,7): d.line([(i*w,120),(i*w,780)],fill="black",width=8)
    for i, c in enumerate(lista[:7]):
        qr = qrcode.QRCode(box_size=14, border=1); qr.add_data(str(c)); qr.make(fit=True)
        qimg = qr.make_image().convert('RGB')
        xf = (i*w)+(w-qimg.size[0])/2
        d.text((xf+(qimg.size[0]-d.textlength(str(c),font=fc))/2,140),str(c),fill="black",font=fc)
        canv.paste(qimg,(int(xf),220))
    return canv

px = buscar_ultimo() + 1
st.metric("Próximo Código", f"{px:08d}")
t1,t2,t3,t4 = st.tabs(["Auto","Manual","Lista","Larga (7 QRs)"])

with t1:
    q = st.number_input("Qtd:",1,200,10)
    if st.button("GERAR LOTE", key="btn_auto"):
        pdf = FPDF('L','mm',(65,100))
        for i in range(q):
            pdf.add_page(); pdf.image(f_padrao(f"{(px+i):08d}"),5,5,90)
        db.table("registros_etiquetas").insert({"inicio":px,"fim":px+q-1,"quantidade":q}).execute()
        st.download_button("Baixar PDF", bytes(pdf.output()), "lote.pdf")

with t2:
    m = st.text_input("Código:")
    if m and st.button("GERAR MANUAL", key="btn_man"):
        p2 = FPDF('L','mm',(65,100)); p2.add_page(); p2.image(f_padrao(m),5,5,90)
        st.download_button("Baixar PDF", bytes(p2.output()), "manual.pdf")

with t3:
    ls = st.text_area("Lista (1 por linha):")
    if ls and st.button("GERAR LISTA", key="btn_list"):
        p3 = FPDF('L','mm',(65,100))
        for c in ls.split("\n"):
            if c.strip(): p3.add_page(); p3.image(f_padrao(c.strip()),5,5,90)
        st.download_button("Baixar PDF", bytes(p3.output()), "lista.pdf")

with t4:
    lg = st.text_area("Códigos p/ Larga:")
    if lg:
        it = [e.strip() for e in lg.split("\n") if e.strip()]
        st.image(f_larga(it[:7]), use_container_width=True)
        if st.button("GERAR PDF LARGA", key="btn_larga"):
            p4 = FPDF('L','mm',(80,315))
            for i in range(0,len(it),7):
                p4.add_page(); p4.image(f_larga(it[i:i+7]),0,0,315,80)
            st.download_button("Baixar PDF", bytes(p4.output()), "larga.pdf")
