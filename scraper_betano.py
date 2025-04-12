from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import logging
import csv
import os
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver(headless=True):
    logger.info("Iniciando configuração do driver Chrome...")
    # Configurar as opções do Chrome
    chrome_options = Options()
    if headless:
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

def scroll_page(driver, scroll_pause_time=2, max_scrolls=30):
    """
    Rola a página para baixo para carregar todos os elementos
    """
    logger.info("Iniciando rolagem da página...")
    
    # Obter altura inicial da página
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    
    while scroll_count < max_scrolls:
        # Rolar para o final da página
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Aguardar o carregamento
        time.sleep(scroll_pause_time)
        
        # Calcular nova altura e comparar com a última altura
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # Se a altura não mudou, não há mais conteúdo para carregar
            logger.info("Página rolada até o final")
            break
            
        last_height = new_height
        scroll_count += 1
        logger.info(f"Rolagem {scroll_count} concluída")
    
    # Voltar ao topo da página
    driver.execute_script("window.scrollTo(0, 0);")
    logger.info("Retornando ao topo da página")
    
    # Aguardar um pouco para garantir que a página esteja estável
    time.sleep(3)

def save_to_csv(resultados, filename=None):
    """
    Salva os resultados em um arquivo CSV
    """
    if not resultados:
        logger.warning("Nenhum resultado para salvar")
        return
    
    if filename is None:
        # Criar nome de arquivo com data e hora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"betano_strikeouts_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Time', 'Jogador', 'Linha', 'Mais_de', 'Menos_de']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for resultado in resultados:
                writer.writerow(resultado)
            
            logger.info(f"Resultados salvos em {filename}")
    except Exception as e:
        logger.error(f"Erro ao salvar resultados em CSV: {str(e)}")

def scrape_betano(headless=True, save_csv=True):
    driver = None
    try:
        driver = setup_driver(headless)
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
        
        # Rolar a página para carregar todos os elementos
        scroll_page(driver)
        
        # Aguardar um pouco mais para garantir que todos os elementos estejam carregados
        time.sleep(5)
        
        # Encontrar todos os elementos multi-outcome
        logger.info("Procurando elementos com classe 'multi-outcome'...")
        multi_outcomes = driver.find_elements(By.CLASS_NAME, "multi-outcome")
        logger.info(f"Encontrados {len(multi_outcomes)} elementos multi-outcome")
        
        resultados = []
        
        for index, multi_outcome in enumerate(multi_outcomes, 1):
            try:
                logger.info(f"Processando multi-outcome {index} de {len(multi_outcomes)}")
                
                # Encontrar todos os times
                times = multi_outcome.find_elements(By.CLASS_NAME, "team")
                logger.info(f"Encontrados {len(times)} times neste multi-outcome")
                
                for time_index, time_element in enumerate(times):
                    try:
                        # Extrair o nome do time
                        time_name_element = time_element.find_element(By.CLASS_NAME, "team-header__title")
                        time_name = time_name_element.text if time_name_element else "N/A"
                        logger.info(f"Nome do time encontrado: {time_name}")
                        
                        # Encontrar o jogador
                        jogador_element = time_element.find_element(By.CLASS_NAME, "row-title__text")
                        jogador = jogador_element.text if jogador_element else "N/A"
                        logger.info(f"Nome do jogador encontrado: {jogador}")
                        
                        # Encontrar a linha (handicap)
                        linha_element = time_element.find_element(By.CLASS_NAME, "handicap__single-item")
                        linha = linha_element.text if linha_element else "N/A"
                        logger.info(f"Linha encontrada: {linha}")
                        
                        # Encontrar as odds (mais de e menos de)
                        odds_elements = time_element.find_elements(By.CSS_SELECTOR, ".selections__selection span")
                        mais_de = odds_elements[0].text if len(odds_elements) > 0 else "N/A"
                        menos_de = odds_elements[1].text if len(odds_elements) > 1 else "N/A"
                        logger.info(f"Odds encontradas: Mais de {mais_de}, Menos de {menos_de}")
                        
                        # Só adicionar resultados que tenham dados válidos
                        if time_name != "N/A" and jogador != "N/A" and linha != "N/A" and mais_de != "N/A" and menos_de != "N/A":
                            resultado = {
                                "Time": time_name,
                                "Jogador": jogador,
                                "Linha": linha,
                                "Mais_de": mais_de,
                                "Menos_de": menos_de
                            }
                            
                            resultados.append(resultado)
                            logger.info(f"Time {time_index+1} do multi-outcome {index} processado com sucesso")
                        else:
                            logger.warning(f"Dados incompletos para time {time_index+1} do multi-outcome {index}, ignorando")
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar time {time_index+1} do multi-outcome {index}: {str(e)}")
                        continue
                
            except Exception as e:
                logger.error(f"Erro ao processar multi-outcome {index}: {str(e)}")
                continue
        
        logger.info(f"Total de resultados coletados: {len(resultados)}")
        
        # Salvar resultados em CSV se solicitado
        if save_csv and resultados:
            save_to_csv(resultados)
            
        return resultados
        
    except Exception as e:
        logger.error(f"Erro durante o scraping: {str(e)}")
        return None
        
    finally:
        if driver:
            logger.info("Fechando o driver Chrome...")
            driver.quit()

if __name__ == "__main__":
    import argparse
    
    # Configurar argumentos de linha de comando
    parser = argparse.ArgumentParser(description='Scraper para dados de strikeouts da Betano')
    parser.add_argument('--no-headless', action='store_true', help='Executar o navegador em modo visível (não headless)')
    parser.add_argument('--no-csv', action='store_true', help='Não salvar resultados em CSV')
    args = parser.parse_args()
    
    logger.info("Iniciando o script de scraping...")
    resultados = scrape_betano(headless=not args.no_headless, save_csv=not args.no_csv)
    
    if resultados:
        logger.info("\nResultados encontrados:")
        for resultado in resultados:
            print("\n-------------------")
            print(f"Time: {resultado['Time']}")
            print(f"Jogador: {resultado['Jogador']}")
            print(f"Linha: {resultado['Linha']}")
            print(f"Mais de: {resultado['Mais_de']}")
            print(f"Menos de: {resultado['Menos_de']}")
    else:
        logger.error("Não foi possível obter os resultados.") 