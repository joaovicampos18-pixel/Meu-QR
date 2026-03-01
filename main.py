import streamlit as st
import qrcode
from io import BytesIO
import zipfile

st.set_page_config(page_title="Gerador de Lote QR", page_icon="📟")
st.title("📟 Gerador de Etiquetas")

if 'contador' not in st.session_state:
    st.session_state.contador = 0

proximo = st.session_state.contador + 1
st.write(f"### Próximo número: **{proximo:08d}**")

# Campo de quantidade
qtd_pedida = st.number_input("Quantas etiquetas gerar?", min_value=1, max_value=500, value=20, step=1)

if st.button(f"GERAR {qtd_pedida} ETIQUETAS"):
    # 1. Criar as imagens primeiro (Garante que todas existam)
    lista_de_qrs = []
    for i in range(qtd_pedida):
        valor_atual = proximo + i
        texto = f"{valor_atual:08d}"
        
        img = qrcode.make(texto)
        img_io = BytesIO()
        img.save(img_io, format="PNG")
        
        # Guardamos o nome e o conteúdo na lista
        lista_de_qrs.append({
            "nome": f"QR_{texto}.png",
            "conteudo": img_io.getvalue()
        })

    # 2. Criar o ZIP a partir da lista pronta
    buf_final = BytesIO()
    with zipfile.ZipFile(buf_final, "w") as zf:
        for item in lista_de_qrs:
            zf.writestr(item["nome"], item["conteudo"])
    
    # 3. Atualizar contador
    st.session_state.contador += qtd_pedida
    
    st.success(f"✅ {len(lista_de_qrs)} imagens prontas no pacote!")
    
    # 4. Download forçado
    st.download_button(
        label="📥 BAIXAR PACOTE COMPLETO (.ZIP)",
        data=buf_final.getvalue(),
        file_name=f"lote_{proximo:08d}.zip",
        mime="application/zip"
    )

if st.button("Resetar"):
    st.session_state.contador = 0
    st.rerun()