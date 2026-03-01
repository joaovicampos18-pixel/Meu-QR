import streamlit as st
import qrcode
from io import BytesIO
import zipfile

# Configurações iniciais
st.set_page_config(page_title="Gerador QR Pro", page_icon="📟")
st.title("📟 Sistema de Etiquetas")

# Memória do contador (Persiste na sessão)
if 'contador' not in st.session_state:
    st.session_state.contador = 0

proximo_sequencial = st.session_state.contador + 1

# --- INTERFACE POR ABAS ---
aba1, aba2, aba3 = st.tabs(["📦 Lote Sequencial", "🎯 Número Específico", "⚙️ Ajustes"])

with aba1:
    st.write(f"### Próximo na sequência: **{proximo_sequencial:08d}**")
    qtd_lote = st.number_input("Quantas etiquetas gerar no lote?", min_value=1, value=20, step=1, key="lote_input")
    
    if st.button(f"Gerar Lote de {qtd_lote}"):
        buf_lote = BytesIO()
        with zipfile.ZipFile(buf_lote, "w") as zf:
            for i in range(qtd_lote):
                val = proximo_sequencial + i
                txt = f"{val:08d}"
                img = qrcode.make(txt)
                img_io = BytesIO()
                img.save(img_io, format="PNG")
                zf.writestr(f"QR_{txt}.png", img_io.getvalue())
        
        st.session_state.contador += qtd_lote
        st.success(f"Lote {proximo_sequencial:08d} até {st.session_state.contador:08d} pronto!")
        st.download_button("📥 BAIXAR ZIP DO LOTE", buf_lote.getvalue(), f"lote_{proximo_sequencial:08d}.zip", "application/zip")

with aba2:
    st.write("### Gerar uma etiqueta avulsa")
    num_manual = st.number_input("Digite o número da etiqueta:", min_value=0, value=proximo_sequencial, step=1, key="manual_input")
    
    if st.button("Gerar Etiqueta Manual"):
        txt_m = f"{num_manual:08d}"
        img_m = qrcode.make(txt_m)
        buf_m = BytesIO()
        img_m.save(buf_m, format="PNG")
        
        # Mostra a imagem na tela antes de baixar
        st.image(buf_m.getvalue(), caption=f"Etiqueta {txt_m}", width=200)
        
        st.download_button(
            label="💾 BAIXAR IMAGEM (PNG)",
            data=buf_m.getvalue(),
            file_name=f"QR_{txt_m}.png",
            mime="image/png"
        )
        
        # Opção extra: Se o usuário quiser que a sequência continue desse número manual
        if st.checkbox("Atualizar sequência automática a partir deste número?"):
            st.session_state.contador = num_manual
            st.info(f"O próximo sequencial agora será o {num_manual + 1:08d}")

with aba3:
    st.write("### Gerenciar Memória")
    novo_valor = st.number_input("Resetar contador para:", min_value=0, value=st.session_state.contador)
    if st.button("Salvar Alteração"):
        st.session_state.contador = novo_valor
        st.rerun()

