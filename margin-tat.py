import streamlit as st

# 🌟 **Affichage du Logo Centré**
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/Djoiusis/TAT-Salary/main/LOGO-Talent-Access-Technologies-removebg.png" width="250">
    </div>
    """,
    unsafe_allow_html=True
)

st.title("📈 Calcul de la Marge & TJM Minimum")

# **Entrées utilisateur**
tjm_client = st.number_input("💰 TJM Client (CHF)", min_value=0, value=800)
jours_travailles = st.number_input("📅 Nombre de jours travaillés par mois", min_value=1, max_value=30, value=20)
salaire_brut_annuel = st.number_input("💰 Salaire Brut Annuel (CHF)", min_value=0, value=160000)

# **Bouton de calcul du TJM**
if st.button("📈 Calculer TJM Minimum"):
    if salaire_brut_annuel > 0:
        salaire_brut_mensuel = salaire_brut_annuel / 12
        revenus_mensuels = tjm_client * jours_travailles
        tjm_minimum = (salaire_brut_mensuel / 0.7) / jours_travailles  # Marge de 30%
        marge_actuelle = (revenus_mensuels - salaire_brut_mensuel) / revenus_mensuels * 100

        st.write(f"### 📉 Marge Actuelle : {marge_actuelle:.2f} %")
        st.write(f"### ⚠️ TJM Minimum à respecter pour 30% de marge : {tjm_minimum:.2f} CHF")

        if tjm_client >= tjm_minimum:
            st.success("✅ Votre TJM couvre la marge requise de 30%")
        else:
            st.warning("⚠️ Votre TJM est trop bas pour assurer une marge de 30%")
    else:
        st.warning("⚠️ Veuillez d'abord entrer un salaire brut annuel valide.")
