import httpx
import asyncio

async def ollama_request(prompt: str, model: str = "qwen-price-parser-bigctx"):
    """Async функція для запитів до Ollama API"""
    base_url = "https://secrecy-graceful-pointing.ngrok-free.dev"
    url = f"{base_url}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
    except httpx.HTTPError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"



# if __name__ == "__main__":
#     print(ollama_request("Напиши жарт про програмістів"))