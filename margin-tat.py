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
    try:
        # Lire le fichier Excel
        response = requests.get(GITHUB_URL_IS)
        df = pd.read_excel(BytesIO(response.content))
        
        # Afficher les info de débogage
        st.write(f"Colonnes dans IS.xlsx: {df.columns.tolist()}")
        
        # Nettoyage des colonnes numériques
        for col in df.columns:
            if col != "INDEX":  # Exclure les colonnes non numériques
                # Convertir en string d'abord pour éviter les erreurs
                df[col] = df[col].astype(str)
                # Nettoyer les valeurs
                df[col] = df[col].str.replace("'", "").str.replace(" ", "")
                df[col] = df[col].str.replace(",", ".")  # Remplacer les virgules par des points
                
                # Convertir en numérique quand possible
                if col in ["Année Min", "Année Max", "Mois Min", "Mois Max"]:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except Exception as e:
                        st.warning(f"Erreur de conversion pour {col}: {e}")
        
        # Afficher quelques lignes pour vérification
        st.write("Exemple de données après nettoyage:")
        st.write(df.head(2))
        
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier IS.xlsx: {e}")
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

# 📌 **Fonction pour obtenir le taux IS - Version améliorée**
def obtenir_taux_is(salaire_brut_annuel, statut_marital, is_df):
    # Convertir le salaire en nombre flottant
    salaire_brut_annuel = float(salaire_brut_annuel)
    
    # Afficher les informations de débogage
    st.write(f"Recherche pour salaire: {salaire_brut_annuel} CHF, Statut: {statut_marital}")
    
    # Vérifier si le DataFrame est valide
    if is_df.empty:
        st.error("Données IS.xlsx vides ou invalides")
        return 0.0
    
    # Vérifier si le statut marital est dans les colonnes
    if statut_marital not in is_df.columns:
        st.error(f"Statut marital '{statut_marital}' non trouvé dans les colonnes: {is_df.columns.tolist()}")
        return 0.0
    
    # Parcourir manuellement chaque ligne pour trouver la tranche appropriée
    for index, row in is_df.iterrows():
        try:
            # Convertir les valeurs de tranche en nombres flottants
            min_val = float(str(row["Année Min"]).replace("'", "").replace(" ", ""))
            max_val = float(str(row["Année Max"]).replace("'", "").replace(" ", ""))
            
            # Vérifier si le salaire est dans cette tranche
            if min_val <= salaire_brut_annuel <= max_val:
                st.success(f"✅ Tranche trouvée: {min_val} - {max_val}")
                
                # Obtenir et convertir le taux
                taux = row[statut_marital]
                taux_str = str(taux).replace(',', '.').strip()
                
                # Vérifier si le taux est valide
                if taux_str == "" or taux_str == "_____" or taux_str == "0":
                    return 0.0
                
                # Convertir en nombre et diviser par 100
                try:
                    taux_final = float(taux_str) / 100
                    st.write(f"Taux appliqué: {taux_str}% ({taux_final:.4f})")
                    return taux_final
                except (ValueError, TypeError) as e:
                    st.error(f"Erreur de conversion du taux '{taux_str}': {e}")
                    return 0.0
        except Exception as e:
            st.warning(f"Erreur lors du traitement de la ligne {index}: {e}")
            continue
    
    # Si aucune tranche n'est trouvée
    st.warning(f"❌ Aucune tranche trouvée pour le salaire {salaire_brut_annuel} CHF")
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
        st.write(f"Taux IS appliqué: {taux_is:.4f} ({taux_is*100:.2f}%)")
    
    total_deductions = sum(cotisations.values())
    salaire_net_mensuel = salaire_brut_mensuel - total_deductions

    return salaire_net_mensuel, salaire_brut_mensuel, cotisations

# 📌 **Chargement des données IS.xlsx**
is_df = charger_is_data()

# Identifier les colonnes pour les statuts maritaux (exclure les colonnes techniques)
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
    salaire_brut_annuel = st.number_input("💰 Salaire Brut Annuel (CHF)", min_value=0, value=116000)
    age = st.number_input("🎂 Âge", min_value=25, max_value=65, value=35)
    
    # Utiliser uniquement les colonnes de statut marital si elles sont disponibles
    if colonnes_statut_marital:
        situation_familiale = st.selectbox("👨‍👩‍👧‍👦 Situation familiale", colonnes_statut_marital)
    else:
        st.error("Aucune colonne de statut marital trouvée dans le fichier IS.xlsx")
        situation_familiale = "Célibataire sans enfant"  # Valeur par défaut

    # **Sélection du statut de résidence**
    nationalite = st.radio("🌍 Statut de résidence", ["🇨🇭 Suisse", "🏷️ Permis C", "🌍 Autre (Imposé à la source)"])
    soumis_is = nationalite == "🌍 Autre (Imposé à la source)"

    # Tester les valeurs problématiques
    if st.checkbox("🧪 Mode test (afficher les résultats pour différents salaires)"):
        salaires_test = [115000, 116000, 120000, 125000, 130000, 135000, 140000]
        for sal in salaires_test:
            st.write(f"### Test pour {sal} CHF:")
            for index, row in is_df.iterrows():
                try:
                    min_val = float(str(row["Année Min"]).replace("'", "").replace(" ", ""))
                    max_val = float(str(row["Année Max"]).replace("'", "").replace(" ", ""))
                    if min_val <= sal <= max_val:
                        st.write(f"Tranche: {min_val} - {max_val}, Taux: {row[situation_familiale]}")
                except Exception as e:
                    pass

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
