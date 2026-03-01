import streamlit as st
from supabase import create_client
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import zipfile
import pandas as pd

# Configuração da Página
st.set_page_config(
    page_title="Gerador QR Pro - João Vitor",
    page_icon="📟",
    layout="wide"
)

# Estilo Customizado para o Rodapé
st.markdown("""
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f0f2f6;
        color: #31333F;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        font-weight: bold;
        border-top: 1px solid #e6e9ef;
    }
    </style>
    """, unsafe_allow_stats=True)

# Conexão com Supabase
@st.cache_resource
def conectar():
    try:
        url = st.secrets["SUPABASE_URL"].strip()
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except:
        return None

supabase = conectar()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/714/714390.png", width=100)
    st.title("Configurações")
    
    if supabase:
        st.success("✅ Banco de Dados Conectado")
    else:
        st.error("❌ Erro de Conexão")

    st.divider()
    st.subheader("📊 Últimos Registros")
    try:
        h = supabase.table("registros_etiquetas").select("*").order("id", desc=True).limit(5).execute()
        if h.data:
            df = pd.DataFrame(h.data)[['inicio', 'fim', 'quantidade']]
            st.dataframe(df, hide_index=True)
    except:
        st.write("Sem histórico disponível.")

# --- CORPO PRINCIPAL ---
st.title("📟 Gerador de Etiquetas Inteligente")
st.write("Crie QR Codes sequenciais ou manuais com salvamento automático.")

def buscar_ultimo():
    try:
        res = supabase.table("registros_etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
        return int(res.data[0]['fim']) if res.data else 0
    except:
        return 0

def gerar_etiqueta_img(conteudo):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(str(conteudo))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    w, h = qr_img.size
    canvas = Image.new('RGB', (w, h + 60), 'white')
    draw = ImageDraw.Draw(canvas)
    
    # Texto Centralizado no Topo
    texto = str(conteudo)
    draw.text((w/2 - 25, 15), texto, fill="black")
    canvas.paste(qr_img, (0, 50))
    
    img_io = BytesIO()
    canvas.save(img_io, format="PNG")
    return img_io.getvalue()

# Layout de Colunas para o Próximo Número
proximo = buscar_ultimo() + 1
col1, col2 = st.columns([1, 3])
with col1:
    st.metric(label="Próximo Código", value=f"{proximo:08d}")

# --- ABAS DE TRABALHO ---
tab_auto, tab_man, tab_list = st.tabs(["⚡ Automático", "🎯 Manual", "📋 Lista de Planilha"])

with tab_auto:
    st.subheader("Gerar Lote Sequencial")
    qtd = st.number_input("Quantas etiquetas deseja gerar?", min_value=1, max_value=500, value=10)
    
    if st.button("🚀 Iniciar Geração Automática", use_container_width=True):
        inicio, fim = proximo, proximo + qtd - 1
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(qtd):
                num_str = f"{(inicio + i):08d}"
                zf.writestr(f"Etiqueta_{num_str}.png", gerar_etiqueta_img(num_str))
        
        try:
            supabase.table("registros_etiquetas").insert({"inicio": inicio, "fim": fim, "quantidade": qtd}).execute()
            st.balloons()
            st.success(f"Lote {inicio:08d} até {fim:08d} gerado!")
            st.download_button("📥 Baixar Arquivo ZIP", buf.getvalue(), f"lote_{inicio}.zip", type="primary")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

with tab_man:
    st.subheader("Gerar Código Específico")
    texto_manual = st.text_input("Digite o código desejado (Letras ou Números):")
    if st.button("🎨 Gerar Etiqueta Única"):
        if texto_manual:
            img_data = gerar_etiqueta_img(texto_manual)
            st.image(img_data, width=200)
            st.download_button("📥 Baixar Imagem", img_data, f"etiqueta_{texto_manual}.png")

with tab_list:
    st.subheader("Importar do Excel/Bloco de Notas")
    lista_codigos = st.text_area("Cole aqui os códigos (um por linha):", height=250)
    if st.button("📦 Gerar Lote da Lista"):
        codigos = [c.strip() for c in lista_codigos.split("\n") if c.strip()]
        if codigos:
            buf = BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                for cod in codigos:
                    zf.writestr(f"Etiqueta_{cod}.png", gerar_etiqueta_img(cod))
            st.success(f"Foram processadas {len(codigos)} etiquetas.")
            st.download_button("📥 Baixar ZIP da Lista", buf.getvalue(), "lote_lista_personalizada.zip")

# RODAPÉ DE CRÉDITOS
st.markdown(f"""
    <div class="footer">
        Desenvolvido por João Vitor de Campos Leandro Silva | 2026
    </div>
    """, unsafe_allow_stats=True)
