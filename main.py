import streamlit as st
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO
import zipfile
from datetime import datetime
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Gerador QR Pro", page_icon="📊")

# 2. Conexão com o Google Sheets
# O link deve estar configurado no menu 'Secrets' do Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def buscar_dados():
    try:
        # ttl=0 garante que ele não use dados antigos (cache)
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["Data", "Hora", "Inicio", "Fim", "Quantidade"])
        return df
    except Exception:
        # Se a planilha estiver vazia ou inacessível, cria a estrutura básica
        return pd.DataFrame(columns=["Data", "Hora", "Inicio", "Fim", "Quantidade"])

# 3. Lógica do Contador (Lê o maior número da coluna 'Fim')
df_sheets = buscar_dados()

try:
    if not df_sheets.empty and "Fim" in df_sheets.columns:
        ultimo_valor = int(pd.to_numeric(df_sheets["Fim"]).max())
    else:
        ultimo_valor = 0
except:
    ultimo_valor = 0

proximo_inicio = ultimo_valor + 1

# --- INTERFACE ---
st.title("📟 Gerador de Etiquetas")
st.write("---")

aba1, aba2 = st.tabs(["📦 Gerar Lote", "📊 Histórico Google Sheets"])

with aba1:
    st.info(f"### ➡️ Próximo número: **{proximo_inicio:08d}**")
    
    qtd = st.number_input("Quantidade para o lote:", min_value=1, value=20, step=1)
    
    if st.button("🚀 GERAR E SALVAR NA PLANILHA"):
        inicio_lote = proximo_inicio
        fim_lote = proximo_inicio + qtd - 1
        
        # --- GERAÇÃO DO ZIP ---
        buf_zip = BytesIO()
        with zipfile.ZipFile(buf_zip, "w") as zf:
            for i in range(qtd):
                num_atual = inicio_lote + i
                txt_qr = f"{num_atual:08d}"
                
                img = qrcode.make(txt_qr)
                img_io = BytesIO()
                img.save(img_io, format="PNG")
                zf.writestr(f"QR_{txt_qr}.png", img_io.getvalue())
        
        # --- SALVAR NO GOOGLE SHEETS ---
        nova_linha = pd.DataFrame([{
            "Data": datetime.now().strftime('%d/%m/%Y'),
            "Hora": datetime.now().strftime('%H:%M:%S'),
            "Inicio": int(inicio_lote),
            "Fim": int(fim_lote),
            "Quantidade": int(qtd)
        }])
        
        try:
            # Combina dados e atualiza planilha
            df_atualizado = pd.concat([df_sheets, nova_linha], ignore_index=True)
            conn.update(data=df_atualizado)
            
            # Limpa cache para atualizar o número na tela
            st.cache_data.clear()
            
            st.success(f"✅ Gravado: {inicio_lote:08d} a {fim_lote:08d}")
            
            st.download_button(
                label="📥 BAIXAR ETIQUETAS (.ZIP)",
                data=buf_zip.getvalue(),
                file_name=f"lote_{inicio_lote:08d}.zip",
                mime="application/zip"
            )
            
            # Botão invisível para forçar recarregamento
            st.button("🔄 Próxima Etiqueta")
                
        except Exception as e:
            st.error("Erro ao gravar. Verifique se a planilha está aberta para 'Editor'.")
            st.info("Dica: A primeira linha da planilha deve ter: Data, Hora, Inicio, Fim, Quantidade")

with aba2:
    st.subheader("📋 Dados na Planilha Online")
    if not df_sheets.empty:
        st.dataframe(df_sheets.sort_index(ascending=False), use_container_width=True)
    else:
        st.write("Planilha vazia ou não conectada.")
    
    if st.button("🔄 Sincronizar Agora"):
        st.cache_data.clear()
        st.rerun()
