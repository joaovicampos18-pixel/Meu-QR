import streamlit as st
from supabase import create_client
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import zipfile
import pandas as pd

st.set_page_config(page_title="Gerador QR Pro", page_icon="📟")

# Conexão
def conectar():
    try:
        url = st.secrets["SUPABASE_URL"].strip()
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception:
        return None

supabase = conectar()

if supabase is None:
    st.error("🚨 Configure as chaves nos Secrets!")
    st.stop()

st.title("📟 Gerador de Etiquetas")

# Função para buscar último número
def buscar_ultimo():
    try:
        res = supabase.table("registros_etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
        return int(res.data[0]['fim']) if res.data else 0
    except:
        return 0

# --- INTERFACE ---
tab1, tab2 = st.tabs(["🔢 Sequencial Automático", "✏️ Digitar Manual"])

with tab1:
    proximo = buscar_ultimo() + 1
    st.info(f"### Próximo número: **{proximo:08d}**")
    qtd = st.number_input("Quantidade de etiquetas:", min_value=1, value=10, key="auto_qtd")
    btn_auto = st.button("🚀 GERAR SEQUÊNCIA AUTOMÁTICA")

with tab2:
    texto_manual = st.text_input("Digite o código da etiqueta:", placeholder="Ex: 00005500")
    btn_manual = st.button("🎨 GERAR ETIQUETA MANUAL")

# --- LÓGICA DE GERAÇÃO ---
def gerar_etiqueta_img(conteudo):
    # Gerar o QR Code
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(conteudo)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Criar moldura (Texto em cima + QR embaixo)
    w, h = qr_img.size
    canvas = Image.new('RGB', (w, h + 50), 'white')
    draw = ImageDraw.Draw(canvas)
    
    # Desenha o texto no topo
    draw.text((w/2 - 30, 10), str(conteudo), fill="black")
    canvas.paste(qr_img, (0, 40))
    
    img_io = BytesIO()
    canvas.save(img_io, format="PNG")
    return img_io.getvalue()

# Ação Automática
if btn_auto:
    inicio, fim = proximo, proximo + qtd - 1
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(qtd):
            num_str = f"{(inicio + i):08d}"
            zf.writestr(f"Etiqueta_{num_str}.png", gerar_etiqueta_img(num_str))
    
    try:
        supabase.table("registros_etiquetas").insert({"inicio": inicio, "fim": fim, "quantidade": qtd}).execute()
        st.success(f"✅ Lote {inicio:08d} a {fim:08d} salvo!")
        st.download_button("📥 Baixar ZIP", buf.getvalue(), f"lote_{inicio}.zip")
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# Ação Manual
if btn_manual:
    if texto_manual:
        img_data = gerar_etiqueta_img(texto_manual)
        st.image(img_data, caption=f"Etiqueta: {texto_manual}")
        st.download_button("📥 Baixar Etiqueta Única", img_data, f"etiqueta_{texto_manual}.png")
    else:
        st.warning("⚠️ Por favor, digite um código primeiro.")

# Histórico
with st.expander("📊 Ver Histórico"):
    try:
        h = supabase.table("registros_etiquetas").select("*").order("id", desc=True).limit(5).execute()
        if h.data:
            st.table(pd.DataFrame(h.data)[['id', 'inicio', 'fim', 'quantidade']])
    except:
        st.write("Sem registros.")
