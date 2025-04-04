# wake_streamlit.py
from playwright.sync_api import sync_playwright
import os
import time
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wake_streamlit_app():
    """
    Vérifie si une application Streamlit est endormie et la réveille si nécessaire
    """
    # Récupérer l'URL depuis les variables d'environnement
    app_url = os.environ.get('STREAMLIT_APP_URL', 'https://tat-margin.streamlit.app/')
    
    logger.info(f"Vérification de l'application Streamlit: {app_url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Accéder à l'URL de l'application
            page.goto(app_url, wait_until="networkidle")
            logger.info("Page chargée")
            
            # Vérifier si l'application est endormie (présence du texte "Zzzz")
            sleep_text = page.locator("text=Zzzz").count()
            
            if sleep_text > 0:
                logger.info("Application endormie détectée")
                
                # Cliquer sur le bouton de réveil
                wake_button = page.locator("text=Yes, get this app back up!")
                if wake_button.count() > 0:
                    wake_button.click()
                    logger.info("Clic sur le bouton de réveil effectué")
                    
                    # Attendre que l'application se réveille
                    page.wait_for_load_state("networkidle")
                    time.sleep(5)  # Attendre un peu plus pour s'assurer que l'app est bien réveillée
                    
                    # Vérifier si l'application est réveillée
                    if page.locator("text=Zzzz").count() == 0:
                        logger.info("Application réveillée avec succès")
                    else:
                        logger.error("L'application n'a pas pu être réveillée")
                else:
                    logger.error("Bouton de réveil non trouvé")
            else:
                logger.info("L'application est déjà active")
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    wake_streamlit_app()
