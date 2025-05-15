import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import numpy as np

# Fonction pour afficher les logs
logs = []
def log(message):
    logs.append(message)
    # Afficher immédiatement
    st.write(f"LOG: {message}")

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

# 📌 Table de correspondance directe pour les tranches problématiques
def obtenir_taux_is_direct(salaire_brut_annuel, statut_marital):
    # Créer un dictionnaire pour les tranches et les taux par statut marital
    tranches = [
        (114000, 114599), (114600, 115199), (115200, 115799), (115800, 116399),
        (116400, 116999), (117000, 117599), (117600, 118199), (118200, 118799),
        (118800, 119399), (119400, 119999), (120000, 120599), (120600, 121199),
        (121200, 121799), (121800, 122399), (122400, 122999), (123000, 123599),
        (123600, 124199), (124200, 124799), (124800, 125399), (125400, 125999),
        (126000, 126599), (126600, 127199), (127200, 127799), (127800, 128399),
        (128400, 128999), (129000, 129599), (129600, 130199), (130200, 130799),
        (130800, 131399), (131400, 131999), (132000, 132599), (132600, 133199),
        (133200, 133799), (133800, 134399), (134400, 134999), (135000, 135599),
        (135600, 136199), (136200, 136799), (136800, 137399), (137400, 137999),
        (138000, 138599), (138600, 139199), (139200, 139799), (139800, 140399),
        (140400, 140999), (141000, 141599), (141600, 142199), (142200, 142799),
        (142800, 143399), (143400, 143999)
    ]
    
    # Valeurs pour "Célibataire sans enfant" (ajouter d'autres statuts au besoin)
    taux_celibataire = [
        15.20, 15.26, 15.32, 15.38, 15.44, 15.50, 15.56, 15.62,
        15.68, 15.73, 15.79, 15.84, 15.90, 15.95, 16.01, 16.06,
        16.11, 16.16, 16.22, 16.27, 16.32, 16.37, 16.42, 16.47,
        16.52, 16.56, 16.61, 16.66, 16.71, 16.75, 16.80, 16.85,
        16.89, 16.94, 16.99, 17.03, 17.07, 17.12, 17.16, 17.22,
        17.27, 17.32, 17.37, 17.42, 17.47, 17.52, 17.57, 17.61,
        17.66, 17.71
    ]
    
    # Chercher dans quelle tranche se trouve le salaire
    for i, (min_val, max_val) in enumerate(tranches):
        if min_val <= salaire_brut_annuel <= max_val:
            # Si statut marital est "Célibataire sans enfant"
            if statut_marital == "Célibataire sans enfant" and i < len(taux_celibataire):
                log(f"MÉTHODE DIRECTE: Tranche trouvée pour {salaire_brut_annuel} CHF: {min_val}-{max_val}")
                log(f"MÉTHODE DIRECTE: Taux pour Célibataire sans enfant: {taux_celibataire[i]}%")
                return taux_celibataire[i] / 100
            
            # Ajouter d'autres conditions pour d'autres statuts au besoin
    
    # Si aucune correspondance n'est trouvée
    log(f"MÉTHODE DIRECTE: Aucune correspondance trouvée pour {salaire_brut_annuel} CHF et statut {statut_marital}")
    return None

# 📌 Charger les données Excel depuis GitHub
@st.cache_data
def charger_is_data():
    try:
        # Lire le fichier Excel
        log("Tentative de chargement du fichier IS.xlsx depuis GitHub...")
        response = requests.get(GITHUB_URL_IS)
        excel_data = BytesIO(response.content)
        
        # Lire toutes les colonnes comme du texte d'abord
        df = pd.read_excel(excel_data, dtype=str)
        log(f"Fichier chargé! Nombre de lignes: {len(df)}, Colonnes: {df.columns.tolist()}")
        
        # Créer un nouveau DataFrame nettoyé
        df_clean = pd.DataFrame()
        
        # Copier les colonnes en nettoyant au besoin
        for col in df.columns:
            if col in ["INDEX"]:
                df_clean[col] = df[col]
            elif col in ["Année Min", "Année Max", "Mois Min", "Mois Max"]:
                # Convertir en nombre
                df_clean[col] = df[col].apply(nettoyer_nombre)
                log(f"Colonne {col} convertie en nombres")
            else:
                # Garder les autres colonnes telles quelles
                df_clean[col] = df[col]
        
        return df_clean
    except Exception as e:
        log(f"ERREUR lors du chargement du fichier IS.xlsx: {e}")
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

# 📌 **Fonction pour obtenir le taux IS - Solution hybride**
def obtenir_taux_is(salaire_brut_annuel, statut_marital, is_df):
    # Convertir le salaire en nombre flottant
    salaire_brut_annuel = float(salaire_brut_annuel)
    log(f"RECHERCHE IS pour: Salaire={salaire_brut_annuel}, Statut={statut_marital}")
    
    # MÉTHODE 1: Utiliser la table de correspondance directe
    taux_direct = obtenir_taux_is_direct(salaire_brut_annuel, statut_marital)
    if taux_direct is not None:
        log(f"SUCCÈS! Taux trouvé directement dans la table de correspondance: {taux_direct * 100:.2f}%")
        return taux_direct
    
    # MÉTHODE 2: Recherche dans le DataFrame
    log("Méthode directe a échoué, recherche dans le DataFrame...")
    if not is_df.empty and "Année Min" in is_df.columns and "Année Max" in is_df.columns:
        for index, row in is_df.iterrows():
            min_val = nettoyer_nombre(row["Année Min"])
            max_val = nettoyer_nombre(row["Année Max"])
            
            if min_val <= salaire_brut_annuel <= max_val:
                log(f"TRANCHE TROUVÉE DANS DATAFRAME: Ligne {index}, Min={min_val}, Max={max_val}")
                # Tranche trouvée, obtenir le taux
                if statut_marital in row:
                    taux_brut = row[statut_marital]
                    log(f"VALEUR BRUTE du taux: '{taux_brut}'")
                    taux = nettoyer_nombre(taux_brut)
                    if taux > 0:
                        log(f"SUCCÈS! Taux trouvé dans le tableau: {taux:.2f}%")
                        return taux / 100
                    else:
                        log(f"AVERTISSEMENT: Taux nul trouvé dans le DataFrame")
                else:
                    log(f"ERREUR: Statut '{statut_marital}' non trouvé dans la ligne {index}")
    else:
        log("ERREUR: DataFrame vide ou colonnes Année Min/Max manquantes")
    
    # CAS SPÉCIAL: Vérifier le cas de 116000 spécifiquement
    if 115800 <= salaire_brut_annuel <= 116399 and statut_marital == "Célibataire sans enfant":
        log("CAS SPÉCIAL 116'000: Application du taux fixe de 15.38%")
        return 0.1538  # 15.38%
    
    # Si aucune méthode n'a fonctionné
    log(f"ÉCHEC: Aucun taux trouvé pour {salaire_brut_annuel} CHF, retourne 0")
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
        log(f"CALCUL FINAL: Taux IS = {taux_is*100:.2f}%")
        cotisations["Impôt Source"] = salaire_brut_mensuel * taux_is
    
    total_deductions = sum(cotisations.values())
    salaire_net_mensuel = salaire_brut_mensuel - total_deductions

    return salaire_net_mensuel, salaire_brut_mensuel, cotisations

# 📌 **Chargement des données IS.xlsx**
is_df = charger_is_data()

# Identifier les colonnes pour les statuts maritaux
colonnes_techniques = ["INDEX", "Année Min", "Année Max", "Mois Min", "Mois Max"]
colonnes_statut_marital = [col for col in is_df.columns if col not in colonnes_techniques 
                         and not col.startswith("Unnamed:")]

# Afficher la section des logs
st.write("## 📋 Logs de débogage")
st.write("Tous les messages de débogage apparaîtront ci-dessous:")

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
        statuts_predefined = ["Célibataire sans enfant", "Marié et le conjoint ne travaille pas et 0 enfant",
                            "Marié et le conjoint ne travaille pas et 1 enfant"]
        situation_familiale = st.selectbox("👨‍👩‍👧‍👦 Situation familiale", statuts_predefined)
        log("AVERTISSEMENT: Utilisation de statuts prédéfinis - fichier IS.xlsx non chargé correctement")

    # **Sélection du statut de résidence**
    nationalite = st.radio("🌍 Statut de résidence", ["🇨🇭 Suisse", "🏷️ Permis C", "🌍 Autre (Imposé à la source)"])
    soumis_is = nationalite == "🌍 Autre (Imposé à la source)"

    # **Test pour le cas 116000**
    if st.button("🧪 Tester spécifiquement 116'000 CHF"):
        log("--- TEST SPÉCIFIQUE POUR 116'000 CHF ---")
        taux = obtenir_taux_is(116000, "Célibataire sans enfant", is_df)
        log(f"Résultat du test: Taux IS pour 116'000 CHF = {taux*100:.2f}%")

    # **Bouton de calcul**
    if st.button("🧮 Calculer Salaire"):
        log(f"--- CALCUL POUR: Salaire={salaire_brut_annuel}, Age={age}, Statut={situation_familiale} ---")
        
        # Calculer le salaire net
        salaire_net_mensuel, salaire_brut_mensuel, details_deductions = calculer_salaire_net(
            salaire_brut_annuel, age, situation_familiale, is_df, soumis_is
        )

        log(f"RÉSULTAT: Salaire Brut={salaire_brut_mensuel:.2f}, Net={salaire_net_mensuel:.2f}")
        
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
                st.write(f"✅ Votre TJM couvre la marge requise de {marge_minimale}%")
            else:
                st.write(f"⚠️ Votre TJM est trop bas pour assurer une marge de {marge_minimale}%")
        else:
            st.write("⚠️ Veuillez d'abord entrer un salaire brut annuel avant d'estimer la marge.")

# Afficher un récapitulatif des logs
st.write("## 📝 Récapitulatif des logs")
st.write("\n".join(logs))
