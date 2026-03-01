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

# --- ETIQUETA LARGA (31.5x8 cm) - QR CODES AMPLIADOS ---
def gerar_etiqueta_larga_pil(lista_codigos):
    # Proporção 31.5 x 8 (3150x800 pixels)
    canvas_w, canvas_h = 3150, 800
    canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(canvas)
    try:
        font_titulo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 95) # Titulo maior
        font_cod = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)    # Codigo maior
    except:
        font_titulo = ImageFont.load_default(); font_cod = ImageFont.load_default()

    if lista_codigos:
        partes = str(lista_codigos[0]).split('.')
        if len(partes) >= 2:
            titulo = f"RUA {partes[0]} POSICAO {partes[1]}"
            w_text = draw.textlength(titulo, font=font_titulo)
            draw.text(((canvas_w - w_text) / 2, 30), titulo, fill="black", font=font_titulo)

    # Parametros para maximizar o tamanho
    margem_inicial = 60
    espacamento_entre = 440 

    for i, cod in enumerate(lista_codigos[:7]):
        # Aumentei box_size de 9 para 13 para o QR Code ficar bem grande
        qr = qrcode.QRCode(version=1, box_size=13, border=2)
        qr.add_data(str(cod))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        
        x_pos = margem_inicial + (i * espacamento_entre)
        
        # Centralizar texto do codigo sobre o seu respectivo QR
        w_cod = draw.textlength(str(cod), font=font_cod)
        offset_texto = (qr_img.size[0] - w_cod) / 2
        
        # Desenha Texto e QR Code (Posicionados para aproveitar a altura)
        draw.text((x_pos + offset_texto, 160), str(cod), fill="black", font=font_cod)
        canvas.paste(qr_img, (x_pos, 250))
    return canvas

# --- INTERFACE ---
st.title("Gerador de LPN/QR Code")
proximo = buscar_ultimo() + 1
st.metric(label="Proximo Codigo Sequencial", value=f"{proximo:08d}")

tab_auto, tab_man, tab_list, tab_larga = st.tabs(["Automatico", "Manual", "Lista", "Etiqueta Larga"])

with tab_auto:
    qtd = st.number_input("Quantidade (10x6.5):", min_value=1, max_value=200, value=10, key="q_auto")
    st.subheader("Pre-visualizacao")
    st.image(gerar_etiqueta_pil(f"{proximo:08d}"), width=500)
    if st.button("GERAR PDF E SALVAR LOTE", key="btn_auto"):
        inicio, fim = proximo, proximo + qtd - 1
        pdf = FPDF(orientation='L', unit='mm', format=(65, 100))
        for i in range(qtd):
            pdf.add_page()
            pdf.image(gerar_etiqueta_pil(f"{(inicio + i):08d}"), x=5, y=5, w=90) 
        pdf_out = pdf.output()
        try:
            supabase.table("registros_etiquetas").insert({"inicio": inicio, "fim": fim, "quantidade": qtd}).execute()
            st.success(f"Lote {inicio:08d} a {fim:08d} salvo")
            st.download_button("Baixar PDF Automático", bytes(pdf_out), f"lote_{inicio}.pdf", "application/pdf")
        except: st.download_button("Baixar PDF (Erro DB)", bytes(pdf_out), f"lote_{inicio}.pdf", "application/pdf")

with tab_man:
    txt_m = st.text_input("Digite o codigo (10x6.5):", key="in_man")
    if txt_m:
        st.subheader("Pre-visualizacao")
        st.image(gerar_etiqueta_pil(txt_m), width=500)
        if st.button("GERAR PDF MANUAL", key="btn_ind"):
            pdf_m = FPDF(orientation='L', unit='mm', format=(65, 100))
            pdf_m.add_page(); pdf_m.image(gerar_etiqueta_pil(txt_m), x=5, y=5, w=90)
            st.download_button("Baixar PDF Manual", bytes(pdf_m.output()), "individual.pdf", "application/pdf")

with tab_list:
    txt_l = st.text_area("Cole a lista (10x6.5):", height=150, key="ta_list")
    if txt_l:
        cods = [c.strip() for c in txt_l.split("\n") if c.strip()]
        if cods:
            st.subheader("Pre-visualizacao")
            st.image(gerar_etiqueta_pil(cods[0]), width=500)
            if st.button("GERAR PDF DA LISTA", key="btn_list_pdf"):
                pdf_l = FPDF(orientation='L', unit='mm', format=(65, 100))
                for c in cods: pdf_l.add_page(); pdf_l.image(gerar_etiqueta_pil(c), x=5, y=5, w=90)
                st.download_button("Baixar PDF Lista", bytes(pdf_l.output()), "lista.pdf", "application/pdf")

with tab_larga:
    st.subheader("Etiqueta de Rua/Posicao (31.5 x 8 cm)")
    txt_lg = st.text_area("Cole os codigos (Ex: 001.002.7):", height=200, key="ta_larga")
    if txt_lg:
        itens = [e.strip() for e in txt_lg.split("\n") if e.strip()]
        if itens:
            st.subheader("Pre-visualizacao (Tamanho Ampliado)")
            st.image(gerar_etiqueta_larga_pil(itens[:7]), use_container_width=True)
            if st.button("GERAR PDF ETIQUETA LARGA", key="btn_lg_pdf"):
                pdf_lg = FPDF(orientation='L', unit='mm', format=(80, 315))
                for i in range(0, len(itens), 7):
                    pdf_lg.add_page()
                    pdf_lg.image(gerar_etiqueta_larga_pil(itens[i:i+7]), x=0, y=0, w=315, h=80)
                st.download_button("Baixar PDF Largo", bytes(pdf_lg.output()), "etiquetas_largas.pdf", "application/pdf")
