import streamlit as st
from supabase import create_client
import qrcode, pytz
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Gerador QR", layout="wide")

# Nome com Fundo Azul para visibilidade total
st.markdown("""
    <style>
    .dev { font-size: 16px; color: white; background: #4A90E2; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-weight: bold; }
    </style>
    <div class="dev">Desenvolvido por: Joao Vitor de Campos Leandro Silva | 2026</div>
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
    try: f1=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",60)
    except: f1=ImageFont.load_default()
    d.text((150,20),str(txt),fill="black",font=f1)
    canv.paste(img,(130,100))
    return canv

def f_larga(lista):
    canv = Image.new('RGB', (3150, 800), 'white')
    d = ImageDraw.Draw(canv)
    try: ft=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",90)
    except: ft=ImageFont.load_default()
    w = 3150/7
    for i in range(1,7): d.line([(i*w,120),(i*w,780)],fill="black",width=8)
    for i, c in enumerate(lista[:7]):
        qr = qrcode.QRCode(box_size=14, border=1); qr.add_data(str(c)); qr.make(fit=True)
        qimg = qr.make_image().convert('RGB')
        xf = (i*w)+(w-qimg.size[0])/2
        canv.paste(qimg,(int(xf),220))
        d.text((xf, 140), str(c), fill="black", font=ft)
    return canv

px = buscar_ultimo() + 1
st.metric("Próximo Código", f"{px:08d}")
t1,t2,t3,t4 = st.tabs(["Auto","Manual","Lista","Larga"])

with t1:
    q = st.number_input("Qtd:", 1, 200, 10, key="ka")
    st.image(f_padrao(f"{px:08d}"), width=400)
    if st.button("GERAR LOTE", key="ba"):
        pdf = FPDF('L','mm',(65,100))
        for i in range(q):
            pdf.add_page(); pdf.image(f_padrao(f"{(px+i):08d}"),5,5,90)
        db.table("registros_etiquetas").insert({"inicio":px,"fim":px+q-1,"quantidade":q}).execute()
        st.download_button("Download PDF", bytes(pdf.output()), "lote.pdf", key="da")

with t2:
    m = st.text_input("Código:", key="km")
    if m:
        st.image(f_padrao(m), width=400)
        if st.button("GERAR MANUAL", key="bm"):
            p2 = FPDF('L','mm',(65,100)); p2.add_page(); p2.image(f_padrao(m),5,5,90)
            st.download_button("Download PDF", bytes(p2.output()), "manual.pdf", key="dm")

with t3:
    ls = st.text_area("Lista:", key="kl")
    if ls:
        cs = [c.strip() for c in ls.split("\n") if c.strip()]
        if cs:
            st.image(f_padrao(cs[0]), width=400)
            if st.button("GERAR LISTA", key="bl"):
                p3 = FPDF('L','mm',(65,100))
                for c in cs: p3.add_page(); p3.image(f_padrao(c),5,5,90)
                st.download_button("Download PDF", bytes(p3.output()), "lista.pdf", key="dl")

with t4:
    lg = st.text_area("Códigos (7 por folha):", key="klg")
    if lg:
        it = [e.strip() for e in lg.split("\n") if e.strip()]
        if it:
            st.image(f_larga(it[:7]), use_container_width=True)
            if st.button("GERAR LARGA", key="blg"):
                p4 = FPDF('L','mm',(80,315))
                for i in range(0,len(it),7):
                    p4.add_page(); p4.image(f_larga(it[i:i+7]),0,0,315,80)
                st.download_button("Download PDF", bytes(p4.output()), "larga.pdf", key="dlg")
