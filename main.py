import streamlit as st
from streamlit_gsheets import GSheetsConnection
import qrcode
from io import BytesIO
import zipfile
from datetime import datetime
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Gerador QR Pro Sheets", page_icon="📊")

# 2. Conexão com o Google Sheets
# Importante: O link deve estar nos 'Secrets' do Streamlit
conn = st.connection("gsheets", type=GSheetsConnection)

def buscar_dados():
    try:
        # Lê a planilha e limpa o cache para garantir dados novos
        df = conn.read(ttl=0)
        return df
    except:
        return pd.DataFrame(columns=["Data", "Hora", "Inicio", "Fim", "Quantidade"])

# 3. Lógica do Contador
df_sheets = buscar_dados()

if not df_sheets.empty and 'Fim' in df_sheets.columns:
    try:
        ultimo_valor = int(pd.to_numeric(df_sheets['Fim']).max())
    except:
        ultimo_valor = 0
else:
    ultimo_valor = 0

proximo_inicio = ultimo_valor + 1

# --- INTERFACE ---
st.title("📟 Gerador de Etiquetas Profissional")
st.write("---")

aba1, aba2 = st.tabs(["📦 Gerar Lote", "📊 Histórico (Google Sheets)"])

with aba1:
    st.info(f"### ➡️ Próximo número: **{proximo_inicio:08d}**")
    
    qtd = st.number_input("Quantidade de etiquetas para o lote:", min_value=1, value=20, step=1)
    
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
            "Inicio": inicio_lote,
            "Fim": fim_lote,
            "Quantidade": qtd
        }])
        
        try:
            # Junta o que já existe com a nova linha
            df_atualizado = pd.concat([df_sheets, nova_linha], ignore_index=True)
            
            # Envia para o Google
            conn.update(data=df_atualizado)
            
            # Força o Streamlit a esquecer os dados antigos e ler a planilha nova
            st.cache_data.clear()
            
            st.success(f"✅ Lote {inicio_lote:08d} - {fim_lote:08d} gravado com sucesso!")
            
            # Botão de Download
            st.download_button(
                label="📥 BAIXAR ARQUIVO ZIP",
                data=buf_zip.getvalue(),
                file_name=f"lote_{inicio_lote:08d}.zip",
                mime="application/zip"
            )
            
            # Botão para atualizar a tela e mostrar o novo 'Próximo'
            if st.button("Atualizar para Próximo Número"):
                st.rerun()
                
        except Exception as e:
            st.error("Erro ao salvar! Verifique se a planilha está como 'Editor' para 'Qualquer pessoa com o link'.")
            st.code(str(e))

with aba2:
    st.subheader("📋 Últimos registros na Planilha")
    if not df_sheets.empty:
        st.dataframe(df_sheets.sort_index(ascending=False), use_container_width=True)
    else:
        st.write("Nenhum dado encontrado na planilha.")

    if st.button("🔄 Atualizar Dados agora"):
        st.cache_data.clear()
        st.rerun()
