import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 📌 URL du fichier IS.xlsx sur GitHub (Raw)
GITHUB_URL_IS = "https://raw.githubusercontent.com/Djoiusis/TAT-Salary/main/IS.xlsx"

# 📌 URL du logo (Raw)
GITHUB_LOGO_URL = "https://raw.githubusercontent.com/Djoiusis/TAT-Salary/main/LOGO-Talent-Access-Technologies-removebg.png"


# 📌 Charger les données Excel depuis GitHub
@st.cache_data
def charger_is_data():
    # Lire le fichier Excel
    df = pd.read_excel(GITHUB_URL_IS)
    
    # Nettoyer les colonnes "Année Min" et "Année Max" pour s'assurer qu'elles sont numériques
    for col in ["Année Min", "Année Max"]:
        if col in df.columns:
            # Remplacer les apostrophes et autres caractères non numériques
            df[col] = df[col].astype(str).str.replace("'", "").str.replace(" ", "").astype(float)
    
    # Afficher les données pour le débogage
    st.write("Aperçu des données IS:", df.head())
    
    return df

# 🌟 **Affichage du Logo Centré**
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="{GITHUB_LOGO_URL}" width="250">
    </div>
    """,
    unsafe_allow_html=True
)

# 📌 **Table des cotisations LPP**
LPP_TABLE = [
    (1, 25, 3.50, 0.70, 4.20),
    (2, 35, 5.00, 0.70, 5.70),
    (3, 45, 7.50, 1.20, 8.70),
    (4, 55, 9.00, 1.20, 10.20),
]

# 📌 **Fonction pour obtenir le taux IS**
def obtenir_taux_is(salaire_brut_annuel, statut_marital, is_df):
    # Débogage: afficher les paramètres
    st.write(f"Recherche de taux IS pour: Salaire={salaire_brut_annuel}, Statut={statut_marital}")
    
    # Vérifier si le DataFrame est vide ou si les colonnes nécessaires existent
    if is_df.empty or "Année Min" not in is_df.columns or "Année Max" not in is_df.columns:
        st.error("Données IS.xlsx invalides ou colonnes manquantes")
        return 0.0
    
    # Vérifier si le statut marital existe comme colonne
    if statut_marital not in is_df.columns:
        st.error(f"Statut marital '{statut_marital}' non trouvé dans les colonnes: {list(is_df.columns)}")
        return 0.0
    
    # Afficher les tranches disponibles pour débogage
    st.write("Tranches de salaire disponibles dans IS.xlsx:")
    st.write(is_df[["Année Min", "Année Max"]].head(10))
    
    # Filtrer la tranche salariale correspondante
    tranche = is_df[(is_df["Année Min"] <= salaire_brut_annuel) & (is_df["Année Max"] >= salaire_brut_annuel)]
    
    # Débogage: afficher les tranches trouvées
    st.write(f"Nombre de tranches trouvées: {len(tranche)}")
    if not tranche.empty:
        st.write("Tranche trouvée:", tranche[["Année Min", "Année Max", statut_marital]])
    else:
        st.warning(f"⚠️ Aucune tranche trouvée pour le salaire {salaire_brut_annuel} CHF")
        # Trouver la tranche maximale pour voir si notre salaire est au-dessus
        max_tranche = is_df["Année Max"].max()
        min_tranche = is_df["Année Min"].min()
        if salaire_brut_annuel > max_tranche:
            st.warning(f"Le salaire est supérieur à la tranche maximale ({max_tranche})")
        elif salaire_brut_annuel < min_tranche:
            st.warning(f"Le salaire est inférieur à la tranche minimale ({min_tranche})")
        return 0.0

    # Nettoyage et conversion du taux
    try:
        valeur = tranche[statut_marital].values[0]
        if pd.isna(valeur) or valeur == "_____":
            return 0.0
        
        valeur_str = str(valeur).replace(',', '.').strip()
        return float(valeur_str) / 100
    except (ValueError, IndexError) as e:
        st.error(f"Erreur lors de la lecture du taux IS: {e}")
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
        cotisations["Impôt Source"] = salaire_brut_mensuel * obtenir_taux_is(salaire_brut_annuel, statut_marital, is_df)
    
    total_deductions = sum(cotisations.values())
    salaire_net_mensuel = salaire_brut_mensuel - total_deductions

    return salaire_net_mensuel, salaire_brut_mensuel, cotisations

# 📌 **Chargement des données IS.xlsx**
is_df = charger_is_data()

# 📌 **Supprimer les colonnes inutiles**
colonnes_filtrees = [col for col in is_df.columns if col not in ["Mois Max", "Unnamed: 5", "Unnamed: 6"]]

# 📌 **Mise en page en deux colonnes avec espacement**
col1, col3, col2 = st.columns([1, 0.2, 1])  # La colonne 2 est plus étroite pour l'espacement
st.markdown("<br>", unsafe_allow_html=True)


# 🏦 **Colonne 1 : Calcul du Salaire Net**
with col1:
    st.header("💰 Calcul du Salaire Net")

    # **Entrées utilisateur**
    salaire_brut_annuel = st.number_input("💰 Salaire Brut Annuel (CHF)", min_value=0, value=160000)
    age = st.number_input("🎂 Âge", min_value=25, max_value=65, value=35)
    situation_familiale = st.selectbox("👨‍👩‍👧‍👦 Situation familiale", colonnes_filtrees[4:])

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
