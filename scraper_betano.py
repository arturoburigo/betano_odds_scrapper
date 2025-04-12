from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    logger.info("Iniciando configuração do driver Chrome...")
    # Configurar as opções do Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Nova versão do modo headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        # Inicializar o driver
        logger.info("Tentando inicializar o driver Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        logger.info("Driver Chrome inicializado com sucesso!")
        return driver
    except Exception as e:
        logger.error(f"Erro ao inicializar o driver Chrome: {str(e)}")
        raise

def wait_for_element(driver, by, value, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except Exception as e:
        logger.error(f"Timeout esperando pelo elemento {value}: {str(e)}")
        return None

def scrape_betano():
    driver = None
    try:
        driver = setup_driver()
        url = "https://www.betano.bet.br/sport/beisebol/eua/mlb/1662/?bt=strikeouts"
        
        logger.info(f"Acessando URL: {url}")
        # Acessar a página
        driver.get(url)
        
        # Aguardar a página carregar
        logger.info("Aguardando carregamento inicial da página...")
        time.sleep(10)  # Aumentado o tempo de espera inicial
        
        # Verificar se a página carregou corretamente
        logger.info("Verificando título da página...")
        logger.info(f"Título da página: {driver.title}")
        
        # Tentar encontrar elementos específicos para confirmar que a página carregou
        logger.info("Verificando elementos da página...")
        try:
            # Salvar screenshot para debug
            driver.save_screenshot("pagina.png")
            logger.info("Screenshot salvo como 'pagina.png'")
            
            # Tentar encontrar algum elemento que sabemos que existe
            page_source = driver.page_source
            logger.info(f"Tamanho do HTML da página: {len(page_source)} caracteres")
            
            if "BASE" in page_source:
                logger.info("Texto 'BASE' encontrado no HTML")
            else:
                logger.warning("Texto 'BASE' não encontrado no HTML")
            
        except Exception as e:
            logger.error(f"Erro ao verificar elementos da página: {str(e)}")
        
        # Encontrar todas as divs com category="BASE"
        logger.info("Procurando elementos com category='BASE'...")
        base_divs = driver.find_elements(By.CSS_SELECTOR, 'div[category="BASE"]')
        logger.info(f"Encontradas {len(base_divs)} divs com category='BASE'")
        
        if len(base_divs) == 0:
            logger.warning("Nenhuma div com category='BASE' encontrada. Tentando encontrar outros elementos...")
            # Tentar encontrar outros elementos para debug
            all_divs = driver.find_elements(By.TAG_NAME, "div")
            logger.info(f"Total de divs na página: {len(all_divs)}")
            
            # Procurar por classes específicas que sabemos que existem
            for div in all_divs[:10]:  # Limitar a 10 para não sobrecarregar o log
                try:
                    class_name = div.get_attribute("class")
                    logger.info(f"Div encontrada com classe: {class_name}")
                except:
                    continue
        
        resultados = []
        
        for index, base_div in enumerate(base_divs, 1):
            try:
                logger.info(f"Processando div {index} de {len(base_divs)}")
                
                # Encontrar o nome do jogador
                logger.info("Buscando nome do jogador...")
                jogador = base_div.find_element(By.CLASS_NAME, "row-title__text").text
                logger.info(f"Nome do jogador encontrado: {jogador}")
                
                # Encontrar o handicap
                logger.info("Buscando handicap...")
                handicap = base_div.find_element(By.CLASS_NAME, "handicap__single-item").text
                logger.info(f"Handicap encontrado: {handicap}")
                
                # Encontrar as odds (valores dos spans dentro das selections)
                logger.info("Buscando odds...")
                odds = base_div.find_elements(By.CSS_SELECTOR, ".selections__selection span")
                odds_values = [odd.text for odd in odds]
                logger.info(f"Odds encontradas: {odds_values}")
                
                resultado = {
                    "Jogador": jogador,
                    "Handicap": handicap,
                    "Odds": odds_values
                }
                
                resultados.append(resultado)
                logger.info(f"Div {index} processada com sucesso")
                
            except Exception as e:
                logger.error(f"Erro ao processar div {index}: {str(e)}")
                continue
        
        logger.info(f"Total de resultados coletados: {len(resultados)}")
        return resultados
        
    except Exception as e:
        logger.error(f"Erro durante o scraping: {str(e)}")
        return None
        
    finally:
        if driver:
            logger.info("Fechando o driver Chrome...")
            driver.quit()

if __name__ == "__main__":
    logger.info("Iniciando o script de scraping...")
    resultados = scrape_betano()
    
    if resultados:
        logger.info("\nResultados encontrados:")
        for resultado in resultados:
            print("\n-------------------")
            print(f"Jogador: {resultado['Jogador']}")
            print(f"Handicap: {resultado['Handicap']}")
            print(f"Odds: {resultado['Odds']}")
    else:
        logger.error("Não foi possível obter os resultados.") 