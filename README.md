# Scraper do Google Maps

Este é um scraper simples que usa o Playwright para extrair dados do Google Maps.

Este exemplo foi criado para fins educacionais.

Este scraper é fácil de personalizar.

Confira os arquivos Excel e CSV (google_maps_data) para ver como os dados finais serão apresentados.

## Para Instalar:
- (Opcional: crie e ative um ambiente virtual) `virtualenv venv`, depois `source venv/bin/activate`

- `pip install -r requirements.txt`
- `playwright install chromium`

## Para Executar:
### Uma única pesquisa:
- `python3 main.py -s=<o que e onde pesquisar> -t=<quantos resultados>`

### Várias pesquisas de uma vez:
1. Adicione as pesquisas no arquivo `input.txt`, cada pesquisa deve estar em uma nova linha, como mostrado no exemplo (veja `input.txt`)
2. Em seguida, execute: `python3 main.py`
3. Se você adicionar `-t=<quantos resultados>`, isso será aplicado a todas as pesquisas.

## Dicas:
Se você quiser buscar mais do que os 120 resultados limitados, detalhe sua pesquisa mais e de forma mais específica no `input.txt`, por exemplo:

- Em vez de usar:

`dentista Estados Unidos`

- Use:

`dentista Boston Estados Unidos`

`dentista Nova York Estados Unidos`

`dentista Texas Estados Unidos`

E assim por diante...