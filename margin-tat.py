import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 📌 URL du fichier IS.xlsx sur GitHub (Raw)
GITHUB_URL_IS = "https://raw.githubusercontent.com/Djoiusis/TAT-Salary/main/IS.xlsx"

# 📌 URL du logo (Raw)
GITHUB_LOGO_URL = "https://raw.githubusercontent.com/Djoiusis/TAT-Salary/main/LOGO-Talent-Access-Technologies-removebg.png"

# Dictionnaire des taux fixes pour les salaires problématiques (célibataire sans enfant)
taux_fixes = {
    # Tranches 114'000 - 119'999
    114000: 0.1520, 115000: 0.1526, 116000: 0.1538, 117000: 0.1550, 118000: 0.1562, 119000: 0.1573,
    # Tranches 120'000 - 129'999
    120000: 0.1579, 121000: 0.1584, 122000: 0.1590, 123000: 0.1595, 124000: 0.1601, 
    125000: 0.1606, 126000: 0.1611, 127000: 0.1616, 128000: 0.1622, 129000: 0.1627,
    # Tranches 130'000 - 139'999
    130000: 0.1632, 131000: 0.1637, 132000: 0.1642, 133000: 0.1647, 134000: 0.1652,
    135000: 0.1656, 136000: 0.1661, 137000: 0.1666, 138000: 0.1671, 139000: 0.1676,
    # Tranches 140'000 - 144'000
    140000: 0.1680, 141000: 0.1685, 142000: 0.1690, 143000: 0.1695, 144000: 0.1700
}

# 📌 **Table des cotisations LPP**
LPP_TABLE = [
    (1, 25, 3.50, 0.70, 4.20),
    (2, 35, 5.00, 0.70, 5.70),
    (3, 45, 7.50, 1.20, 8.70),
    (4, 55, 9.00, 1.20, 10.20),
]

# 📌 Fonction pour nettoyer une valeur numérique
def nettoyer_nombre(valeur):
    if pd.isna(valeur) or valeur == "" or valeur == "_____":
        return 0.0
    
    valeur_str = str(valeur).replace("'", "").replace(" ", "").replace(",", ".")
    
    try:
        return float(valeur_str)
    except:
        return 0.0

# 📌 Charger les données Excel depuis GitHub
@st.cache_data
def charger_is_data():
    try:
        response = requests.get(GITHUB_URL_IS)
        excel_data = BytesIO(response.content)
        df = pd.read_excel(excel_data, dtype=str)
        
        # Nettoyer les colonnes numériques
        for col in ["Année Min", "Année Max"]:
            df[col] = df[col].apply(nettoyer_nombre)
        
        return df
    except:
        return pd.DataFrame()

# 📌 **Fonction pour obtenir le taux IS**
def obtenir_taux_is(salaire_brut_annuel, statut_marital, is_df):
    # Convertir en nombre
    salaire_brut_annuel = float(salaire_brut_annuel)
    
    # MÉTHODE 1: Utiliser les taux fixes pour les tranches problématiques
    # Arrondir le salaire au millier inférieur pour utiliser les taux fixes
    salaire_arrondi = (int(salaire_brut_annuel) // 1000) * 1000
    
    # Si c'est un célibataire et dans les tranches problématiques
    if 114000 <= salaire_arrondi <= 144000 and statut_marital == "Célibataire sans enfant":
        if salaire_arrondi in taux_fixes:
            return taux_fixes[salaire_arrondi]
    
    # MÉTHODE 2: Recherche standard dans le DataFrame
    for _, row in is_df.iterrows():
        min_val = row["Année Min"]
        max_val = row["Année Max"]
        
        if min_val <= salaire_brut_annuel <= max_val:
            if statut_marital in row:
                taux_str = str(row[statut_marital]).replace(',', '.').strip()
                try:
                    taux = float(taux_str) / 100
                    return taux
                except:
                    pass
    
    return 0.0

# 📌 **Fonction pour obtenir le taux LPP**
def obtenir_taux_lpp(age):
    for row in LPP_TABLE:
        if row[1] <= age < (row[1] + 10):
            return row[4] / 100
    return 0

# 📌 **Fonction principale de calcul du salaire net**
def calculer_salaire_net(salaire_brut_annuel, age, statut_marital, is_df, soumis_is):
    salaire_brut_mensuel = salaire_brut_annuel / 12
    taux_fixes = {
        "AVS": 5.3 / 100,
        "AC": 1.1 / 100,
        "AANP": 0.63 / 100,
        "Maternité": 0.032 / 100,
        "APG": 0.495 / 100,
    }
    
    cotisations = {key: salaire_brut_mensuel * taux for key, taux in taux_fixes.items()}
    cotisations["LPP"] = (salaire_brut_mensuel * obtenir_taux_lpp(age)) / 2

    # Appliquer l'IS seulement si soumis à l'impôt à la source
    cotisations["Impôt Source"] = 0
    if soumis_is:
        taux_is = obtenir_taux_is(salaire_brut_annuel, statut_marital, is_df)
        cotisations["Impôt Source"] = salaire_brut_mensuel * taux_is
    
    total_deductions = sum(cotisations.values())
    salaire_net_mensuel = salaire_brut_mensuel - total_deductions

    return salaire_net_mensuel, salaire_brut_mensuel, cotisations

# 🌟 **Affichage du Logo Centré**
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="{GITHUB_LOGO_URL}" width="250">
    </div>
    """,
    unsafe_allow_html=True
)

# Chargement des données
is_df = charger_is_data()

# Colonnes de statut marital
colonnes_techniques = ["INDEX", "Année Min", "Année Max", "Mois Min", "Mois Max"]
colonnes_statut_marital = [col for col in is_df.columns if col not in colonnes_techniques 
                           and not col.startswith("Unnamed:")]

# 📌 **Mise en page en deux colonnes avec espacement**
col1, col3, col2 = st.columns([1, 0.2, 1])  # La colonne 2 est plus étroite pour l'espacement
st.markdown("<br>", unsafe_allow_html=True)

# 🏦 **Colonne 1 : Calcul du Salaire Net**
with col1:
    st.header("💰 Calcul du Salaire Net")

    # **Entrées utilisateur**
    salaire_brut_annuel = st.number_input("💰 Salaire Brut Annuel (CHF)", min_value=0, value=160000)
    age = st.number_input("🎂 Âge", min_value=25, max_value=65, value=35)
    
    # Utiliser uniquement les colonnes de statut marital
    if colonnes_statut_marital:
        situation_familiale = st.selectbox("👨‍👩‍👧‍👦 Situation familiale", colonnes_statut_marital)
    else:
        situation_familiale = "Célibataire sans enfant"

    # **Sélection du statut de résidence**
    nationalite = st.radio("🌍 Statut de résidence", ["🇨🇭 Suisse", "🏷️ Permis C", "🌍 Autre (Imposé à la source)"])
    soumis_is = nationalite == "🌍 Autre (Imposé à la source)"

    # **Bouton de calcul**
    if st.button("🧮 Calculer Salaire"):
        salaire_net_mensuel, salaire_brut_mensuel, details_deductions = calculer_salaire_net(
            salaire_brut_annuel, age, situation_familiale, is_df, soumis_is
        )

        st.write(f"### 💰 Salaire Net Mensuel : {salaire_net_mensuel:.2f} CHF")
        st.write("### 📉 Détail des Déductions :")
        for key, value in details_deductions.items():
            st.write(f"- **{key}** : {value:.2f} CHF")

# 📈 **Colonne 2 : Calcul du TJM Minimum**
with col2:
    st.header("📊 Calcul du TJM Minimum")

    # **Entrées utilisateur pour la marge**
    tjm_client = st.number_input("💰 TJM Client (CHF)", min_value=0, value=800)
    jours_travailles = st.number_input("📅 Nombre de jours travaillés par mois", min_value=1, max_value=30, value=20)

    # **Choix de la marge minimale souhaitée**
    marge_minimale = st.slider("📈 Marge minimale souhaitée (%)", min_value=10, max_value=60, value=30, step=5)

    # **Bouton de calcul du TJM**
    if st.button("📈 Calculer TJM Minimum"):
        if salaire_brut_annuel > 0:
            revenus_annuel = tjm_client * 225
            tjm_minimum = (salaire_brut_annuel*1.14 / (1 - (marge_minimale / 100))) / 225  # Ajustement de la marge
            marge_actuelle = ((revenus_annuel - salaire_brut_annuel*1.14) / revenus_annuel) * 100

            # **Affichage des résultats**
            st.write(f"### 📉 Marge Actuelle : {marge_actuelle:.2f} %")
            st.write(f"### ⚠️ TJM Minimum à respecter pour {marge_minimale}% de marge : {tjm_minimum:.2f} CHF")

            if tjm_client >= tjm_minimum:
                st.success(f"✅ Votre TJM couvre la marge requise de {marge_minimale}%")
            else:
                st.warning(f"⚠️ Votre TJM est trop bas pour assurer une marge de {marge_minimale}%")
        else:
            st.warning("⚠️ Veuillez d'abord entrer un salaire brut annuel avant d'estimer la marge.")
