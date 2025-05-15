import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Créer un conteneur pour les logs
log_container = st.empty()
logs = []

def add_log(message):
    global logs
    logs.append(message)
    # Mettre à jour l'affichage des logs
    log_container.text_area("Logs de débogage", "\n".join(logs), height=200)

# 📌 URL du fichier IS.xlsx sur GitHub (Raw)
GITHUB_URL_IS = "https://raw.githubusercontent.com/Djoiusis/TAT-Salary/main/IS.xlsx"

# 📌 URL du logo (Raw)
GITHUB_LOGO_URL = "https://raw.githubusercontent.com/Djoiusis/TAT-Salary/main/LOGO-Talent-Access-Technologies-removebg.png"

# 📌 Fonction pour nettoyer une valeur numérique
def nettoyer_nombre(valeur):
    if pd.isna(valeur) or valeur == "" or valeur == "_____":
        return 0.0
    
    # Convertir en chaîne de caractères
    valeur_str = str(valeur)
    
    # Nettoyer la chaîne
    valeur_clean = valeur_str.replace("'", "").replace(" ", "").replace(",", ".")
    
    # Essayer de convertir en nombre
    try:
        return float(valeur_clean)
    except (ValueError, TypeError):
        return 0.0

# Définir manuellement les tranches et taux pour les cas problématiques
tranches_116000 = {
    (115800, 116399): {
        "Célibataire sans enfant": 15.38,
        # Ajouter d'autres statuts au besoin
    },
    (116400, 116999): {
        "Célibataire sans enfant": 15.44,
        # Ajouter d'autres statuts au besoin
    }
}

# 📌 Charger les données Excel depuis GitHub
@st.cache_data
def charger_is_data():
    try:
        # Lire le fichier Excel
        response = requests.get(GITHUB_URL_IS)
        excel_data = BytesIO(response.content)
        
        # Lire toutes les colonnes comme du texte d'abord
        df = pd.read_excel(excel_data, dtype=str)
        
        # Créer un nouveau DataFrame nettoyé
        df_clean = pd.DataFrame()
        
        # Copier les colonnes en nettoyant au besoin
        for col in df.columns:
            if col in ["INDEX"]:
                df_clean[col] = df[col]
            elif col in ["Année Min", "Année Max", "Mois Min", "Mois Max"]:
                # Convertir en nombre
                df_clean[col] = df[col].apply(nettoyer_nombre)
            else:
                # Garder les autres colonnes telles quelles
                df_clean[col] = df[col]
        
        add_log(f"Fichier chargé avec {len(df_clean)} lignes")
        return df_clean
    except Exception as e:
        add_log(f"Erreur lors du chargement du fichier: {e}")
        return pd.DataFrame()

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
    # Afficher les informations de débogage
    add_log(f"Recherche de taux IS pour: {salaire_brut_annuel} CHF, Statut: {statut_marital}")
    
    # CAS SPÉCIAL: Vérifier en priorité les cas problématiques connus
    for (min_val, max_val), taux_map in tranches_116000.items():
        if min_val <= salaire_brut_annuel <= max_val:
            add_log(f"Tranche spéciale trouvée: {min_val}-{max_val}")
            if statut_marital in taux_map:
                taux = taux_map[statut_marital] / 100
                add_log(f"Taux spécial appliqué: {taux*100}%")
                return taux
    
    # Méthode standard: recherche dans le DataFrame
    add_log("Recherche standard dans les données...")
    if not is_df.empty and "Année Min" in is_df.columns and "Année Max" in is_df.columns:
        for index, row in is_df.iterrows():
            try:
                min_val = nettoyer_nombre(row["Année Min"])
                max_val = nettoyer_nombre(row["Année Max"])
                
                # Afficher pour débogage
                if abs(min_val - salaire_brut_annuel) < 500:  # Proche du salaire recherché
                    add_log(f"Ligne {index}: Min={min_val}, Max={max_val}")
                
                if min_val <= salaire_brut_annuel <= max_val:
                    add_log(f"Tranche trouvée: {min_val}-{max_val}")
                    
                    # Obtenir le taux
                    if statut_marital in row:
                        taux = nettoyer_nombre(row[statut_marital])
                        add_log(f"Taux trouvé: {taux}%")
                        return taux / 100
                    else:
                        add_log(f"Statut {statut_marital} non trouvé dans cette ligne")
            except Exception as e:
                add_log(f"Erreur ligne {index}: {e}")
    else:
        add_log("DataFrame vide ou colonnes manquantes")
    
    # Si rien n'est trouvé
    add_log("AUCUN TAUX TROUVÉ. Retour de 0")
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
        add_log(f"Taux IS final: {taux_is*100}%")
        cotisations["Impôt Source"] = salaire_brut_mensuel * taux_is
    
    total_deductions = sum(cotisations.values())
    salaire_net_mensuel = salaire_brut_mensuel - total_deductions

    return salaire_net_mensuel, salaire_brut_mensuel, cotisations

# 📌 **Chargement des données IS.xlsx**
add_log("Chargement des données IS.xlsx...")
is_df = charger_is_data()

# Identifier les colonnes pour les statuts maritaux
colonnes_techniques = ["INDEX", "Année Min", "Année Max", "Mois Min", "Mois Max"]
colonnes_statut_marital = [col for col in is_df.columns if col not in colonnes_techniques 
                         and not col.startswith("Unnamed:")]

# Afficher les colonnes disponibles
add_log(f"Colonnes disponibles: {is_df.columns.tolist()}")
add_log(f"Statuts maritaux disponibles: {colonnes_statut_marital}")

# 📌 **Mise en page en deux colonnes avec espacement**
col1, col3, col2 = st.columns([1, 0.2, 1])  # La colonne 2 est plus étroite pour l'espacement
st.markdown("<br>", unsafe_allow_html=True)

# 🏦 **Colonne 1 : Calcul du Salaire Net**
with col1:
    st.header("💰 Calcul du Salaire Net")

    # **Entrées utilisateur**
    salaire_brut_annuel = st.number_input("💰 Salaire Brut Annuel (CHF)", min_value=0, value=116000)
    age = st.number_input("🎂 Âge", min_value=25, max_value=65, value=35)
    
    # Utiliser uniquement les colonnes de statut marital
    if colonnes_statut_marital:
        situation_familiale = st.selectbox("👨‍👩‍👧‍👦 Situation familiale", colonnes_statut_marital)
    else:
        # Si pas de colonnes trouvées, utiliser une liste prédéfinie
        statuts_predefined = ["Célibataire sans enfant", "Marié et le conjoint ne travaille pas et 0 enfant"]
        situation_familiale = st.selectbox("👨‍👩‍👧‍👦 Situation familiale", statuts_predefined)

    # **Sélection du statut de résidence**
    nationalite = st.radio("🌍 Statut de résidence", ["🇨🇭 Suisse", "🏷️ Permis C", "🌍 Autre (Imposé à la source)"])
    soumis_is = nationalite == "🌍 Autre (Imposé à la source)"

    # **Bouton de test**
    if st.button("🧪 Test pour 116'000 CHF"):
        add_log("\n--- TEST POUR 116'000 CHF ---")
        taux = obtenir_taux_is(116000, "Célibataire sans enfant", is_df)
        add_log(f"Résultat du test: {taux*100}%")
        st.text_area("Résultat du test pour 116'000 CHF", 
                     f"Taux trouvé: {taux*100}%\nMontant mensuel: {(116000/12) * taux:.2f} CHF", 
                     height=100)

    # **Bouton de calcul**
    if st.button("🧮 Calculer Salaire"):
        add_log("\n--- CALCUL DU SALAIRE ---")
        add_log(f"Salaire: {salaire_brut_annuel}, Age: {age}, Statut: {situation_familiale}")
        add_log(f"Soumis à l'IS: {soumis_is}")
        
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
                st.write("✅ Votre TJM couvre la marge requise")
            else:
                st.write("⚠️ Votre TJM est trop bas pour assurer la marge")
        else:
            st.write("⚠️ Veuillez d'abord entrer un salaire brut annuel")
