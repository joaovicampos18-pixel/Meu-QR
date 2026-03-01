import streamlit as st
from supabase import create_client, Client
import qrcode
from io import BytesIO
import zipfile
import pandas as pd

# Conexão segura com Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("Erro na conexão! Verifique os Secrets.")
    st.stop()

st.title("📟 Gerador de Etiquetas Profissional")

# Busca o último número
def buscar_ultimo():
    try:
        res = supabase.table("etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
        if res.data:
            return int(res.data[0]['fim'])
    except:
        return 0
    return 0

proximo = buscar_ultimo() + 1
st.info(f"### ➡️ Próximo número: **{proximo:08d}**")

qtd = st.number_input("Quantidade:", min_value=1, value=20)

if st.button("🚀 GERAR E SALVAR"):
    inicio = proximo
    fim = proximo + qtd - 1
    
    # Gerar ZIP
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(qtd):
            num = f"{(inicio + i):08d}"
            img = qrcode.make(num)
            img_io = BytesIO()
            img.save(img_io, format="PNG")
            zf.writestr(f"QR_{num}.png", img_io.getvalue())
    
    # Salvar no Banco
    try:
        supabase.table("etiquetas").insert({
            "inicio": inicio,
            "fim": fim,
            "quantidade": qtd
        }).execute()
        
        st.success(f"✅ Salvo! Lote {inicio:08d} a {fim:08d}")
        st.download_button("📥 Baixar ZIP", buf.getvalue(), f"lote_{inicio}.zip")
    except Exception as e:
        st.error("Erro ao gravar. Verifique se rodou o comando no SQL Editor.")
        st.code(e)

# Histórico
with st.expander("📊 Ver Histórico"):
    try:
        dados = supabase.table("etiquetas").select("*").order("id", desc=True).limit(10).execute()
        if dados.data:
            st.dataframe(pd.DataFrame(dados.data)[['id', 'inicio', 'fim', 'quantidade']])
    except:
        st.write("Banco ainda vazio.")
