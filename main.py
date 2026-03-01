import streamlit as st
from supabase import create_client
import qrcode
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
    st.error("🚨 Verifique as chaves nos Secrets do Streamlit!")
    st.stop()

st.title("📟 Gerador de Etiquetas")

# Busca o último número na tabela 'registros_etiquetas'
def buscar_ultimo():
    try:
        res = supabase.table("registros_etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
        return int(res.data[0]['fim']) if res.data else 0
    except Exception as e:
        st.warning(f"Aguardando primeira gravação ou erro: {e}")
        return 0

proximo = buscar_ultimo() + 1
st.info(f"### ➡️ Próximo número: **{proximo:08d}**")

qtd = st.number_input("Quantidade de etiquetas:", min_value=1, value=10)

if st.button("🚀 GERAR E SALVAR"):
    inicio, fim = proximo, proximo + qtd - 1
    
    # Gerar ZIP
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(qtd):
            num_str = f"{(inicio + i):08d}"
            img = qrcode.make(num_str)
            img_io = BytesIO()
            img.save(img_io, format="PNG")
            zf.writestr(f"QR_{num_str}.png", img_io.getvalue())
    
    # Salvar
    try:
        supabase.table("registros_etiquetas").insert({
            "inicio": inicio,
            "fim": fim,
            "quantidade": qtd
        }).execute()
        
        st.success(f"✅ Sucesso! Lote {inicio:08d} a {fim:08d}")
        st.download_button("📥 Baixar Etiquetas (.ZIP)", buf.getvalue(), f"lote_{inicio}.zip")
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# Histórico
with st.expander("📊 Ver Histórico"):
    try:
        h = supabase.table("registros_etiquetas").select("*").order("id", desc=True).limit(5).execute()
        if h.data:
            st.table(pd.DataFrame(h.data)[['id', 'inicio', 'fim', 'quantidade']])
    except:
        st.write("Sem registros.")
