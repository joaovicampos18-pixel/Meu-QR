import streamlit as st
from supabase import create_client, Client
import qrcode
from io import BytesIO
import zipfile
import pandas as pd

# 1. Conexão com Supabase usando seus Secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("🚨 Erro: Chaves de API não encontradas nos Secrets do Streamlit!")
    st.stop()

st.set_page_config(page_title="Gerador QR Pro", page_icon="📟", layout="centered")
st.title("📟 Gerador de Etiquetas")
st.write("---")

# 2. Função para buscar o último número gravado
def get_ultimo_registro():
    try:
        # Busca o maior valor da coluna 'fim' na tabela 'etiquetas'
        response = supabase.table("etiquetas").select("fim").order("fim", desc=True).limit(1).execute()
        if response.data and len(response.data) > 0:
            return int(response.data[0]['fim'])
    except Exception as e:
        # Se a tabela não existir ou estiver inacessível, retorna 0
        return 0
    return 0

ultimo_fim = get_ultimo_registro()
proximo = ultimo_fim + 1

# Exibição do contador atual
st.info(f"### ➡️ Próximo número disponível: **{proximo:08d}**")

# --- INTERFACE POR ABAS ---
aba1, aba2 = st.tabs(["📦 Gerar Lote", "📜 Histórico de Lotes"])

with aba1:
    qtd = st.number_input("Quantas etiquetas deseja gerar neste lote?", min_value=1, value=20, step=1)
    
    if st.button("🚀 GERAR E SALVAR NO BANCO"):
        inicio_lote = proximo
        fim_lote = proximo + qtd - 1
        
        # --- GERAÇÃO DOS QR CODES ---
        buf_zip = BytesIO()
        with zipfile.ZipFile(buf_zip, "w") as zf:
            for i in range(qtd):
                num_atual = inicio_lote + i
                num_str = f"{num_atual:08d}"
                
                img = qrcode.make(num_str)
                img_io = BytesIO()
                img.save(img_io, format="PNG")
                zf.writestr(f"QR_{num_str}.png", img_io.getvalue())
        
        # --- SALVAMENTO NO SUPABASE ---
        try:
            # Tenta inserir os dados na tabela
            dados_lote = {
                "inicio": int(inicio_lote),
                "fim": int(fim_lote),
                "quantidade": int(qtd)
            }
            
            supabase.table("etiquetas").insert(dados_lote).execute()
            
            st.success(f"✅ Lote {inicio_lote:08d} até {fim_lote:08d} salvo com sucesso!")
            
            # Botão para baixar o arquivo gerado
            st.download_button(
                label="📥 BAIXAR ETIQUETAS (.ZIP)",
                data=buf_zip.getvalue(),
                file_name=f"lote_{inicio_lote:08d}_{fim_lote:08d}.zip",
                mime="application/zip"
            )
            
            # Botão para recarregar a página e atualizar o contador
            if st.button("Atualizar para o Próximo Número"):
                st.rerun()
                
        except Exception as e:
            st.error("❌ Erro ao salvar no banco de dados!")
            st.warning("Verifique se a tabela 'etiquetas' existe e se o RLS foi desativado no SQL Editor.")
            st.code(str(e))

with aba2:
    st.subheader("📋 Histórico dos Últimos Lotes")
    try:
        # Busca os últimos 15 registros
        hist = supabase.table("etiquetas").select("*").order("id", desc=True).limit(15).execute()
        if hist.data:
            df_hist = pd.DataFrame(hist.data)
            # Reorganiza as colunas para ficar bonito
            colunas_exibir = ['id', 'inicio', 'fim', 'quantidade']
            st.dataframe(df_hist[colunas_exibir], use_container_width=True)
        else:
            st.write("Nenhum lote foi gerado ainda.")
    except Exception:
        st.write("Aguardando o primeiro registro ser criado...")

# Rodapé simples
st.write("---")
if st.button("🔄 Sincronizar Banco"):
    st.cache_data.clear()
    st.rerun()
