import streamlit as st
from supabase import create_client
import qrcode
from io import BytesIO
import zipfile
import pandas as pd

st.set_page_config(page_title="Gerador QR Pro", page_icon="📟")

# Conexão com o Banco
@st.cache_resource
def conectar():
    url = st.secrets["SUPABASE_URL"].strip()
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

try:
    supabase = conectar()
except Exception as e:
    st.error("Erro nos Secrets! Verifique a URL e a KEY.")
    st.stop()

st.title("📟 Gerador de Etiquetas Profissional")

# Busca o último número gravado para não repetir
def buscar_ultimo():
    try:
        res = supabase.table("etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
        return int(res.data[0]['fim']) if res.data else 0
    except:
        return 0

proximo = buscar_ultimo() + 1
st.info(f"### ➡️ Próximo número: **{proximo:08d}**")

# Interface
qtd = st.number_input("Quantas etiquetas gerar?", min_value=1, value=20)

if st.button("🚀 GERAR E SALVAR NO BANCO"):
    inicio, fim = proximo, proximo + qtd - 1
    
    # Criar o arquivo ZIP com as imagens
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(qtd):
            num = f"{(inicio + i):08d}"
            img = qrcode.make(num)
            img_io = BytesIO()
            img.save(img_io, format="PNG")
            zf.writestr(f"QR_{num}.png", img_io.getvalue())
    
    # Salvar o registro no Supabase
    try:
        supabase.table("etiquetas").insert({
            "inicio": inicio, 
            "fim": fim, 
            "quantidade": qtd
        }).execute()
        
        st.success(f"✅ Lote {inicio:08d} a {fim:08d} salvo!")
        st.download_button("📥 BAIXAR ETIQUETAS (ZIP)", buf.getvalue(), f"lote_{inicio}.zip")
        
        if st.button("Atualizar"):
            st.rerun()
    except Exception as e:
        st.error(f"Erro ao gravar: {e}")

# Histórico Visual
with st.expander("📊 Ver Histórico de Onde Parei"):
    try:
        h = supabase.table("etiquetas").select("*").order("id", desc=True).limit(10).execute()
        if h.data:
            st.table(pd.DataFrame(h.data)[['id', 'inicio', 'fim', 'quantidade']])
    except:
        st.write("Banco de dados ainda vazio.")
