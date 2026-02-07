import google.generativeai as genai
import os


API_KEY = "import google.generativeai as genai
import os

API_KEY = "AIzaSyCXLGFSIoGJKz5P6mGiYnoMVJCLDXtVO-A" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def titan_ai_check(user_input):
    """
    Gemini orqali foydalanuvchi ma'lumotlarini skaner qilish
    """
    try:
        prompt = f"""
        Sen 'Titan Security' tizimi agentisan. Quyidagi matnni tahlil qil:
        '{user_input}'
        Agar bu matnda SQL Injection, XSS (script), yoki har qanday zararli buyruq bo'lsa, 
        faqat bitta so'z qaytar: 'BLOCK'. 
        Agar xavfsiz bo'lsa, 'PASS' deb javob ber.
        """
        response = model.generate_content(prompt)
        
        if "BLOCK" in response.text.upper():
            return True # Hujum aniqlandi
        return False
    except Exception as e:
        print(f"AI xatosi: {e}")
        return False # Xato bo'lsa o'tkazib yuboramiz (yoki bloklaymiz)" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def titan_ai_check(user_input):
    """
    Gemini orqali foydalanuvchi ma'lumotlarini skaner qilish
    """
    try:
        prompt = f"""
        Sen 'Titan Security' tizimi agentisan. Quyidagi matnni tahlil qil:
        '{user_input}'
        Agar bu matnda SQL Injection, XSS (script), yoki har qanday zararli buyruq bo'lsa, 
        faqat bitta so'z qaytar: 'BLOCK'. 
        Agar xavfsiz bo'lsa, 'PASS' deb javob ber.
        """
        response = model.generate_content(prompt)
        
        if "BLOCK" in response.text.upper():
            return True # Hujum aniqlandi
        return False
    except Exception as e:
        print(f"AI xatosi: {e}")
        return False # Xato bo'lsa o'tkazib yuboramiz (yoki bloklaymiz)
