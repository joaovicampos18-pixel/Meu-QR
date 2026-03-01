import streamlit as st
import qrcode
from io import BytesIO
import zipfile
import os

# --- FUNÇÕES DE BANCO DE DADOS (ARQUIVO LOCAL) ---
ARQUIVO_MEMORIA = "ultimo_numero.txt"

def ler_ultimo_numero():
    if os.path.exists(ARQUIVO_MEMORIA):
        with open(ARQUIVO_MEMORIA, "r") as f:
            try:
                return int(f.read().strip())
            except:
                return 0
    return 0

def salvar_ultimo_numero(n):
    with open(ARQUIVO_MEMORIA, "w") as f:
        f.write(str(n))

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="QR Pro Persistente", page_icon="💾")
st.title("📟 Sistema de Etiquetas")

# Inicializa o contador pegando do arquivo físico
if 'contador' not in st.session_state:
    st.session_state.contador = ler_ultimo_numero()

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
        
        # ATUALIZA SESSÃO E ARQUIVO FÍSICO
        novo_ultimo = proximo_sequencial + qtd_lote - 1
        st.session_state.contador = novo_ultimo
        salvar_ultimo_numero(novo_ultimo)
        
        st.success(f"Lote salvo! Próximo agora é {(novo_ultimo + 1):08d}")
        st.download_button("📥 BAIXAR ZIP DO LOTE", buf_lote.getvalue(), f"lote_{proximo_sequencial:08d}.zip", "application/zip")

with aba2:
    st.write("### Gerar uma etiqueta avulsa")
    num_manual = st.number_input("Digite o número da etiqueta:", min_value=0, value=proximo_sequencial, step=1, key="manual_input")
    
    if st.button("Gerar Etiqueta Manual"):
        txt_m = f"{num_manual:08d}"
        img_m = qrcode.make(txt_m)
        buf_m = BytesIO()
        img_m.save(buf_m, format="PNG")
        
        st.image(buf_m.getvalue(), caption=f"Etiqueta {txt_m}", width=200)
        st.download_button("💾 BAIXAR PNG", buf_m.getvalue(), f"QR_{txt_m}.png", "image/png")
        
        if st.checkbox("Atualizar sequência a partir deste número?"):
            st.session_state.contador = num_manual
            salvar_ultimo_numero(num_manual)
            st.info("Sequência atualizada!")

with aba3:
    st.write("### Gerenciar Memória Permanente")
    st.info(f"O número salvo no banco de dados é: {ler_ultimo_numero():08d}")
    
    novo_valor = st.number_input("Resetar banco para:", min_value=0, value=st.session_state.contador)
    if st.button("Confirmar e Salvar no Banco"):
        st.session_state.contador = novo_valor
        salvar_ultimo_numero(novo_valor)
        st.success("Banco de dados atualizado!")
        st.rerun()
