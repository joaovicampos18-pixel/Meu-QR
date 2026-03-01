import streamlit as st
from supabase import create_client, Client
import qrcode
from io import BytesIO
import zipfile
import pandas as pd

st.set_page_config(page_title="Gerador QR Pro", page_icon="📟")

# Função para conectar com tratamento de erro real
def conectar_banco():
    try:
        url = st.secrets["SUPABASE_URL"].strip()
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro nos Secrets: {e}")
        return None

supabase = conectar_banco()

st.title("📟 Gerador de Etiquetas")

if supabase:
    # Busca o último número
    def buscar_ultimo():
        try:
            res = supabase.table("etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
            if res.data:
                return int(res.data[0]['fim'])
        except Exception as e:
            if "401" in str(e):
                st.error("🔑 Chave Inválida (Erro 401). Verifique se copiou a 'anon public' inteira!")
            return 0
        return 0

    ultimo_numero = buscar_ultimo()
    proximo = ultimo_numero + 1

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
        
        # Salvar no Banco
        try:
            supabase.table("etiquetas").insert({
                "inicio": inicio,
                "fim": fim,
                "quantidade": qtd
            }).execute()
            
            st.success(f"✅ Salvo Lote {inicio:08d} a {fim:08d}!")
            st.download_button("📥 Baixar ZIP", buf.getvalue(), f"lote_{inicio}.zip")
        except Exception as e:
            st.error("❌ Erro ao salvar. Verifique se rodou o comando SQL no Supabase.")
            st.code(str(e))

    # Histórico
    with st.expander("📊 Histórico"):
        try:
            dados = supabase.table("etiquetas").select("*").order("id", desc=True).limit(5).execute()
            if dados.data:
                st.table(pd.DataFrame(dados.data)[['id', 'inicio', 'fim', 'quantidade']])
        except:
            st.write("Sem registros.")
