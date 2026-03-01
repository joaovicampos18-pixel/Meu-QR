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
        z-index: 999;
    }
    </style>
    <div class="footer">
        Desenvolvido por João Vitor de Campos Leandro Silva | 2026
    </div>
    """, unsafe_allow_html=True)

# Conexão com Supabase (Removido cache_resource para garantir leitura atualizada)
def conectar():
    try:
        url = st.secrets["SUPABASE_URL"].strip()
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except:
        return None

supabase = conectar()

# --- FUNÇÕES ---
def buscar_ultimo():
    try:
        # Busca sempre o valor mais recente sem cache
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
    draw.text((w/2 - 30, 15), str(conteudo), fill="black")
    canvas.paste(qr_img, (0, 50))
    img_io = BytesIO()
    canvas.save(img_io, format="PNG")
    return img_io.getvalue()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ Configurações")
    if supabase:
        st.success("✅ Banco Conectado")
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
        st.write("Sem histórico.")

# --- CORPO PRINCIPAL ---
st.title("📟 Gerador de Etiquetas Profissional")

# Cálculo do próximo número
proximo = buscar_ultimo() + 1
st.metric(label="Próximo Código Sequencial", value=f"{proximo:08d}")

# --- ABAS ---
tab_auto, tab_man, tab_list = st.tabs(["⚡ Automático", "🎯 Manual", "📋 Colar Lista"])

with tab_auto:
    qtd = st.number_input("Quantidade:", min_value=1, max_value=500, value=10)
    
    # Usamos uma variável de estado para mostrar o download após o rerun
    if st.button("🚀 Iniciar Geração", use_container_width=True):
        inicio, fim = proximo, proximo + qtd - 1
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(qtd):
                num_str = f"{(inicio + i):08d}"
                zf.writestr(f"Etiqueta_{num_str}.png", gerar_etiqueta_img(num_str))
        
        try:
            # Grava no banco
            supabase.table("registros_etiquetas").insert({"inicio": inicio, "fim": fim, "quantidade": qtd}).execute()
            
            # Armazena o buffer temporariamente para download antes do reset
            st.session_state['file_ready'] = buf.getvalue()
            st.session_state['last_lot'] = f"{inicio:08d} a {fim:08d}"
            
            # Força o Streamlit a recarregar a página e ler o NOVO 'proximo'
            st.rerun()
            
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    # Exibe o botão de download se o lote foi gerado com sucesso
    if 'file_ready' in st.session_state:
        st.success(f"✅ Lote {st.session_state['last_lot']} salvo com sucesso!")
        st.download_button(
            label="📥 Baixar Arquivo ZIP",
            data=st.session_state['file_ready'],
            file_name=f"lote_etiquetas.zip",
            mime="application/zip",
            type="primary"
        )
        # Limpa o estado para a próxima geração
        del st.session_state['file_ready']

with tab_man:
    texto_manual = st.text_input("Digite o código manual:")
    if st.button("🎨 Gerar Única"):
        if texto_manual:
            img_data = gerar_etiqueta_img(texto_manual)
            st.image(img_data, width=200)
            st.download_button("📥 Baixar PNG", img_data, f"etiqueta_{texto_manual}.png")

with tab_list:
    lista_codigos = st.text_area("Cole os códigos (um por linha):", height=200)
    if st.button("📦 Gerar Lote da Lista"):
        codigos = [c.strip() for c in lista_codigos.split("\n") if c.strip()]
        if codigos:
            buf = BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                for cod in codigos:
                    zf.writestr(f"Etiqueta_{cod}.png", gerar_etiqueta_img(cod))
            st.download_button("📥 Baixar ZIP da Lista", buf.getvalue(), "lista_personalizada.zip")
