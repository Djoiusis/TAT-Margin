import streamlit as st

# 🌟 **Affichage du Logo Centré**
GITHUB_LOGO_URL = "https://raw.githubusercontent.com/Djoiusis/TAT-Salary/main/LOGO-Talent-Access-Technologies-removebg.png"
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="{GITHUB_LOGO_URL}" width="250">
    </div>
    """,
    unsafe_allow_html=True
)

# **🔹 Interface de Calcul de la Marge & TJM Minimum**
st.title("📊 Calcul de la Marge & TJM Minimum")

# **🔹 Entrées utilisateur**
tjm_client = st.number_input("💰 TJM Client (CHF)", min_value=0, value=800)
jours_travailles = st.number_input("📅 Nombre de jours travaillés par mois", min_value=1, max_value=30, value=20)
salaire_brut_annuel = st.number_input("💰 Salaire Brut Annuel (CHF)", min_value=0, value=160000)

# **Choix de la marge minimale souhaitée**
marge_minimale = st.slider("📈 Marge minimale souhaitée (%)", min_value=10, max_value=60, value=30, step=5)

# **Bouton de calcul du TJM**
if st.button("📈 Calculer TJM Minimum"):
    if salaire_brut_annuel > 0:
        salaire_brut_mensuel = salaire_brut_annuel / 12
        revenus_mensuels = tjm_client * jours_travailles
        tjm_minimum = (salaire_brut_mensuel / (1 - (marge_minimale / 100))) / jours_travailles  # Ajustement de la marge
        marge_actuelle = ((revenus_mensuels - salaire_brut_mensuel) / revenus_mensuels) * 100

        # **Affichage des résultats**
        st.write(f"### 📉 Marge Actuelle : {marge_actuelle:.2f} %")
        st.write(f"### ⚠️ TJM Minimum à respecter pour {marge_minimale}% de marge : {tjm_minimum:.2f} CHF")

        if tjm_client >= tjm_minimum:
            st.success(f"✅ Votre TJM couvre la marge requise de {marge_minimale}%")
        else:
            st.warning(f"⚠️ Votre TJM est trop bas pour assurer une marge de {marge_minimale}%")
    else:
        st.warning("⚠️ Veuillez d'abord entrer un salaire brut annuel avant d'estimer la marge.")
