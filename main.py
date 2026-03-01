import streamlit as st
from supabase import create_client, Client
import qrcode
from io import BytesIO
import zipfile
import pandas as pd

# Conexão com Supabase usando seus Secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Erro: Configure as chaves no Secrets do Streamlit!")
    st.stop()

st.set_page_config(page_title="Gerador QR Pro", page_icon="📟")
st.title("📟 Gerador de Etiquetas")

# Busca o último número gravado
def get_ultimo_registro():
    try:
        response = supabase.table("etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
        if response.data:
            return int(response.data[0]['fim'])
    except Exception:
        return 0
    return 0

ultimo_fim = get_ultimo_registro()
proximo = ultimo_fim + 1

st.info(f"### ➡️ Próximo número disponível: **{proximo:08d}**")

# --- INTERFACE ---
aba1, aba2 = st.tabs(["📦 Gerar Lote", "📜 Histórico"])

with aba1:
    qtd = st.number_input("Quantas etiquetas gerar?", min_value=1, value=20, step=1)
    
    if st.button("🚀 GERAR E SALVAR"):
        inicio_lote = proximo
        fim_lote = proximo + qtd - 1
        
        # Gerar ZIP
        buf_zip = BytesIO()
        with zipfile.ZipFile(buf_zip, "w") as zf:
            for i in range(qtd):
                num_str = f"{(inicio_lote + i):08d}"
                img = qrcode.make(num_str)
                img_io = BytesIO()
                img.save(img_io, format="PNG")
                zf.writestr(f"QR_{num_str}.png", img_io.getvalue())
        
        # SALVAR NO BANCO
        try:
            supabase.table("etiquetas").insert({
                "inicio": inicio_lote,
                "fim": fim_lote,
                "quantidade": qtd
            }).execute()
            
            st.success(f"✅ Salvo! Lote {inicio_lote:08d} a {fim_lote:08d}")
            st.download_button("📥 BAIXAR ZIP", buf_zip.getvalue(), f"lote_{inicio_lote:08d}.zip")
            
        except Exception as e:
            st.error("Erro ao salvar no banco. Verifique se a tabela 'etiquetas' foi criada e o RLS está desativado.")

with aba2:
    st.subheader("📋 Últimos Registros")
    try:
        hist = supabase.table("etiquetas").select("*").order("id", desc=True).limit(10).execute()
        if hist.data:
            st.table(pd.DataFrame(hist.data)[['id', 'inicio', 'fim', 'quantidade']])
    except:
        st.write("Sem registros no momento.")

if st.button("🔄 Atualizar"):
    st.rerun()
