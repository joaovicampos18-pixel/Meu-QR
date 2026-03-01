import streamlit as st
import qrcode
from io import BytesIO
import zipfile

# Título da página
st.set_page_config(page_title="Gerador QR Pro", page_icon="📟")

# Inicializa o contador na memória da sessão (evita o erro de input)
if 'contador' not in st.session_state:
    st.session_state.contador = 0

st.title("📟 Gerador de QR Code Sequencial")
st.markdown("---")

# Mostra o status atual
proximo_disponivel = st.session_state.contador + 1
st.write(f"### ➡️ Próximo número: `{{proximo_disponivel:08d}}`")

# Interface do usuário (em vez de usar input())
col1, col2 = st.columns(2)

with col1:
    qtd = st.number_input("Quantas etiquetas?", min_value=1, max_value=500, value=10, step=1)

with col2:
    st.write(" ") # Espaçamento
    if st.button("🚀 Gerar e Baixar ZIP"):
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a") as zip_file:
            for i in range(qtd):
                num_atual = proximo_disponivel + i
                num_str = f"{{num_atual:08d}}"
                
                # Criação do QR
                img = qrcode.make(num_str)
                buf = BytesIO()
                img.save(buf, format="PNG")
                
                # Adiciona ao pacote
                zip_file.writestr(f"QR_{{num_str}}.png", buf.getvalue())
        
        # Atualiza a contagem para a próxima vez
        st.session_state.contador += qtd
        
        st.success(f"✅ Geradas {{qtd}} etiquetas!")
        st.download_button(
            label="📩 Clique para Baixar o ZIP",
            data=zip_buffer.getvalue(),
            file_name=f"lote_{{proximo_disponivel:08d}}.zip",
            mime="application/zip"
        )

st.markdown("---")
# Opção de resetar caso precise recomeçar
with st.expander("🛠️ Opções Avançadas"):
    novo_inicio = st.number_input("Ajustar contador para:", min_value=0, value=st.session_state.contador)
    if st.button("Salvar Novo Valor"):
        st.session_state.contador = novo_inicio
        st.rerun()