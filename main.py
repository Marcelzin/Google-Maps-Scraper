"""Este script serve como um exemplo de como usar Python
   e Playwright para raspar/extrair dados do Google Maps"""

from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys

@dataclass
class Negocio:
    """armazena dados de um negócio"""

    nome: str = None
    endereco: str = None
    site: str = None
    telefone: str = None
    quantidade_avaliacoes: int = None
    media_avaliacoes: float = None
    latitude: float = None
    longitude: float = None


@dataclass
class ListaNegocios:
    """armazena uma lista de objetos Negocio,
    e salva em ambos formatos excel e csv
    """
    lista_negocios: list[Negocio] = field(default_factory=list)
    salvar_em = 'saida'

    def para_dataframe(self):
        """transforma lista_negocios em um dataframe pandas

        Retorna: dataframe pandas
        """
        return pd.json_normalize(
            (asdict(negocio) for negocio in self.lista_negocios), sep="_"
        )

    def salvar_em_excel(self, nome_arquivo):
        """salva o dataframe pandas em um arquivo excel (xlsx)

        Argumentos:
            nome_arquivo (str): nome do arquivo
        """
        if not os.path.exists(self.salvar_em):
            os.makedirs(self.salvar_em)
        self.para_dataframe().to_excel(f"{self.salvar_em}/{nome_arquivo}.xlsx", index=False, engine='openpyxl')

    def salvar_em_csv(self, nome_arquivo):
        """salva o dataframe pandas em um arquivo csv

        Argumentos:
            nome_arquivo (str): nome do arquivo
        """
        if not os.path.exists(self.salvar_em):
            os.makedirs(self.salvar_em)
        self.para_dataframe().to_csv(f"{self.salvar_em}/{nome_arquivo}.csv", index=False, encoding='utf-8-sig')

def extrair_coordenadas_de_url(url: str) -> tuple[float,float]:
    """função auxiliar para extrair coordenadas de uma URL"""
    
    coordenadas = url.split('/@')[-1].split('/')[0]
    # retorna latitude, longitude
    return float(coordenadas.split(',')[0]), float(coordenadas.split(',')[1])

def main():
    
    ########
    # entrada 
    ########
    
    # lê a pesquisa dos argumentos
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--pesquisa", type=str)
    parser.add_argument("-t", "--total", type=int)
    args = parser.parse_args()
    
    if args.pesquisa:
        lista_pesquisas = [args.pesquisa]
        
    if args.total:
        total = args.total
    else:
        # se nenhum total for passado, definimos o valor para um número grande aleatório
        total = 1_000_000

    if not args.pesquisa:
        lista_pesquisas = []
        # lê a pesquisa do arquivo input.txt
        nome_arquivo_entrada = 'input.txt'
        # Obtém o caminho absoluto do arquivo no diretório de trabalho atual
        caminho_arquivo_entrada = os.path.join(os.getcwd(), nome_arquivo_entrada)
        # Verifica se o arquivo existe
        if os.path.exists(caminho_arquivo_entrada):
            # Abre o arquivo no modo de leitura com codificação UTF-8
            with open(caminho_arquivo_entrada, 'r', encoding='utf-8') as arquivo:
                # Lê todas as linhas em uma lista
                lista_pesquisas = arquivo.readlines()
                
        if len(lista_pesquisas) == 0:
            print('Erro: Você deve passar o argumento de pesquisa -s ou adicionar pesquisas ao arquivo input.txt')
            sys.exit()
        
    ###########
    # raspagem
    ###########
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=False)
        pagina = navegador.new_page()

        pagina.goto("https://www.google.com/maps", timeout=60000)
        # espera adicionada para fase de desenvolvimento. pode ser removida em produção
        pagina.wait_for_timeout(5000)
        
        for indice_pesquisa, pesquisa in enumerate(lista_pesquisas):
            print(f"-----\n{indice_pesquisa} - {pesquisa}".strip())

            pagina.locator('//input[@id="searchboxinput"]').fill(pesquisa.strip())
            pagina.wait_for_timeout(3000)

            pagina.keyboard.press("Enter")
            pagina.wait_for_timeout(5000)

            # rolando a página
            pagina.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

            # essa variável é usada para detectar se o bot
            # raspou o mesmo número de listagens na iteração anterior
            anteriormente_contado = 0
            while True:
                pagina.mouse.wheel(0, 10000)
                pagina.wait_for_timeout(3000)

                if (
                    pagina.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).count()
                    >= total
                ):
                    listagens = pagina.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).all()[:total]
                    listagens = [listagem.locator("xpath=..") for listagem in listagens]
                    print(f"Total raspado: {len(listagens)}")
                    break
                else:
                    # lógica para sair do loop e não rodar infinitamente
                    # caso tenha chegado a todas as listagens disponíveis
                    if (
                        pagina.locator(
                            '//a[contains(@href, "https://www.google.com/maps/place")]'
                        ).count()
                        == anteriormente_contado
                    ):
                        listagens = pagina.locator(
                            '//a[contains(@href, "https://www.google.com/maps/place")]'
                        ).all()
                        print(f"Chegou a todas as disponíveis\nTotal raspado: {len(listagens)}")
                        break
                    else:
                        anteriormente_contado = pagina.locator(
                            '//a[contains(@href, "https://www.google.com/maps/place")]'
                        ).count()
                        print(
                            f"Raspado atualmente: ",
                            pagina.locator(
                                '//a[contains(@href, "https://www.google.com/maps/place")]'
                            ).count(),
                        )

            lista_negocios = ListaNegocios()

            # raspagem
            for listagem in listagens:
                try:
                    listagem.click()
                    pagina.wait_for_timeout(5000)

                    atributo_nome = 'aria-label'
                    xpath_endereco = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                    xpath_site = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                    xpath_telefone = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                    xpath_qtd_avaliacoes = '//button[@jsaction="pane.reviewChart.moreReviews"]//span'
                    xpath_media_avaliacoes = '//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]'
                    
                    negocio = Negocio()
                   
                    if len(listagem.get_attribute(atributo_nome)) >= 1:
                        negocio.nome = listagem.get_attribute(atributo_nome)
                    else:
                        negocio.nome = ""
                    if pagina.locator(xpath_endereco).count() > 0:
                        negocio.endereco = pagina.locator(xpath_endereco).all()[0].inner_text()
                    else:
                        negocio.endereco = ""
                    if pagina.locator(xpath_site).count() > 0:
                        negocio.site = pagina.locator(xpath_site).all()[0].inner_text()
                    else:
                        negocio.site = ""
                    if pagina.locator(xpath_telefone).count() > 0:
                        negocio.telefone = pagina.locator(xpath_telefone).all()[0].inner_text()
                    else:
                        negocio.telefone = ""
                    if pagina.locator(xpath_qtd_avaliacoes).count() > 0:
                        negocio.quantidade_avaliacoes = int(
                            pagina.locator(xpath_qtd_avaliacoes).inner_text()
                            .split()[0]
                            .replace(',','')
                            .strip()
                        )
                    else:
                        negocio.quantidade_avaliacoes = ""
                        
                    if pagina.locator(xpath_media_avaliacoes).count() > 0:
                        negocio.media_avaliacoes = float(
                            pagina.locator(xpath_media_avaliacoes).get_attribute(atributo_nome)
                            .split()[0]
                            .replace(',','.')
                            .strip())
                    else:
                        negocio.media_avaliacoes = ""
                    
                    negocio.latitude, negocio.longitude = extrair_coordenadas_de_url(pagina.url)

                    lista_negocios.lista_negocios.append(negocio)
                except Exception as e:
                    print(f'Erro: {e}')
            
            #########
            # saída
            #########
            lista_negocios.salvar_em_excel(f"google_maps_data_{pesquisa.strip()}".replace(' ', '_'))
            lista_negocios.salvar_em_csv(f"google_maps_data_{pesquisa.strip()}".replace(' ', '_'))

        navegador.close()


if __name__ == "__main__":
    main()
