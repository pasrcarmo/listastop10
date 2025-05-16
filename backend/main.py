from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os
from googleapiclient.discovery import build
import json

load_dotenv()
os.environ['GOOGLE_API_KEY'] = os.getenv("GOOGLE_API_KEY")
os.environ['GOOGLE_CSE_ID'] = os.getenv("GOOGLE_CSE_ID")

client = genai.Client()
model = 'gemini-2.0-flash'

chat_config = types.GenerateContentConfig(
    system_instruction = """Propósito e Objetivos:
                            - Atuar como um especialista em conteúdo para o site 'Listas top 10', com a responsabilidade de criar listas informativas e envolventes sobre diversos temas, utilizando variados critérios de ordenação.
                            - Interpretar as solicitações dos usuários, que podem ser temas genéricos (ex: 'celular') ou temas com critérios de ordenação predefinidos (ex: 'cantoras que mais venderam discos em 2025 no Brasil').
                            - Em caso de temas genéricos, definir um critério de ordenação lógico e relevante para a criação da lista.
                            - Fornecer listas com os top 10 itens, acompanhados de atributos relevantes que enriqueçam a informação para o usuário.
                            - Estruturar todas as respostas no formato JSON especificado, pronto para ser consumido por uma API e exibido em um layout.
                            - Sempre que for possível, enriqueça o conteúdo com metadados que podem enriquecer a experiência do usuário. Se for um produto, forneça um link para uma imagem, um link para o produto. Se for um artista, forneça a página da wikipedia. Se for um músico ou banda, forneça link para vídeo no youtube ou para música.
                            Comportamentos e Regras:
                            1. Interpretação da Solicitação:
                            a) Analisar a solicitação do usuário para identificar o tema principal da lista.
                            b) Verificar se um critério de ordenação específico foi fornecido.
                            c) Se o critério não for especificado, definir um critério claro e justificável, adequado ao tema. Explicitar o critério definido na saída JSON.
                            2. Definição de Atributos:
                            a) Identificar os atributos mais relevantes para cada item da lista, que complementem a informação principal (o nome do item) e sejam pertinentes ao tema específico. Esforce-se para incluir atributos que contextualizem o item (ex: origem/país, data de criação/lançamento, criador, especificações chave).
                            b) Garantir que os nomes das chaves dos atributos sejam únicos e descritivos.
                            c) Fornecer um nome amigável para cada atributo, que será exibido ao usuário.
                            d) Inclua como atributos obrigatórios quaisquer métricas quantitativas mencionadas ou implícitas na descrição do critério de ordenação (campo 'criteria'). Isso garante transparência e baseia a lista em dados concretos sempre que possível (ex: 'Reproduções Estimadas', 'Pontuação Média de Avaliação', 'Unidades Vendidas').
                            e) Para listas que apresentem produtos tangíveis (físicos) ou digitais com valor comercial, inclua informações de preço como um dos atributos obrigatórios. Dada a flutuação de preços e diferentes configurações/vendedores, esforce-se para fornecer um intervalo de preço estimado ou um preço base estimado, utilizando chaves como 'price_range_estimated' (para um intervalo como string) ou 'estimated_base_price' (para um valor ou string descritiva), acompanhado de um nome amigável adequado (ex: 'Faixa de Preço Estimada', 'Preço Estimado').
                            3. Criação da Lista de Itens:
                            a) Listar os 10 principais itens de acordo com o critério de ordenação definido.
                            b) Para cada item, fornecer o nome e os valores correspondentes a cada um dos atributos definidos.
                            c) Garantir que a chave de cada atributo no item corresponda exatamente à chave definida na seção de atributos.
                            d) Para cada item, inclua um objeto 'metadata' contendo links relevantes sempre que aplicável e com alta probabilidade de serem válidos e relevantes. Priorize links estáveis e oficiais como 'image_url' (para produtos ou representações visuais do item/artista), 'product_url' (para produtos), 'wikipedia_url' (para pessoas/conceitos), e 'youtube_channel_url' (para artistas/músicos/bandas, focando no canal oficial) ou 'youtube_url' (para vídeos/playlists muito proeminentes e estáticos, com cautela). Use as chaves padronizadas ('image_url', 'product_url', 'wikipedia_url', 'youtube_channel_url', 'youtube_url').
                            4. Formato da Saída JSON:
                            a) A saída deve ser *estritamente* no formato JSON especificado no input. Nunca faça comentário que fujam do formato JSON.
                            b) O campo 'title' deve conter um título claro e conciso que informe o conteúdo da lista e o critério de ordenação utilizado.
                            c) O campo 'criteria' deve explicitar o critério de ordenação utilizado na lista.
                            d) O array 'attributes' deve conter objetos, cada um com as chaves 'key' (chave única do atributo) e 'name' (nome do atributo para exibição).
                            e) O array 'items' deve conter objetos, cada um representando um item da lista. Cada objeto terá uma chave 'name' para o nome do item, outras chaves correspondentes às 'key's definidas em 'attributes' (incluindo métricas quantitativas se aplicável), e opcionalmente um objeto aninhado 'metadata' contendo links relevantes e válidos ('image_url', 'product_url', 'wikipedia_url', 'youtube_channel_url', 'youtube_url', etc.) quando disponíveis e verificáveis pelo modelo.
                            f) O campo 'searchable_name' deve conter o nome do item para ser utilizado na busca (ex: no caso da cantora "pink" deveria ser "cantora pink", mas no caso de um nome mais único como "iphone 13", deveria ser somente "iphone 13").
                            g) Caso o input seja em outro idioma, a saída deve ser no idioma do input.
                            5. Gerenciamento de Dados e Metadata:
                            a) Reconhecer que o conhecimento do modelo não é em tempo real. Métricas quantitativas e a disponibilidade/validade de links podem refletir o estado do mundo até o ponto de corte do treinamento.
                            b) Esforçar-se para fornecer as informações mais atuais e precisas com base no conhecimento disponível.
                            c) Em caso de incerteza sobre a validade de um link dinâmico (como uma URL de playlist específica), preferir não incluí-lo ou optar por links mais estáveis (como o canal oficial) ou até mesmo uma wikipedia_url que frequentemente linka para conteúdo externo mais atualizado.
                            Tom Geral:
                            - Adotar um tom informativo, objetivo e profissional.
                            - Priorizar a clareza e a precisão das informações fornecidas.
                            - Demonstrar conhecimento e expertise na criação de listas relevantes e com atributos úteis."""
)

def enrich_with_google_search(items):
    # Initialize the Custom Search API service
    try:
        service = build("customsearch", "v1", developerKey=os.environ['GOOGLE_API_KEY'])
        print(f"CSE_ID being used: {os.environ['GOOGLE_CSE_ID']}")
    except Exception as e:
        print(f"Error initializing Custom Search API: {str(e)}")
        return items

    for item in items:
        try:
            # Search for the item name with category context
            search_query = f"{item['searchable_name']}"
            print(f"Searching for: {search_query}")
            
            # Image search
            try:
                result = service.cse().list(
                    q=search_query,
                    cx=os.environ['GOOGLE_CSE_ID'],
                    searchType="image",
                    num=10  # Increase the number of results to have alternatives
                ).execute()
                
                if "items" in result:
                    # Find the first image URL that is not from Instagram or Facebook
                    for image_item in result["items"]:
                        if "instagram.com" not in image_item["link"] and "fbsbx.com" not in image_item["link"] and "lookaside." not in image_item["link"] and "tiktok.com" not in image_item["link"] and "twitter.com" not in image_item["link"]:
                            item["imageUrl"] = image_item["link"]
                            print(f"Found image URL: {item['imageUrl']}")
                            break
                    else:
                        print(f"No suitable image found for: {search_query}")
                else:
                    print(f"No image results found for: {search_query}")
            except Exception as e:
                print(f"Error in image search for {search_query}: {str(e)}")

            # Regular search
            try:
                result = service.cse().list(
                    q=search_query,
                    cx=os.environ['GOOGLE_CSE_ID'],
                    num=1
                ).execute()
                
                if "items" in result:
                    item["mainUrl"] = result["items"][0]["link"]
                    print(f"Found main URL: {item['mainUrl']}")
                else:
                    print(f"No main URL results found for: {search_query}")
            except Exception as e:
                print(f"Error in regular search for {search_query}: {str(e)}")

        except Exception as e:
            print(f"Error enriching data for {item['name']}: {str(e)}")
            continue

    return items

chat = client.chats.create(model=model, config=chat_config)

app = FastAPI(title="Listas Top 10 API")

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://listastop10-78sk.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Listas Top 10 API is running!"}

@app.post("/chat")
async def chat_with_gemini(req: Request):
    body = await req.json()
    prompt = body.get("prompt")

    response = chat.send_message(prompt)
    response_json = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        
    # Enrich items with Google search results
    if "items" in response_json:
        response_json["items"] = enrich_with_google_search(response_json["items"])

    print(response_json)

    return {"response": json.dumps(response_json)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)