from google import genai

client = genai.Client(api_key="AQ.Ab8RN6L3Jfuj1lk63B1oSeKMt9JHxnK_hIjNXfTPB6QXSMV7RA")

for model in client.models.list():
    print(model.name)