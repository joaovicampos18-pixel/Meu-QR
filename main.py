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

def buscar_ultimo():
    try:
        res = supabase.table("registros_etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
        return int(res.data[0]['fim']) if res.data else 0
    except:
        return 0

# Função mestre para criar a imagem da etiqueta
def gerar_etiqueta_img(conteudo):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(str(conteudo))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    w, h = qr_img.size
    canvas = Image.new('RGB', (w, h + 50), 'white')
    draw = ImageDraw.Draw(canvas)
    
    # Texto no topo
    draw.text((w/2 - 30, 10), str(conteudo), fill="black")
    canvas.paste(qr_img, (0, 40))
    
    img_io = BytesIO()
    canvas.save(img_io, format="PNG")
    return img_io.getvalue()

# --- INTERFACE POR ABAS ---
tab1, tab2, tab3 = st.tabs(["🔢 Automático", "✏️ Manual", "📋 Colar Lista"])

with tab1:
    proximo = buscar_ultimo() + 1
    st.info(f"### Próximo número: **{proximo:08d}**")
    qtd = st.number_input("Quantidade:", min_value=1, value=10, key="auto_qtd")
    if st.button("🚀 GERAR SEQUÊNCIA"):
        inicio, fim = proximo, proximo + qtd - 1
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(qtd):
                num_str = f"{(inicio + i):08d}"
                zf.writestr(f"Etiqueta_{num_str}.png", gerar_etiqueta_img(num_str))
        
        supabase.table("registros_etiquetas").insert({"inicio": inicio, "fim": fim, "quantidade": qtd}).execute()
        st.success(f"✅ Lote {inicio:08d} a {fim:08d} salvo!")
        st.download_button("📥 Baixar ZIP", buf.getvalue(), f"lote_{inicio}.zip")

with tab2:
    texto_manual = st.text_input("Digite o código:", placeholder="Ex: ABC-123")
    if st.button("🎨 GERAR AVULSA"):
        if texto_manual:
            img_data = gerar_etiqueta_img(texto_manual)
            st.image(img_data, caption=f"Código: {texto_manual}")
            st.download_button("📥 Baixar PNG", img_data, f"etiqueta_{texto_manual}.png")

with tab3:
    st.write("Cole uma lista de códigos (um por linha):")
    lista_codigos = st.text_area("Área de colagem", height=200, help="Cole aqui seus 50 códigos vindos do Excel.")
    
    if st.button("📦 GERAR LOTE COLADO"):
        # Limpa a lista tirando espaços e linhas vazias
        codigos = [c.strip() for c in lista_codigos.split("\n") if c.strip()]
        
        if codigos:
            st.write(f"Processando **{len(codigos)}** etiquetas...")
            buf = BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                for cod in codigos:
                    zf.writestr(f"Etiqueta_{cod}.png", gerar_etiqueta_img(cod))
            
            st.success(f"✅ {len(codigos)} etiquetas prontas!")
            st.download_button("📥 Baixar Lote Colado (.ZIP)", buf.getvalue(), "lote_colado.zip")
        else:
            st.warning("⚠️ A lista está vazia!")

# Histórico
with st.expander("📊 Ver Histórico"):
    try:
        h = supabase.table("registros_etiquetas").select("*").order("id", desc=True).limit(5).execute()
        if h.data:
            st.table(pd.DataFrame(h.data)[['id', 'inicio', 'fim', 'quantidade']])
    except:
        st.write("Sem registros.")
