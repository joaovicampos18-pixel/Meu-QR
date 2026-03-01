import streamlit as st
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO
import zipfile
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Gerador QR Pro", page_icon="📊")

# Conexão
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler dados com tratamento de erro
def buscar_dados():
    try:
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["Data", "Hora", "Inicio", "Fim", "Quantidade"])
        return df
    except:
        return pd.DataFrame(columns=["Data", "Hora", "Inicio", "Fim", "Quantidade"])

df_sheets = buscar_dados()

# Cálculo do contador
try:
    # Garante que as colunas existam antes de calcular o máximo
    if "Fim" in df_sheets.columns:
        ultimo_valor = int(pd.to_numeric(df_sheets["Fim"]).max())
    else:
        ultimo_valor = 0
except:
    ultimo_valor = 0

proximo_inicio = ultimo_valor + 1

st.title("📟 Gerador de Etiquetas")
st.info(f"### ➡️ Próximo número: **{proximo_inicio:08d}**")

qtd = st.number_input("Quantidade:", min_value=1, value=10, step=1)

if st.button("🚀 GERAR E SALVAR"):
    inicio_lote = proximo_inicio
    fim_lote = proximo_inicio + qtd - 1
    
    # Gerar ZIP
    buf_zip = BytesIO()
    with zipfile.ZipFile(buf_zip, "w") as zf:
        for i in range(qtd):
            num_str = f"{(inicio_lote + i):08d}"
            img = qrcode.make(num_str)
            img_io = BytesIO()
            img.save(img_io, format="PNG")
            zf.writestr(f"QR_{num_str}.png", img_io.getvalue())
    
    # Criar nova linha
    nova_linha = pd.DataFrame([{
        "Data": datetime.now().strftime('%d/%m/%Y'),
        "Hora": datetime.now().strftime('%H:%M:%S'),
        "Inicio": int(inicio_lote),
        "Fim": int(fim_lote),
        "Quantidade": int(qtd)
    }])
    
    try:
        # IMPORTANTE: Re-organiza as colunas para bater com a planilha
        df_para_salvar = pd.concat([df_sheets, nova_linha], ignore_index=True)
        df_para_salvar = df_para_salvar[["Data", "Hora", "Inicio", "Fim", "Quantidade"]]
        
        # Envia para o Google
        conn.update(data=df_para_salvar)
        
        st.cache_data.clear()
        st.success("✅ Salvo com sucesso no Google Sheets!")
        
        st.download_button(
            label="📥 BAIXAR ZIP",
            data=buf_zip.getvalue(),
            file_name=f"lote_{inicio_lote:08d}.zip",
            mime="application/zip"
        )
    except Exception as e:
        st.error("Erro técnico na gravação.")
        # Isso vai mostrar o erro real do Google para sabermos o que é
        st.exception(e) 

if st.button("🔄 Sincronizar"):
    st.cache_data.clear()
    st.rerun()
