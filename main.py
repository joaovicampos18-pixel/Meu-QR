import streamlit as st
import qrcode
from io import BytesIO
import zipfile

# Configuração da página
st.set_page_config(page_title="Gerador QR Pro", page_icon="📟")

# Inicializa o contador na memória da sessão
if 'contador' not in st.session_state:
    st.session_state.contador = 0

st.title("📟 Gerador de QR Code Sequencial")
st.write("---")

# Mostra o status atual
proximo_inicio = st.session_state.contador + 1
st.write(f"### ➡️ Próximo número: `{{proximo_inicio:08d}}`")

# Entrada de quantidade
qtd = st.number_input("Quantas etiquetas gerar no lote?", min_value=1, max_value=1000, value=20, step=1)

# Botão de ação
if st.button(f"🚀 Gerar {{qtd}} Etiquetas agora"):
    zip_buffer = BytesIO()
    
    # Criamos o arquivo ZIP
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for i in range(qtd):
            # Cálculo preciso do número atual dentro do loop
            num_atual = proximo_inicio + i
            num_str = f"{{num_atual:08d}}" # Garante os 8 dígitos sempre
            
            # Gera o QR Code
            img = qrcode.make(num_str)
            
            # Salva a imagem em memória
            img_buffer = BytesIO()
            img.save(img_buffer, format="PNG")
            
            # Adiciona ao ZIP com nome organizado
            zip_file.writestr(f"QR_{{num_str}}.png", img_buffer.getvalue())
    
    # Só atualizamos o contador global DEPOIS de gerar tudo com sucesso
    st.session_state.contador += qtd
    
    # Prepara o download
    st.success(f"✅ Sucesso! Geradas {{qtd}} etiquetas (de {{proximo_inicio:08d}} até {{st.session_state.contador:08d}})")
    
    st.download_button(
        label="📩 BAIXAR ARQUIVO ZIP",
        data=zip_buffer.getvalue(),
        file_name=f"lote_{{proximo_inicio:08d}}_a_{{st.session_state.contador:08d}}.zip",
        mime="application/zip"
    )

st.write("---")
# Opção de reset/ajuste manual
with st.expander("🛠️ Ajuste Manual do Contador"):
    valor_manual = st.number_input("Mudar contador para:", min_value=0, value=st.session_state.contador)
    if st.button("Confirmar Alteração"):
        st.session_state.contador = valor_manual
        st.rerun()