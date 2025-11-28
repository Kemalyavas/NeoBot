import os
import time
import json
from openai import OpenAI
from dotenv import load_dotenv
from .tools import tools_schema, available_functions

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

ASSISTANT_ID = os.getenv("ASSISTANT_ID")  # Load from env or create new

def get_or_create_assistant():
    """
    Retrieves the assistant ID from env.
    """
    global ASSISTANT_ID
    
    if ASSISTANT_ID:
        print(f"Using existing Assistant ID: {ASSISTANT_ID}")
        return client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)
    
    # Create new assistant ONLY if ID is missing
    print("Assistant ID not found in .env, creating a new one...")
    assistant = client.beta.assistants.create(
        name="NeoBI",
        instructions="Sen NeoBI'sın. NeoOne şirketi için saha satış ve iskonto yönetim asistanısın. "
                     "Kullanıcılara ürün performansı hakkında bilgi ver, az satan ürünleri bul ve onlar için iskonto öner. "
                     "İskonto tanımlamak istediklerinde ilgili fonksiyonları kullan. "
                     "Her zaman profesyonel, yardımsever ve çözüm odaklı ol. Türkçe konuş. "
                     "ÖNEMLİ: İskonto tanımlama, güncelleme veya silme gibi veritabanını değiştiren kritik işlemlerden önce "
                     "MUTLAKA kullanıcıdan açıkça onay iste. Kullanıcı 'evet' veya 'onaylıyorum' demeden fonksiyonları çağırma. "
                     "İskonto süresi (duration_days) belirtilmemişse kullanıcıya sor. "
                     "GRAFİK GÖSTERİMİ: Eğer kullanıcı bir verinin grafiğini veya dağılımını isterse (örneğin 'satış dağılımını göster'), "
                     "önce ilgili veriyi al (get_product_sales_distribution gibi). "
                     "ÖNEMLI: Veriyi liste halinde YAZMA. Sadece çok kısa bir giriş cümlesi yaz (örn: 'İşte X ürününün satış dağılımı:') ve "
                     "hemen ardından JSON bloğunu ekle. JSON bloğu grafiği otomatik oluşturacak, kullanıcı zaten grafikte tüm detayları görecek. "
                     "JSON formatı: "
                     "```json\n"
                     "{\n"
                     "  \"type\": \"chart\",\n"
                     "  \"title\": \"Grafik Başlığı\",\n"
                     "  \"data\": [\n"
                     "    {\"name\": \"Etiket1\", \"value\": 10},\n"
                     "    {\"name\": \"Etiket2\", \"value\": 20}\n"
                     "  ]\n"
                     "}\n"
                     "```\n"
                     "Örnek cevap: 'İşte Organik Yulaf Ezmesi'nin satış dağılımı:' (sonra JSON bloğu)",
        tools=tools_schema,
        model="gpt-4o",
    )
    ASSISTANT_ID = assistant.id
    print(f"New Assistant Created: {ASSISTANT_ID}")
    return assistant

def create_thread():
    return client.beta.threads.create()

def add_message_to_thread(thread_id, content):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content
    )

def run_assistant(thread_id):
    """
    Runs the assistant on the thread, handles tool calls, and returns the final response.
    """
    assistant = get_or_create_assistant()
    
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant.id
    )

    # Polling loop
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        print(f"Run status: {run_status.status}")

        if run_status.status == 'completed':
            break
        elif run_status.status == 'requires_action':
            # Handle Function Calling
            tool_outputs = []
            try:
                for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"DEBUG: Calling function {function_name} with args: {function_args}")

                    if function_name in available_functions:
                        function_to_call = available_functions[function_name]
                        output = function_to_call(**function_args)
                        print(f"DEBUG: Function output: {output}")
                        
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": output
                        })
                    else:
                        print(f"ERROR: Function {function_name} not found in available_functions.")
            except Exception as e:
                print(f"ERROR processing tool calls: {e}")
            
            # Submit outputs back to the run
            if tool_outputs:
                try:
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    print("DEBUG: Tool outputs submitted successfully.")
                except Exception as e:
                    print(f"ERROR submitting tool outputs: {e}")

        elif run_status.status in ['failed', 'cancelled', 'expired']:
            print(f"Run failed with status: {run_status.status}")
            if run_status.last_error:
                print(f"Error details: {run_status.last_error}")
            return "Bir hata oluştu veya işlem zaman aşımına uğradı."
        
        time.sleep(1) # Wait before polling again

    # Get the latest message from the assistant
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )
    
    # Return the last message content
    for msg in messages.data:
        if msg.role == "assistant":
            return msg.content[0].text.value
            
    return "Yanıt alınamadı."
