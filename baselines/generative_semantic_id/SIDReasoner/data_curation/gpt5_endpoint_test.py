from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI


ENDPOINTS = [
    "feedscopilot-azureopenai-au",
    "feedscopilot-azureopenai-ca-east",
    "feedscopilot-azureopenai-eastus",
    "feedscopilot-azureopenai-eastus2",
    "feedscopilot-azureopenai-jp",
    "feedscopilot-azureopenai-northus",
    "feedscopilot-azureopenai-southus",
    "feedscopilot-azureopenai-sweden",
    "feedscopilot-azureopenai-uksouth",
    "feedscopilot-azureopenai-westus3",
]


def get_GPT5_client(endpoint):
    if endpoint not in ENDPOINTS:
        raise ValueError(f"Unsupported endpoint: {endpoint}")

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    return AzureOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint=f"https://{endpoint}.openai.azure.com/",
        azure_ad_token_provider=token_provider,
    )
